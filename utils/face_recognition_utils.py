"""
Face Recognition Utilities for Smart Time Entry System (STES)
Handles face detection, encoding, and recognition using OpenCV and face_recognition
"""

import cv2
import numpy as np

# Mock face_recognition module for demo purposes
class MockFaceRecognition:
    """Mock face recognition module for demo when dlib is not installed"""
    
    @staticmethod
    def face_locations(image, model="hog"):
        """Mock face detection - returns a fake face location"""
        height, width = image.shape[:2]
        # Return a fake face in the center of the image
        top = height // 4
        right = 3 * width // 4
        bottom = 3 * height // 4
        left = width // 4
        return [(top, right, bottom, left)]
    
    @staticmethod
    def face_encodings(image, face_locations=None):
        """Mock face encoding - returns random encodings"""
        if face_locations is None:
            face_locations = MockFaceRecognition.face_locations(image)
        
        # Return mock encodings for each face
        encodings = []
        for _ in face_locations:
            # Generate a random 128-dimensional encoding
            encoding = np.random.uniform(-1, 1, 128)
            encodings.append(encoding)
        return encodings
    
    @staticmethod
    def compare_faces(known_encodings, face_encoding, tolerance=0.6):
        """Mock face comparison - randomly return matches for demo"""
        # For demo purposes, sometimes return matches
        matches = []
        for known_encoding in known_encodings:
            # Calculate mock distance
            distance = np.random.uniform(0, 1)
            matches.append(distance < tolerance)
        return matches
    
    @staticmethod
    def face_distance(known_encodings, face_encoding):
        """Mock face distance calculation"""
        distances = []
        for _ in known_encodings:
            # Return random distances between 0 and 1
            distance = np.random.uniform(0, 1)
            distances.append(distance)
        return np.array(distances)
    
    @staticmethod
    def load_image_from_file(image_path):
        """Load image using OpenCV instead"""
        image = cv2.imread(image_path)
        if image is not None:
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

import pickle
import os
import logging
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import real face_recognition, fall back to mock
try:
    import face_recognition
    logger.info("✅ Using real face_recognition library")
except ImportError:
    face_recognition = MockFaceRecognition()
    logger.info("⚠️ Using mock face_recognition for demo (install face_recognition for real functionality)")

class FaceRecognitionManager:
    """
    Manager class for face recognition operations
    Handles face detection, encoding, and recognition
    """
    
    def __init__(self, config):
        """
        Initialize the Face Recognition Manager
        
        Args:
            config: Configuration object with face recognition settings
        """
        self.config = config
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        
        # Load known faces
        self.load_known_faces()
        
        logger.info("✅ Face Recognition Manager initialized")
    
    def load_known_faces(self):
        """
        Load known face encodings from file or database
        """
        try:
            # Try to load from pickle file first
            if os.path.exists(self.config.FACE_ENCODINGS_PATH):
                with open(self.config.FACE_ENCODINGS_PATH, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_names = data.get('names', [])
                    logger.info(f"✅ Loaded {len(self.known_face_names)} known faces from file")
            else:
                # Load from database
                self.load_faces_from_database()
                
        except Exception as e:
            logger.error(f"❌ Error loading known faces: {e}")
            self.known_face_encodings = []
            self.known_face_names = []
    
    def load_faces_from_database(self):
        """
        Load face encodings from database
        """
        try:
            from db.connection import get_database_manager
            
            db_manager = get_database_manager()
            employees = db_manager.get_all_employees()
            
            self.known_face_encodings = []
            self.known_face_names = []
            
            # Get face encodings for each employee
            for emp in employees:
                with db_manager.get_session() as session:
                    from models.database import Employee
                    db_emp = session.query(Employee).filter_by(id=emp['id']).first()
                    if db_emp:
                        face_encoding = np.array(db_emp.get_face_encoding())
                        self.known_face_encodings.append(face_encoding)
                        self.known_face_names.append(emp['name'])
            
            logger.info(f"✅ Loaded {len(self.known_face_names)} known faces from database")
            
        except Exception as e:
            logger.error(f"❌ Error loading faces from database: {e}")
    
    def save_known_faces(self):
        """
        Save known face encodings to file
        """
        try:
            os.makedirs(os.path.dirname(self.config.FACE_ENCODINGS_PATH), exist_ok=True)
            
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            
            with open(self.config.FACE_ENCODINGS_PATH, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"✅ Saved {len(self.known_face_names)} known faces to file")
            
        except Exception as e:
            logger.error(f"❌ Error saving known faces: {e}")
    
    def detect_faces_in_frame(self, frame: np.ndarray) -> Tuple[List, List]:
        """
        Detect faces in a single frame
        
        Args:
            frame (np.ndarray): Input frame from camera
            
        Returns:
            Tuple[List, List]: (face_locations, face_encodings)
        """
        try:
            # Convert BGR to RGB (OpenCV uses BGR, face_recognition uses RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize frame for faster processing (optional)
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(
                small_frame, 
                model=self.config.FACE_DETECTION_MODEL
            )
            
            face_encodings = face_recognition.face_encodings(
                small_frame, 
                face_locations
            )
            
            # Scale back up face locations since the frame was scaled down
            face_locations = [(top*4, right*4, bottom*4, left*4) 
                            for (top, right, bottom, left) in face_locations]
            
            return face_locations, face_encodings
            
        except Exception as e:
            logger.error(f"❌ Error detecting faces: {e}")
            return [], []
    
    def recognize_faces(self, face_encodings: List) -> List[str]:
        """
        Recognize faces by comparing with known encodings
        
        Args:
            face_encodings (List): List of face encodings to recognize
            
        Returns:
            List[str]: List of recognized names (or "Unknown" if not recognized)
        """
        face_names = []
        
        for face_encoding in face_encodings:
            # Check if there are any known faces to compare against
            if not self.known_face_encodings:
                face_names.append("Unknown")
                continue
            
            # Compare face encoding with known faces
            matches = face_recognition.compare_faces(
                self.known_face_encodings, 
                face_encoding,
                tolerance=self.config.FACE_RECOGNITION_TOLERANCE
            )
            
            name = "Unknown"
            
            # Use the known face with the smallest distance if a match is found
            if True in matches:
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, 
                    face_encoding
                )
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    
                    # Log the recognition with confidence score
                    confidence = 1 - face_distances[best_match_index]
                    logger.info(f"🎯 Face recognized: {name} (confidence: {confidence:.2f})")
            
            face_names.append(name)
        
        return face_names
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """
        Process a single frame for face recognition
        
        Args:
            frame (np.ndarray): Input frame from camera
            
        Returns:
            Tuple[np.ndarray, List[str]]: (processed_frame, recognized_names)
        """
        try:
            # Detect faces in the frame
            face_locations, face_encodings = self.detect_faces_in_frame(frame)
            
            # Recognize faces
            face_names = self.recognize_faces(face_encodings)
            
            # Store results for drawing
            self.face_locations = face_locations
            self.face_names = face_names
            
            # Draw bounding boxes and labels on the frame
            processed_frame = self.draw_face_boxes(frame, face_locations, face_names)
            
            return processed_frame, face_names
            
        except Exception as e:
            logger.error(f"❌ Error processing frame: {e}")
            return frame, []
    
    def draw_face_boxes(self, frame: np.ndarray, face_locations: List, face_names: List[str]) -> np.ndarray:
        """
        Draw bounding boxes and labels on detected faces
        
        Args:
            frame (np.ndarray): Input frame
            face_locations (List): List of face locations
            face_names (List[str]): List of recognized names
            
        Returns:
            np.ndarray: Frame with drawn bounding boxes and labels
        """
        try:
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Choose color based on recognition status
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)  # Green for known, Red for unknown
                
                # Draw rectangle around face
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw label background
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                
                # Draw label text
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
                
                # Add timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                cv2.putText(frame, timestamp, (left, top - 10), font, 0.5, color, 1)
            
            return frame
            
        except Exception as e:
            logger.error(f"❌ Error drawing face boxes: {e}")
            return frame
    
    def add_new_face(self, name: str, face_encoding: np.ndarray) -> bool:
        """
        Add a new face to the known faces
        
        Args:
            name (str): Name of the person
            face_encoding (np.ndarray): Face encoding
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            # Check if name already exists
            if name in self.known_face_names:
                logger.warning(f"⚠️ Face with name '{name}' already exists")
                return False
            
            # Add to known faces
            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(name)
            
            # Save to file
            self.save_known_faces()
            
            logger.info(f"✅ Added new face: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding new face: {e}")
            return False
    
    def encode_face_from_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Generate face encoding from image file
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            Optional[np.ndarray]: Face encoding or None if face not found
        """
        try:
            # Load image
            image = face_recognition.load_image_from_file(image_path)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                logger.warning(f"⚠️ No face found in image: {image_path}")
                return None
            
            if len(face_encodings) > 1:
                logger.warning(f"⚠️ Multiple faces found in image: {image_path}, using first one")
            
            return face_encodings[0]
            
        except Exception as e:
            logger.error(f"❌ Error encoding face from image: {e}")
            return None
    
    def get_face_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about known faces
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return {
            'total_known_faces': len(self.known_face_names),
            'known_names': self.known_face_names,
            'face_recognition_tolerance': self.config.FACE_RECOGNITION_TOLERANCE,
            'detection_model': self.config.FACE_DETECTION_MODEL
        }


class VideoCapture:
    """
    Enhanced video capture class with face recognition
    """
    
    def __init__(self, config, source=0):
        """
        Initialize video capture
        
        Args:
            config: Configuration object
            source (int): Camera source (default: 0)
        """
        self.config = config
        self.source = source
        self.cap = None
        self.face_manager = FaceRecognitionManager(config)
        self.is_running = False
        
        logger.info("✅ Video Capture initialized")
    
    def start_capture(self):
        """Start video capture"""
        try:
            self.cap = cv2.VideoCapture(self.source)
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.VIDEO_FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.VIDEO_FRAME_HEIGHT)
            
            if not self.cap.isOpened():
                raise Exception(f"Cannot open camera {self.source}")
            
            self.is_running = True
            logger.info(f"✅ Video capture started on source {self.source}")
            
        except Exception as e:
            logger.error(f"❌ Error starting video capture: {e}")
            raise
    
    def stop_capture(self):
        """Stop video capture"""
        try:
            self.is_running = False
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            logger.info("✅ Video capture stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping video capture: {e}")
    
    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Get a single frame from the camera
        
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (success, frame)
        """
        if not self.cap or not self.is_running:
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame
    
    def get_processed_frame(self) -> Tuple[bool, Optional[np.ndarray], List[str]]:
        """
        Get a processed frame with face recognition
        
        Returns:
            Tuple[bool, Optional[np.ndarray], List[str]]: (success, processed_frame, recognized_names)
        """
        ret, frame = self.get_frame()
        
        if not ret or frame is None:
            return False, None, []
        
        processed_frame, face_names = self.face_manager.process_frame(frame)
        return True, processed_frame, face_names 