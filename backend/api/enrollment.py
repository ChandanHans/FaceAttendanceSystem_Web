from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.database import Database
from backend.core.face_recognition_engine import FaceRecognitionEngine
from backend.core.face_capture import SmartFaceCapture
import cv2
import os
import shutil
import base64
import numpy as np
import logging
import threading
import queue as q

enrollment_bp = Blueprint('enrollment', __name__, url_prefix='/api/enrollment')

# Global storage for ongoing enrollment sessions
enrollment_sessions = {}
face_engine = None

def init_enrollment_routes(recognition_engine: FaceRecognitionEngine):
    """Initialize routes with face recognition engine"""
    global face_engine
    face_engine = recognition_engine

@enrollment_bp.route('/start', methods=['POST'])
@jwt_required()
def start_enrollment():
    """Start a new enrollment session"""
    data = request.get_json()
    
    person_id = data.get('id', '').strip().upper()
    name = data.get('name', '').strip()
    role = data.get('role', 'student')  # 'student' or 'staff'
    course = data.get('course', '')
    sem = data.get('sem', '')
    dep = data.get('dep', '')
    
    # Validation
    if not person_id or not name:
        return jsonify({'error': 'ID and name are required'}), 400
    
    if role == 'student' and (not course or not sem):
        return jsonify({'error': 'Course and semester required for students'}), 400
    
    if role == 'staff' and not dep:
        return jsonify({'error': 'Department required for staff'}), 400
    
    # Create enrollment session
    session_id = f"{person_id}_{threading.get_ident()}"
    
    import json
    # Get project root (FaceAttendanceSystem_Web directory)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(project_root, 'config', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    face_capture_count = config.get('face_capture_count', 5)
    angle_threshold = config.get('face_angle_threshold', 15.0)
    
    enrollment_sessions[session_id] = {
        'person_id': person_id,
        'name': name,
        'role': role,
        'course': course,
        'sem': sem,
        'dep': dep,
        'face_capturer': SmartFaceCapture(
            target_count=face_capture_count,
            angle_threshold=angle_threshold
        )
    }
    
    return jsonify({
        'message': 'Enrollment session started',
        'session_id': session_id,
        'target_count': face_capture_count
    }), 200

@enrollment_bp.route('/capture', methods=['POST'])
@jwt_required()
def capture_frame():
    """Capture a frame for enrollment - SERVER-SIDE ONLY"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    if session_id not in enrollment_sessions:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session = enrollment_sessions[session_id]
    face_capturer = session['face_capturer']
    
    # SERVER-SIDE PROCESSING ONLY
    frame_data = data.get('frame')
    if not frame_data:
        return jsonify({'error': 'Frame data required'}), 400
    
    # Decode frame
    try:
        img_data = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        return jsonify({'error': f'Invalid frame data: {str(e)}'}), 400
    
    # Process frame
    should_capture, face_img, status_message = face_capturer.process_frame(frame)
    
    captured_count = len(face_capturer.captured_images)
    target_count = face_capturer.target_count
    
    return jsonify({
        'captured': should_capture,
        'count': captured_count,
        'target': target_count,
        'message': status_message,
        'complete': captured_count >= target_count
    }), 200

@enrollment_bp.route('/complete', methods=['POST'])
@jwt_required()
def complete_enrollment():
    """Complete enrollment and save face data"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    if session_id not in enrollment_sessions:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session = enrollment_sessions[session_id]
    face_capturer = session['face_capturer']
    person_id = session['person_id']
    name = session['name']
    role = session['role']
    
    try:
        # SERVER-SIDE PROCESSING ONLY
        if len(face_capturer.captured_images) < face_capturer.target_count:
            return jsonify({'error': 'Not enough images captured'}), 400
        
        # Save images to disk
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        images_dir = os.path.join(
            project_root,
            'Student_Face' if role == 'student' else 'Staff_Face'
        )
        person_dir = face_capturer.save_images(images_dir, person_id)
        
        # Generate face encodings
        encodings = face_engine.generate_encodings_from_images(person_dir)
        
        if not encodings:
            if os.path.exists(person_dir):
                shutil.rmtree(person_dir)
            return jsonify({'error': 'Failed to generate face encodings'}), 500
        
        # Save encodings to file
        face_engine.save_encodings_to_file(person_id, encodings, name, role)
        
        # Save to database (both modes need this)
        db = Database()
        
        if role == 'student':
            success = db.execute_query(
                """INSERT INTO student_face (ID, Name, Course, Sem)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    Name = VALUES(Name), Course = VALUES(Course), Sem = VALUES(Sem);""",
                (person_id, name, session['course'], session['sem']),
            )
        else:
            success = db.execute_query(
                """INSERT INTO staff_face (ID, Name, Dep)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    Name = VALUES(Name), Dep = VALUES(Dep);""",
                (person_id, name, session['dep']),
            )
        
        if not success:
            # Only delete person_dir if it exists (server-side mode)
            if hasattr(face_capturer, 'captured_images'):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            images_dir = os.path.join(
                project_root,
                'Student_Face' if role == 'student' else 'Staff_Face'
            )
            person_dir = os.path.join(images_dir, person_id)
            if os.path.exists(person_dir):
                shutil.rmtree(person_dir)
            return jsonify({'error': 'Failed to save to database'}), 500
        
        # RefrDelete person_dir
    
        # Clean up session
        del enrollment_sessions[session_id]
        
        return jsonify({
            'message': 'Enrollment completed successfully',
            'person_id': person_id,
            'name': name,
            'encodings_count': len(encodings)
        }), 200
        
    except Exception as e:
        logging.error(f"Enrollment error: {e}")
        return jsonify({'error': f'Enrollment failed: {str(e)}'}), 500

@enrollment_bp.route('/capture_server', methods=['POST'])
@jwt_required()
def capture_server():
    """Capture frame using server-side camera"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    if session_id not in enrollment_sessions:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session = enrollment_sessions[session_id]
    face_capturer = session['face_capturer']
    
    try:
        # Get camera configuration
        import json
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(project_root, 'config', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        camera_src = config.get('camera_choice', 0)
        # Convert to int if it's a numeric string
        if isinstance(camera_src, str) and camera_src.isdigit():
            camera_src = int(camera_src)
        
        # Open camera
        cap = cv2.VideoCapture(camera_src)
        if not cap.isOpened():
            return jsonify({'error': 'Failed to open server camera'}), 500
        
        # Capture frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            return jsonify({'error': 'Failed to capture frame'}), 500
        
        # Process frame using server-side face recognition
        should_capture, face_img, status_message = face_capturer.process_frame(frame)
        
        captured_count = len(face_capturer.captured_images)
        target_count = face_capturer.target_count
        
        # Log the response data
        logging.info(f"Server capture response: captured={should_capture}, count={captured_count}/{target_count}, msg='{status_message}'")
        
        response_data = {
            'captured': should_capture,
            'captured_count': captured_count,
            'total_required': target_count,
            'message': status_message,
            'complete': captured_count >= target_count
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Server capture error: {e}")
        return jsonify({'error': f'Server capture failed: {str(e)}'}), 500

@enrollment_bp.route('/camera_config')
def get_camera_config():
    """Get camera configuration for client-side preview"""
    import json
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(project_root, 'config', 'config.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return jsonify({
            'camera_choice': config.get('camera_choice', 0)
        }), 200
    except Exception as e:
        logging.error(f"Error reading camera config: {e}")
        return jsonify({'error': 'Could not read camera config'}), 500

@enrollment_bp.route('/preview_stream')
def preview_stream():
    """Stream video preview during enrollment"""
    from flask import Response
    
    def generate_preview():
        """Generate frames for preview"""
        import json
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(project_root, 'config', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        camera_src = config.get('camera_choice', 0)
        if isinstance(camera_src, str) and camera_src.isdigit():
            camera_src = int(camera_src)
        
        cap = cv2.VideoCapture(camera_src)
        if not cap.isOpened():
            logging.error(f"Failed to open camera for preview: {camera_src}")
            return
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if not ret:
                    continue
                
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            cap.release()
    
    return Response(generate_preview(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@enrollment_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_enrollment():
    """Cancel an enrollment session"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    if session_id in enrollment_sessions:
        del enrollment_sessions[session_id]
        return jsonify({'message': 'Enrollment cancelled'}), 200
    
    return jsonify({'error': 'Invalid session ID'}), 400

@enrollment_bp.route('/list', methods=['GET'])
@jwt_required()
def list_enrolled():
    """List all enrolled persons"""
    role = request.args.get('role', 'all')
    
    db = Database()
    
    if role == 'student' or role == 'all':
        students = db.fetch_data(
            """SELECT ID, Name, Course, Sem FROM student_face ORDER BY ID"""
        )
        student_list = [
            {'id': s[0], 'name': s[1], 'course': s[2], 'sem': s[3], 'role': 'student'}
            for s in students
        ]
    else:
        student_list = []
    
    if role == 'staff' or role == 'all':
        staff = db.fetch_data(
            """SELECT ID, Name, Dep FROM staff_face ORDER BY ID"""
        )
        staff_list = [
            {'id': s[0], 'name': s[1], 'dep': s[2], 'role': 'staff'}
            for s in staff
        ]
    else:
        staff_list = []
    
    return jsonify({
        'students': student_list,
        'staff': staff_list
    }), 200

@enrollment_bp.route('/delete/<person_id>', methods=['DELETE'])
@jwt_required()
def delete_enrollment(person_id):
    """Delete an enrolled person"""
    role = request.args.get('role', 'student')
    
    db = Database()
    
    try:
        # Get project root (FaceAttendanceSystem_Web directory)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        if role == 'student':
            db.execute_query("DELETE FROM student_face WHERE ID = %s", (person_id,))
            db.execute_query("DELETE FROM student_attendance WHERE ID = %s", (person_id,))
            image_dir = os.path.join(project_root, 'Student_Face', person_id)
        else:
            db.execute_query("DELETE FROM staff_face WHERE ID = %s", (person_id,))
            db.execute_query("DELETE FROM staff_attendance WHERE ID = %s", (person_id,))
            image_dir = os.path.join(project_root, 'Staff_Face', person_id)
        
        # Delete image folder
        if os.path.exists(image_dir):
            shutil.rmtree(image_dir)
        
        # Delete face data file
        face_engine.delete_person_data(person_id)
        
        return jsonify({'message': f'Deleted {person_id}'}), 200
        
    except Exception as e:
        logging.error(f"Delete error: {e}")
        return jsonify({'error': f'Failed to delete: {str(e)}'}), 500
