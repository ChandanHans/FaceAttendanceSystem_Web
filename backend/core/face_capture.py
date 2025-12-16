import cv2
import numpy as np
import face_recognition
import dlib
import os
import json
from typing import List, Tuple, Optional
import logging

class SmartFaceCapture:
    """
    Smart face capture that only saves images when face angle changes significantly.
    This reduces redundancy and improves training efficiency.
    """
    
    def __init__(self, target_count=5, angle_threshold=15.0):
        """
        Args:
            target_count: Number of images to capture (default: 5)
            angle_threshold: Minimum angle difference in degrees to capture new image
        """
        self.target_count = target_count
        self.angle_threshold = angle_threshold
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(self._get_predictor_path())
        self.captured_angles = []
        self.captured_images = []
        
    def _get_predictor_path(self):
        """Get the path to dlib's shape predictor model"""
        # Try to find the predictor in common locations
        try:
            import face_recognition_models
            return face_recognition_models.pose_predictor_model_location()
        except:
            logging.warning("Could not find shape predictor, using basic face detection")
            return None
    
    def calculate_face_angle(self, face_landmarks) -> Tuple[float, float, float]:
        """
        Calculate face angles (yaw, pitch, roll) from facial landmarks.
        
        Args:
            face_landmarks: Dlib face landmarks
            
        Returns:
            Tuple of (yaw, pitch, roll) angles in degrees
        """
        if face_landmarks is None:
            return (0, 0, 0)
        
        # Get 2D coordinates of key facial points
        nose_tip = np.array([face_landmarks.part(30).x, face_landmarks.part(30).y])
        nose_bridge = np.array([face_landmarks.part(27).x, face_landmarks.part(27).y])
        left_eye = np.array([face_landmarks.part(36).x, face_landmarks.part(36).y])
        right_eye = np.array([face_landmarks.part(45).x, face_landmarks.part(45).y])
        left_mouth = np.array([face_landmarks.part(48).x, face_landmarks.part(48).y])
        right_mouth = np.array([face_landmarks.part(54).x, face_landmarks.part(54).y])
        
        # Calculate approximate angles
        # Yaw (left-right rotation)
        eye_center = (left_eye + right_eye) / 2
        horizontal_diff = nose_tip[0] - eye_center[0]
        face_width = np.linalg.norm(right_eye - left_eye)
        yaw = np.degrees(np.arctan2(horizontal_diff, face_width)) * 2
        
        # Pitch (up-down rotation)
        vertical_diff = nose_tip[1] - nose_bridge[1]
        pitch = np.degrees(np.arctan2(vertical_diff, face_width)) * 2
        
        # Roll (tilt)
        roll = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
        
        return (yaw, pitch, roll)
    
    def is_angle_different(self, new_angles: Tuple[float, float, float]) -> bool:
        """
        Check if the new face angle is significantly different from captured angles.
        
        Args:
            new_angles: Tuple of (yaw, pitch, roll) for the new face
            
        Returns:
            True if angle is different enough to capture
        """
        if not self.captured_angles:
            return True
        
        for captured in self.captured_angles:
            angle_diff = np.sqrt(
                (new_angles[0] - captured[0])**2 +
                (new_angles[1] - captured[1])**2 +
                (new_angles[2] - captured[2])**2
            )
            if angle_diff < self.angle_threshold:
                return False
        
        return True
    
    def process_frame(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray], str]:
        """
        Process a frame and determine if it should be captured.
        
        Args:
            frame: Input image frame
            
        Returns:
            Tuple of (should_capture, processed_face, status_message)
        """
        if len(self.captured_images) >= self.target_count:
            return False, None, f"Capture complete: {len(self.captured_images)}/{self.target_count}"
        
        # Detect faces
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.detector(rgb_frame, 1)
        
        if len(faces) == 0:
            return False, None, "No face detected"
        
        if len(faces) > 1:
            return False, None, "Multiple faces detected. Please ensure only one person is in frame."
        
        face = faces[0]
        
        # Get face landmarks if predictor is available
        if self.predictor:
            landmarks = self.predictor(rgb_frame, face)
            angles = self.calculate_face_angle(landmarks)
        else:
            # If no predictor, use face position as a simple angle estimate
            face_center_x = (face.left() + face.right()) / 2
            frame_center_x = frame.shape[1] / 2
            yaw = (face_center_x - frame_center_x) / frame_center_x * 30
            angles = (yaw, 0, 0)
        
        # Check if this angle is different enough
        if self.is_angle_different(angles):
            # Extract face with margin
            margin = 50
            top = max(face.top() - margin, 0)
            right = min(face.right() + margin, frame.shape[1])
            bottom = min(face.bottom() + margin, frame.shape[0])
            left = max(face.left() - margin, 0)
            
            face_img = frame[top:bottom, left:right]
            
            self.captured_angles.append(angles)
            self.captured_images.append(face_img)
            
            return True, face_img, f"Captured {len(self.captured_images)}/{self.target_count} - Try different angle"
        
        return False, None, f"Turn your head to capture different angles ({len(self.captured_images)}/{self.target_count})"
    
    def get_captured_images(self) -> List[np.ndarray]:
        """Get all captured images"""
        return self.captured_images
    
    def save_images(self, output_dir: str, person_id: str):
        """
        Save captured images to disk.
        
        Args:
            output_dir: Directory to save images
            person_id: ID of the person
        """
        person_dir = os.path.join(output_dir, person_id)
        os.makedirs(person_dir, exist_ok=True)
        
        for idx, img in enumerate(self.captured_images, 1):
            filepath = os.path.join(person_dir, f"{idx}.jpg")
            cv2.imwrite(filepath, img)
        
        logging.info(f"Saved {len(self.captured_images)} images for person {person_id}")
        return person_dir
    
    def reset(self):
        """Reset the capture state"""
        self.captured_angles = []
        self.captured_images = []
