from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import json
import os
from datetime import timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def load_config():
    """Load configuration"""
    # Get project root (FaceAttendanceSystem_Web directory)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(project_root, 'config', 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    config = load_config()
    admin_users = config.get('admin_users', [])
    
    # Check credentials
    for user in admin_users:
        if user['username'] == username and user['password'] == password:
            # Create access token
            expires = timedelta(hours=config.get('jwt_expiration_hours', 24))
            access_token = create_access_token(
                identity=username,
                expires_delta=expires
            )
            
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'username': username
            }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify():
    """Verify token endpoint"""
    current_user = get_jwt_identity()
    return jsonify({
        'valid': True,
        'username': current_user
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint"""
    # In a production app, you'd add token to blacklist
    return jsonify({'message': 'Logged out successfully'}), 200
