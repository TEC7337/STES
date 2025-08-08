#!/usr/bin/env python3
"""
Employee Registration Utility for Smart Time Entry System (STES)
Allows registration of new employees with face capture and encoding
"""

import os
import sys
import cv2
import argparse
import logging
from datetime import datetime
from typing import Optional, Tuple, List

import face_recognition
import numpy as np
import os
from db.connection import get_database_manager
from config.config import get_config
from PIL import Image

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_database_manager
from utils.face_recognition_utils import FaceRecognitionManager
from config.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmployeeRegistrationManager:
    """
    Manager class for employee registration
    """
    
    def __init__(self, config_env='default'):
        """
        Initialize Employee Registration Manager
        
        Args:
            config_env (str): Configuration environment
        """
        self.config = get_config(config_env)
        self.db_manager = get_database_manager(config_env)
        self.face_manager = FaceRecognitionManager(self.config)
        
        logger.info("✅ Employee Registration Manager initialized")
    
    def capture_face_from_camera(self, employee_name: str) -> Optional[str]:
        """
        Capture face from camera for employee registration
        
        Args:
            employee_name (str): Name of the employee
            
        Returns:
            Optional[str]: Path to saved image file or None if failed
        """
        try:
            # Initialize camera
            cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
            
            if not cap.isOpened():
                logger.error(f"❌ Cannot open camera {self.config.CAMERA_INDEX}")
                return None
            
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.VIDEO_FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.VIDEO_FRAME_HEIGHT)
            
            logger.info("📸 Face capture started. Press SPACE to capture, ESC to cancel")
            
            captured_frame = None
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.error("❌ Failed to grab frame from camera")
                    break
                
                # Detect faces in the frame
                face_locations, face_encodings = self.face_manager.detect_faces_in_frame(frame)
                
                # Draw bounding boxes around detected faces
                display_frame = frame.copy()
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(display_frame, f"Face Detected", (left, top - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Add instructions
                cv2.putText(display_frame, "Press SPACE to capture, ESC to cancel", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(display_frame, f"Registering: {employee_name}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Display frame
                cv2.imshow('Employee Registration - Face Capture', display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == 32:  # SPACE key
                    if face_locations:
                        captured_frame = frame.copy()
                        logger.info("✅ Face captured successfully!")
                        break
                    else:
                        logger.warning("⚠️ No face detected. Please position your face in the frame.")
                
                elif key == 27:  # ESC key
                    logger.info("❌ Face capture cancelled")
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            if captured_frame is not None:
                # Save the captured frame
                os.makedirs(self.config.EMPLOYEE_PHOTOS_PATH, exist_ok=True)
                filename = f"{employee_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                filepath = os.path.join(self.config.EMPLOYEE_PHOTOS_PATH, filename)
                
                cv2.imwrite(filepath, captured_frame)
                logger.info(f"📸 Face image saved: {filepath}")
                
                return filepath
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error capturing face from camera: {e}")
            return None
    
    def register_employee_from_image(self, name: str, image_path: str, 
                                   email: Optional[str] = None, 
                                   department: Optional[str] = None) -> bool:
        """
        Register employee from image file
        
        Args:
            name (str): Employee name
            image_path (str): Path to employee image
            email (Optional[str]): Employee email
            department (Optional[str]): Employee department
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            # Check if employee already exists
            existing_employee = self.db_manager.get_employee_by_name(name)
            if existing_employee:
                logger.warning(f"⚠️ Employee '{name}' already exists in database")
                return False
            
            # Check if image file exists
            if not os.path.exists(image_path):
                logger.error(f"❌ Image file not found: {image_path}")
                return False
            
            # Generate face encoding from image
            face_encoding = self.face_manager.encode_face_from_image(image_path)
            
            if face_encoding is None:
                logger.error(f"❌ Could not generate face encoding from image: {image_path}")
                return False
            
            # Create employee record in database
            employee = self.db_manager.create_employee(
                name=name,
                face_encoding=face_encoding,
                email=email,
                department=department
            )
            
            # Add face to the recognition manager
            self.face_manager.add_new_face(name, face_encoding)
            
            logger.info(f"✅ Employee '{name}' registered successfully!")
            
            # Log system event
            self.db_manager.log_system_event(
                event_type='employee_registered',
                message=f'New employee registered: {name}',
                employee_id=employee.id,
                details={
                    'email': email,
                    'department': department,
                    'image_path': image_path,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error registering employee: {e}")
            return False
    
    def register_employee_with_camera(self, name: str, 
                                    email: Optional[str] = None, 
                                    department: Optional[str] = None) -> bool:
        """
        Register employee using camera capture
        
        Args:
            name (str): Employee name
            email (Optional[str]): Employee email
            department (Optional[str]): Employee department
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            # Capture face from camera
            image_path = self.capture_face_from_camera(name)
            
            if image_path is None:
                logger.error("❌ Failed to capture face from camera")
                return False
            
            # Register employee using the captured image
            return self.register_employee_from_image(name, image_path, email, department)
            
        except Exception as e:
            logger.error(f"❌ Error registering employee with camera: {e}")
            return False
    
    def list_employees(self) -> List:
        """
        List all registered employees
        
        Returns:
            List: List of employee information
        """
        try:
            employees = self.db_manager.get_all_employees()
            
            employee_list = []
            for emp in employees:
                employee_info = {
                    'id': emp.id,
                    'name': emp.name,
                    'email': emp.email,
                    'department': emp.department,
                    'is_active': emp.is_active,
                    'created_at': emp.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                employee_list.append(employee_info)
            
            return employee_list
            
        except Exception as e:
            logger.error(f"❌ Error listing employees: {e}")
            return []
    
    def remove_employee(self, name: str) -> bool:
        """
        Remove employee from the system
        
        Args:
            name (str): Employee name
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        try:
            # Get employee from database
            employee = self.db_manager.get_employee_by_name(name)
            
            if not employee:
                logger.warning(f"⚠️ Employee '{name}' not found in database")
                return False
            
            # Mark employee as inactive (instead of deleting)
            with self.db_manager.get_session() as session:
                employee.is_active = False
                session.merge(employee)
            
            # Remove from face recognition manager
            if name in self.face_manager.known_face_names:
                index = self.face_manager.known_face_names.index(name)
                self.face_manager.known_face_names.pop(index)
                self.face_manager.known_face_encodings.pop(index)
                self.face_manager.save_known_faces()
            
            logger.info(f"✅ Employee '{name}' removed from system")
            
            # Log system event
            self.db_manager.log_system_event(
                event_type='employee_removed',
                message=f'Employee removed: {name}',
                employee_id=employee.id,
                details={
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing employee: {e}")
            return False


def register_employee_from_images(name, email, department, image_paths):
    """
    Register a new employee using multiple images for face encoding.
    """
    encodings = []
    for img_path in image_paths:
        image = face_recognition.load_image_file(img_path)
        faces = face_recognition.face_encodings(image)
        if faces:
            encodings.append(faces[0])
    if not encodings:
        print(f"No faces found in provided images for {name}.")
        return False
    # Average encoding for robustness
    avg_encoding = np.mean(encodings, axis=0)
    db_manager = get_database_manager()
    db_manager.create_employee(
        name=name,
        face_encoding=avg_encoding,
        email=email,
        department=department
    )
    print(f"✅ Registered {name} with {len(encodings)} face encodings.")
    return True


def interactive_registration():
    """
    Interactive employee registration
    """
    print("🎯 Smart Time Entry System - Employee Registration")
    print("=" * 50)
    
    registration_manager = EmployeeRegistrationManager()
    
    while True:
        print("\nChoose an option:")
        print("1. Register new employee (with camera)")
        print("2. Register new employee (from image file)")
        print("3. List all employees")
        print("4. Remove employee")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            # Register with camera
            name = input("Enter employee name: ").strip()
            email = input("Enter email (optional): ").strip() or None
            department = input("Enter department (optional): ").strip() or None
            
            if name:
                success = registration_manager.register_employee_with_camera(name, email, department)
                if success:
                    print(f"✅ Employee '{name}' registered successfully!")
                else:
                    print(f"❌ Failed to register employee '{name}'")
            else:
                print("❌ Employee name is required")
        
        elif choice == '2':
            # Register from image file
            name = input("Enter employee name: ").strip()
            image_path = input("Enter image file path: ").strip()
            email = input("Enter email (optional): ").strip() or None
            department = input("Enter department (optional): ").strip() or None
            
            if name and image_path:
                success = registration_manager.register_employee_from_image(name, image_path, email, department)
                if success:
                    print(f"✅ Employee '{name}' registered successfully!")
                else:
                    print(f"❌ Failed to register employee '{name}'")
            else:
                print("❌ Employee name and image path are required")
        
        elif choice == '3':
            # List employees
            employees = registration_manager.list_employees()
            if employees:
                print(f"\n📋 Registered Employees ({len(employees)}):")
                print("-" * 80)
                for emp in employees:
                    status = "✅ Active" if emp['is_active'] else "❌ Inactive"
                    print(f"ID: {emp['id']:<3} | Name: {emp['name']:<20} | Email: {emp['email'] or 'N/A':<25} | {status}")
                print("-" * 80)
            else:
                print("📋 No employees registered yet.")
        
        elif choice == '4':
            # Remove employee
            name = input("Enter employee name to remove: ").strip()
            if name:
                success = registration_manager.remove_employee(name)
                if success:
                    print(f"✅ Employee '{name}' removed successfully!")
                else:
                    print(f"❌ Failed to remove employee '{name}'")
            else:
                print("❌ Employee name is required")
        
        elif choice == '5':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-5.")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='STES Employee Registration')
    parser.add_argument('--env', choices=['default', 'development', 'production'], 
                       default='default', help='Configuration environment')
    parser.add_argument('--interactive', action='store_true', 
                       help='Run in interactive mode')
    parser.add_argument('--name', type=str, help='Employee name')
    parser.add_argument('--image', type=str, help='Path to employee image')
    parser.add_argument('--email', type=str, help='Employee email')
    parser.add_argument('--department', type=str, help='Employee department')
    parser.add_argument('--camera', action='store_true', 
                       help='Use camera to capture face')
    parser.add_argument('--list', action='store_true', 
                       help='List all employees')
    parser.add_argument('--remove', type=str, help='Remove employee by name')
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            interactive_registration()
        else:
            registration_manager = EmployeeRegistrationManager(args.env)
            
            if args.list:
                employees = registration_manager.list_employees()
                if employees:
                    print(f"📋 Registered Employees ({len(employees)}):")
                    for emp in employees:
                        status = "✅ Active" if emp['is_active'] else "❌ Inactive"
                        print(f"- {emp['name']} ({emp['email'] or 'No email'}) - {status}")
                else:
                    print("📋 No employees registered yet.")
            
            elif args.remove:
                success = registration_manager.remove_employee(args.remove)
                if success:
                    print(f"✅ Employee '{args.remove}' removed successfully!")
                else:
                    print(f"❌ Failed to remove employee '{args.remove}'")
            
            elif args.name:
                if args.camera:
                    success = registration_manager.register_employee_with_camera(
                        args.name, args.email, args.department
                    )
                elif args.image:
                    success = registration_manager.register_employee_from_image(
                        args.name, args.image, args.email, args.department
                    )
                else:
                    print("❌ Either --camera or --image must be specified")
                    sys.exit(1)
                
                if success:
                    print(f"✅ Employee '{args.name}' registered successfully!")
                else:
                    print(f"❌ Failed to register employee '{args.name}'")
            
            else:
                print("❌ No action specified. Use --interactive or specify registration parameters.")
                print("Run with --help for more information.")
                
    except KeyboardInterrupt:
        print("\n👋 Registration cancelled by user")
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 