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
    """Capture a frame for enrollment - supports both client-side and server-side processing"""
    data = request.get_json()
    session_id = data.get('session_id')
    use_client_processing = data.get('use_client_processing', False)
    
    if session_id not in enrollment_sessions:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session = enrollment_sessions[session_id]
    face_capturer = session['face_capturer']
    
    # CLIENT-SIDE PROCESSING MODE (Recommended for Raspberry Pi)
    if use_client_processing:
        descriptor = data.get('descriptor')
        angle = data.get('angle')
        
        if not descriptor or not angle:
            return jsonify({'error': 'Descriptor and angle required for client-side processing'}), 400
        
        # Convert descriptor to numpy array
        descriptor_array = np.array(descriptor, dtype=np.float64)
        
        # Store descriptor directly (no server-side image processing!)
        if not hasattr(face_capturer, 'captured_descriptors'):
            face_capturer.captured_descriptors = []
            face_capturer.captured_angles = []
        
        # Check if angle is different enough
        angle_dict = angle if isinstance(angle, dict) else {'yaw': angle, 'pitch': 0, 'roll': 0}
        new_angle = (angle_dict.get('yaw', 0), angle_dict.get('pitch', 0), angle_dict.get('roll', 0))
        
        # Simple angle difference check
        is_different = True
        if len(face_capturer.captured_angles) > 0:
            for captured_angle in face_capturer.captured_angles:
                yaw_diff = abs(new_angle[0] - captured_angle[0])
                pitch_diff = abs(new_angle[1] - captured_angle[1])
                roll_diff = abs(new_angle[2] - captured_angle[2])
                distance = np.sqrt(yaw_diff**2 + pitch_diff**2 + roll_diff**2)
                if distance < face_capturer.angle_threshold:
                    is_different = False
                    break
        
        status_message = ''
        should_capture = False
        
        if is_different:
            face_capturer.captured_descriptors.append(descriptor_array)
            face_capturer.captured_angles.append(new_angle)
            should_capture = True
            status_message = f'✅ Captured angle: yaw={angle_dict["yaw"]:.1f}° pitch={angle_dict["pitch"]:.1f}°'
        else:
            status_message = f'⚠️ Similar angle detected. Turn your head slightly.'
        
        captured_count = len(face_capturer.captured_descriptors)
        target_count = face_capturer.target_count
        
        return jsonify({
            'captured': should_capture,
            'count': captured_count,
            'target': target_count,
            'message': status_message,
            'complete': captured_count >= target_count
        }), 200
    
    # SERVER-SIDE PROCESSING MODE (Fallback for older browsers)
    else:
        frame_data = data.get('frame')  # Base64 encoded image
        
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
        # CLIENT-SIDE PROCESSING MODE
        if hasattr(face_capturer, 'captured_descriptors'):
            if len(face_capturer.captured_descriptors) < face_capturer.target_count:
                return jsonify({'error': 'Not enough descriptors captured'}), 400
            
            # Save descriptors directly (no image processing!)
            encodings = face_capturer.captured_descriptors
            
            # Save encodings to file
            face_engine.save_encodings_to_file(person_id, encodings, name, role)
        
        # SERVER-SIDE PROCESSING MODE (Fallback)
        else:
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
        
        # Refresh face recognition engine
        face_engine.refresh_known_faces()
        
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
        
        return jsonify({
            'captured': should_capture,
            'captured_count': captured_count,
            'total_required': target_count,
            'message': status_message,
            'complete': captured_count >= target_count
        }), 200
        
    except Exception as e:
        logging.error(f"Server capture error: {e}")
        return jsonify({'error': f'Server capture failed: {str(e)}'}), 500

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
