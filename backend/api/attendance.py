from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.database import Database
from backend.core.face_recognition_engine import FaceRecognitionEngine
import cv2
import threading
import queue
import logging
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

# Global variables for video streaming
video_capture = None
video_thread = None
video_queue = queue.Queue(maxsize=2)
is_streaming = False
recognition_engine = None
attendance_queue = queue.Queue()
monitoring_start_time = None
is_initializing = False

def init_attendance_routes(face_engine: FaceRecognitionEngine):
    """Initialize routes with face recognition engine"""
    global recognition_engine
    recognition_engine = face_engine

def start_monitoring(camera_source: int = 0):
    """Programmatic start for monitoring (used by app auto-start)"""
    global is_streaming, video_thread, video_capture, monitoring_start_time, is_initializing

    # Avoid duplicate start
    if is_streaming and video_thread and video_thread.is_alive():
        return False, 'Attendance already running'

    # Reset if flag stuck
    if is_streaming and (not video_thread or not video_thread.is_alive()):
        logging.warning("is_streaming flag was stuck, resetting...")
        is_streaming = False
        if video_capture:
            video_capture.release()
            video_capture = None

    # Refresh known faces before starting
    recognition_engine.refresh_known_faces()

    # Start video capture thread
    is_streaming = True
    monitoring_start_time = datetime.now()
    is_initializing = True
    video_thread = threading.Thread(target=video_capture_thread, args=(camera_source,), daemon=True)
    video_thread.start()

    # Start attendance marking thread
    threading.Thread(target=mark_attendance_worker, daemon=True).start()

    return True, 'Attendance monitoring started'

def video_capture_thread(camera_source):
    """Background thread for capturing video frames"""
    global video_capture, is_streaming, video_queue, is_initializing
    
    video_capture = cv2.VideoCapture(camera_source)
    if not video_capture or not video_capture.isOpened():
        logging.error(f"Failed to open camera source {camera_source}")
        is_initializing = False
        is_streaming = False
        return
    
    while is_streaming:
        ret, frame = video_capture.read()
        if ret:
            # Process frame for face recognition
            annotated_frame, detected_persons = recognition_engine.process_frame_for_attendance(frame)
            # First successful frame -> initialization complete
            if is_initializing:
                is_initializing = False
            
            # Add detected persons to attendance queue
            if detected_persons:
                attendance_queue.put(detected_persons)
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            if ret:
                if not video_queue.full():
                    video_queue.put(buffer.tobytes())
    
    if video_capture:
        video_capture.release()
        video_capture = None
    is_initializing = False

def generate_video_stream():
    """Generator for video streaming"""
    while is_streaming:
        try:
            frame = video_queue.get(timeout=1)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except queue.Empty:
            continue

@attendance_bp.route('/start', methods=['POST'])
@jwt_required()
def start_attendance():
    """Start attendance monitoring"""
    global monitoring_start_time
    data = request.get_json()
    camera_source = data.get('camera_source', 0)
    ok, msg = start_monitoring(camera_source)
    if not ok:
        return jsonify({'error': msg}), 400
    return jsonify({'message': msg, 'status': 'running'}), 200

@attendance_bp.route('/stop', methods=['POST'])
@jwt_required()
def stop_attendance():
    """Stop attendance monitoring"""
    global is_streaming, video_capture, video_thread, monitoring_start_time, is_initializing
    
    is_streaming = False
    monitoring_start_time = None
    is_initializing = False
    
    # Wait for thread to finish
    if video_thread and video_thread.is_alive():
        video_thread.join(timeout=2)
    
    if video_capture:
        video_capture.release()
        video_capture = None
    
    # Clear queues
    while not video_queue.empty():
        try:
            video_queue.get_nowait()
        except queue.Empty:
            break
    
    while not attendance_queue.empty():
        try:
            attendance_queue.get_nowait()
        except queue.Empty:
            break
    
    video_thread = None
    
    return jsonify({'message': 'Attendance monitoring stopped', 'status': 'stopped'}), 200

@attendance_bp.route('/stream')
def video_stream():
    """Video streaming endpoint"""
    if not is_streaming:
        return jsonify({'error': 'Attendance not running'}), 400
    
    return Response(
        generate_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@attendance_bp.route('/status', methods=['GET'])
@jwt_required()
def get_status():
    """Get attendance system status"""
    return jsonify({
        'is_running': is_streaming,
        'known_faces_count': len(recognition_engine.known_faces),
        'monitoring_since': monitoring_start_time.strftime('%Y-%m-%d %H:%M:%S') if monitoring_start_time else None,
        'is_busy': is_initializing
    }), 200

@attendance_bp.route('/today-summary', methods=['GET'])
@jwt_required()
def get_today_summary():
    """Get today's attendance summary"""
    db = Database()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Count today's attendance
    students_present = db.fetch_data(
        "SELECT COUNT(DISTINCT ID) FROM student_attendance WHERE Date = %s",
        (today,)
    )[0][0]
    
    staff_present = db.fetch_data(
        "SELECT COUNT(DISTINCT ID) FROM staff_attendance WHERE Date = %s",
        (today,)
    )[0][0]
    
    # Total enrolled
    students_total = db.fetch_data("SELECT COUNT(*) FROM student_face")[0][0]
    staff_total = db.fetch_data("SELECT COUNT(*) FROM staff_face")[0][0]
    
    return jsonify({
        'students_present': students_present,
        'students_total': students_total,
        'staff_present': staff_present,
        'staff_total': staff_total,
        'total_enrolled': students_total + staff_total
    }), 200

def mark_attendance_worker():
    """Background worker to mark attendance in database"""
    db = Database()
    last_detected = {}  # Track last detection time for each person
    cooldown_seconds = 30  # Don't mark same person within 30 seconds
    
    while is_streaming:
        try:
            detected_persons = attendance_queue.get(timeout=1)
            current_time = datetime.now()
            date = current_time.strftime("%Y-%m-%d")
            time = current_time.strftime("%H:%M:%S")
            
            for person_id, name, role in detected_persons:
                # Check cooldown
                last_time = last_detected.get(person_id)
                if last_time:
                    seconds_diff = (current_time - last_time).total_seconds()
                    if seconds_diff < cooldown_seconds:
                        continue
                
                # Mark attendance
                try:
                    if role == "student":
                        db.execute_query(
                            """
                            INSERT IGNORE INTO 
                                student_attendance (ID, Date, CheckIn) 
                            VALUES
                                (%s, %s, %s)
                            """,
                            (person_id, date, time),
                        )
                    else:  # staff
                        # Simplified: record only CheckIn, no CheckOut logic
                        db.execute_query(
                            """
                            INSERT IGNORE INTO 
                                staff_attendance (ID, Date, CheckIn) 
                            VALUES
                                (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                CheckIn = VALUES(CheckIn)
                            """,
                            (person_id, date, time),
                        )

                    last_detected[person_id] = current_time
                    logging.info(f"Marked attendance for {name} ({person_id})")
                    print(f"✅ DETECTED: {name} ({person_id}) - {role} at {time}")

                except Exception as e:
                    logging.error(f"Error marking attendance: {e}")
        
        except queue.Empty:
            continue
    
    db.close()
