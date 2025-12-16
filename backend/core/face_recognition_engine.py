import cv2
import numpy as np
import face_recognition
import dlib
import pickle
import os
import json
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from threading import Lock
from backend.core.lcd_display import LCDDisplay

class FaceRecognitionEngine:
    """
    Core face recognition engine for attendance system.
    Optimized for Raspberry Pi with frame skipping and efficient processing.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the face recognition engine"""
        self.config = self._load_config(config_path)
        self.detector = dlib.get_frontal_face_detector()
        self.known_faces = []
        self.face_data_lock = Lock()
        self.frame_counter = 0
        self.frame_skip = self.config.get('frame_skip', 2)
        
        # Initialize LCD display if enabled
        lcd_config = self.config.get('lcd_display', {})
        if lcd_config.get('enabled', False):
            self.lcd = LCDDisplay(
                i2c_expander=lcd_config.get('i2c_expander', 'PCF8574'),
                address=int(lcd_config.get('address', '0x27'), 16) if isinstance(lcd_config.get('address'), str) else lcd_config.get('address', 0x27),
                port=lcd_config.get('port', 1)
            )
        else:
            self.lcd = None
        
    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration from JSON file"""
        if config_path is None:
            # Get project root (FaceAttendanceSystem_Web directory)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(project_root, 'config', 'config.json')
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def generate_encodings_from_images(self, image_folder: str) -> List[np.ndarray]:
        """
        Generate face encodings from a folder of images.
        
        Args:
            image_folder: Path to folder containing face images
            
        Returns:
            List of face encodings
        """
        encodings = []
        
        if not os.path.exists(image_folder):
            logging.error(f"Image folder not found: {image_folder}")
            return encodings
        
        for filename in os.listdir(image_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(image_folder, filename)
                try:
                    image = face_recognition.load_image_file(filepath)
                    face_encodings = face_recognition.face_encodings(image)
                    
                    if face_encodings:
                        encodings.append(face_encodings[0])
                        logging.info(f"Generated encoding from {filename}")
                    else:
                        logging.warning(f"No face found in {filename}")
                        
                except Exception as e:
                    logging.error(f"Error processing {filename}: {e}")
        
        return encodings
    
    def save_encodings_to_file(self, person_id: str, encodings: List[np.ndarray], 
                                name: str, role: str):
        """
        Save face encodings to disk.
        
        Args:
            person_id: Unique person identifier
            encodings: List of face encodings
            name: Person's name
            role: 'student' or 'staff'
        """
        face_data_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', 'face_data'
        )
        os.makedirs(face_data_dir, exist_ok=True)
        
        data = {
            'id': person_id,
            'name': name,
            'role': role,
            'encodings': encodings,
            'created_at': datetime.now().isoformat()
        }
        
        filepath = os.path.join(face_data_dir, f"{person_id}.pkl")
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        logging.info(f"Saved encodings for {person_id} ({name})")
    
    def load_all_face_data(self) -> List[Dict]:
        """
        Load all face data from disk.
        
        Returns:
            List of face data dictionaries
        """
        # Get project root (FaceAttendanceSystem_Web directory)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        face_data_dir = os.path.join(project_root, 'face_data')
        
        if not os.path.exists(face_data_dir):
            os.makedirs(face_data_dir, exist_ok=True)
            return []
        
        face_data = []
        
        for filename in os.listdir(face_data_dir):
            if filename.endswith('.pkl'):
                filepath = os.path.join(face_data_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        data = pickle.load(f)
                        face_data.append(data)
                except Exception as e:
                    logging.error(f"Error loading {filename}: {e}")
        
        logging.info(f"Loaded {len(face_data)} face profiles")
        return face_data
    
    def refresh_known_faces(self):
        """Reload all known faces from disk"""
        with self.face_data_lock:
            self.known_faces = self.load_all_face_data()
    
    def predict_face(self, face_encoding: np.ndarray) -> Optional[Tuple[str, str, str]]:
        """
        Predict identity from a face encoding.
        
        Args:
            face_encoding: Face encoding to identify
            
        Returns:
            Tuple of (person_id, name, role) or None if no match
        """
        tolerance = self.config.get('recognition_tolerance', 0.42)
        threshold = self.config.get('recognition_threshold', 0.6)
        
        with self.face_data_lock:
            for person_data in self.known_faces:
                if 'encodings' not in person_data:
                    continue
                
                matches = face_recognition.compare_faces(
                    person_data['encodings'], 
                    face_encoding, 
                    tolerance
                )
                
                match_percentage = sum(matches) / len(matches) if matches else 0
                
                if match_percentage >= threshold:
                    return (
                        person_data['id'],
                        person_data['name'],
                        person_data['role']
                    )
        
        return None
    
    def process_frame_for_attendance(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Tuple]]:
        """
        Process a frame for face recognition and mark attendance.
        Optimized with frame skipping for Pi.
        
        Args:
            frame: Input video frame
            
        Returns:
            Tuple of (annotated_frame, detected_persons)
            detected_persons: List of (person_id, name, role) tuples
        """
        self.frame_counter += 1
        
        # Skip frames for performance
        if self.frame_counter % (self.frame_skip + 1) != 0:
            return frame, []
        
        detected_persons = []
        
        # Scale down for faster processing
        scale = self.config.get('scale', 0.5)
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        
        # Detect faces
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = self.detector(rgb_small_frame, 1)
        
        if not face_locations:
            return frame, detected_persons
        
        # Get face encodings
        face_locations_list = [
            (face.top(), face.right(), face.bottom(), face.left()) 
            for face in face_locations
        ]
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations_list)
        
        # Identify faces
        for face_location, face_encoding in zip(face_locations, face_encodings):
            result = self.predict_face(face_encoding)
            
            if result:
                person_id, name, role = result
                detected_persons.append((person_id, name, role))
                
                # Draw rectangle and name on frame
                top = int(face_location.top() / scale)
                right = int(face_location.right() / scale)
                bottom = int(face_location.bottom() / scale)
                left = int(face_location.left() / scale)
                
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(
                    frame, name, (left, bottom + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                )
                
                # Display on LCD if available
                if self.lcd:
                    self.lcd.show_name(name, role)
            else:
                # Unknown face
                top = int(face_location.top() / scale)
                right = int(face_location.right() / scale)
                bottom = int(face_location.bottom() / scale)
                left = int(face_location.left() / scale)
                
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(
                    frame, "Unknown", (left, bottom + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
                )
                
                # Display on LCD if available
                if self.lcd:
                    self.lcd.show_unknown()
        
        return frame, detected_persons
    
    def delete_person_data(self, person_id: str):
        """Delete face data for a person"""
        # Get project root (FaceAttendanceSystem_Web directory)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        face_data_dir = os.path.join(project_root, 'face_data')
        filepath = os.path.join(face_data_dir, f"{person_id}.pkl")
        
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"Deleted face data for {person_id}")
            self.refresh_known_faces()
