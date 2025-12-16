from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import json
import os
import logging
from datetime import timedelta

# Import blueprints
from backend.api.auth import auth_bp
from backend.api.attendance import attendance_bp, init_attendance_routes, start_monitoring
from backend.api.enrollment import enrollment_bp, init_enrollment_routes
from backend.api.reports import reports_bp

# Import core components
from backend.core.face_recognition_engine import FaceRecognitionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_config():
    """Load configuration from JSON file"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def create_app():
    """Application factory"""
    app = Flask(__name__, 
                static_folder='backend/static',
                template_folder='backend/templates')
    
    # Load configuration
    config = load_config()
    
    # Flask configuration
    app.config['SECRET_KEY'] = config.get('secret_key', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = config.get('secret_key', 'dev-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=config.get('jwt_expiration_hours', 24))
    
    # Initialize extensions
    CORS(app)
    jwt = JWTManager(app)
    
    # Initialize face recognition engine
    face_engine = FaceRecognitionEngine()
    face_engine.refresh_known_faces()
    
    # Initialize API routes with face engine
    init_attendance_routes(face_engine)
    init_enrollment_routes(face_engine)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(enrollment_bp)
    app.register_blueprint(reports_bp)
    
    # Web routes
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('index.html')
    
    @app.route('/login')
    def login_page():
        """Login page"""
        return render_template('login.html')
    
    @app.route('/enrollment')
    def enrollment_page():
        """Enrollment page"""
        return render_template('enrollment.html')
    
    @app.route('/attendance')
    def attendance_page():
        """Attendance monitoring page"""
        return render_template('attendance.html')
    
    @app.route('/reports')
    def reports_page():
        """Reports page"""
        return render_template('reports.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration
    config = load_config()
    
    # Auto-start monitoring if configured (use camera_choice)
    try:
        if config.get('auto_start_monitoring', False):
            camera_src = int(config.get('camera_choice', 0))
            ok, msg = start_monitoring(camera_src)
            if ok:
                logging.info(f"Auto-start monitoring: {msg} (camera {camera_src})")
            else:
                logging.warning(f"Auto-start monitoring skipped: {msg}")
    except Exception as e:
        logging.error(f"Failed to auto-start monitoring: {e}")
    
    # Run application
    app.run(
        host='0.0.0.0',  # Accessible from network
        port=5000,
        debug=True,
        threaded=True
    )
