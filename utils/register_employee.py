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

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import face_recognition, fall back to mock implementation
try:
    import face_recognition
except ImportError:
    # Import the mock implementation from face_recognition_utils
    from utils.face_recognition_utils import MockFaceRecognition
    face_recognition = MockFaceRecognition()

import numpy as np
import os
from db.connection import get_database_manager
from config.config import get_config
from PIL import Image

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
                                   department: Optional[str] = None,
                                   location_id: int = 1) -> bool:
        """
        Register employee from image file
        
        Args:
            name (str): Employee name
            image_path (str): Path to employee image
            email (Optional[str]): Employee email
            department (Optional[str]): Employee department
            location_id (int): Employee location ID (default: 1)
            
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
                department=department,
                location_id=location_id
            )
            
            # Add face to the recognition manager
            self.face_manager.add_new_face(name, face_encoding)
            
            logger.info(f"✅ Employee '{name}' registered successfully at location {location_id}!")
            
            # Log system event
            self.db_manager.log_system_event(
                event_type='employee_registered',
                message=f'New employee registered: {name}',
                employee_id=employee.id,
                details={
                    'email': email,
                    'department': department,
                    'location_id': location_id,
                    'image_path': image_path,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Update Power BI export files
            try:
                # Call the update function directly
                update_powerbi_exports(location_id)
                logger.info(f"✅ Power BI export files updated for {name}")
            except Exception as e:
                logger.error(f"❌ Failed to update Power BI exports for {name}: {e}")
                # Don't fail the registration if Power BI update fails
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error registering employee: {e}")
            return False
    
    def register_employee_with_camera(self, name: str, 
                                    email: Optional[str] = None, 
                                    department: Optional[str] = None,
                                    location_id: int = 1) -> bool:
        """
        Register employee using camera capture
        
        Args:
            name (str): Employee name
            email (Optional[str]): Employee email
            department (Optional[str]): Employee department
            location_id (int): Employee location ID (default: 1)
            
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
            success = self.register_employee_from_image(name, image_path, email, department, location_id)
            
            # The update_powerbi_exports is already called in register_employee_from_image
            # so we don't need to call it again here
            
            return success
            
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


def update_powerbi_exports(location_id=None):
    """
    Update Power BI export CSV files and SQL Server after employee registration
    Only adds new employees without duplicating existing data
    
    Args:
        location_id (int, optional): Location ID for the new employee. If None, uses the location from database.
    """
    try:
        print("🔄 Updating Power BI export files and SQL Server...")
        
        # Start SQL Server sync if available
        try:
            from sql_server_integration import SQLServerIntegration
            sql_server = SQLServerIntegration()
            sql_server.sync_all_data()
            print("🗄️ SQL Server sync completed")
        except ImportError:
            print("ℹ️ SQL Server integration not available")
        except Exception as e:
            print(f"⚠️ SQL Server sync failed: {e}")
        
        import pandas as pd
        import sqlite3
        from datetime import datetime
        
        # Location configurations
        locations = [
            {"id": 1, "name": "Main Office"},
            {"id": 2, "name": "Branch Office"},
            {"id": 3, "name": "West Coast Office"}
        ]
        
        # Connect to database
        conn = sqlite3.connect('stes.db')
        
        # Get all employees from database
        all_employees = pd.read_sql_query("SELECT * FROM employees ORDER BY id", conn)
        
        if all_employees.empty:
            print("❌ No employees found in database")
            conn.close()
            return
        
        print(f"📊 Found {len(all_employees)} employees in database")
        print(f"📊 Latest employee: {all_employees.iloc[-1]['name']} (ID: {all_employees.iloc[-1]['id']})")
        
        # Ensure export directory exists
        os.makedirs('powerbi_exports', exist_ok=True)
        
        # Check existing CSV file to see what's already exported
        employees_file = 'powerbi_exports/all_locations_employees_fixed.csv'
        existing_employee_ids = set()
        
        if os.path.exists(employees_file):
            existing_csv = pd.read_csv(employees_file)
            existing_employee_ids = set(existing_csv['original_id'].astype(int))
            print(f"📊 Found {len(existing_employee_ids)} employees already in CSV")
        
        # Find new employees that need to be added
        new_employees = []
        for _, employee in all_employees.iterrows():
            if employee['id'] not in existing_employee_ids:
                # This is a new employee that needs to be added
                if location_id is None:
                    # Use the location from the database or default to Main Office
                    emp_location_id = employee.get('location_id', 1)
                else:
                    # Use the provided location_id (for the latest employee)
                    emp_location_id = location_id
                
                location_name = next(loc["name"] for loc in locations if loc["id"] == emp_location_id)
                
                # Create new employee record for export
                new_employee = employee.copy()
                new_employee['original_id'] = new_employee['id']
                new_employee['id'] = new_employee['id'] + (emp_location_id - 1) * 1000
                new_employee['location_id'] = emp_location_id
                new_employee['location_name'] = location_name
                new_employee['export_timestamp'] = datetime.now().isoformat()
                
                new_employees.append(new_employee)
                print(f"➕ Found new employee: {employee['name']} (ID: {employee['id']})")
        
        if not new_employees:
            print("✅ All employees are already in the CSV file")
            conn.close()
            return
        
        # Update employees CSV - add all new employees
        if os.path.exists(employees_file):
            # Read existing employees
            existing_employees = pd.read_csv(employees_file)
            
            # Add new employees
            new_employees_df = pd.DataFrame(new_employees)
            updated_employees = pd.concat([existing_employees, new_employees_df], ignore_index=True)
            
            # Save updated file
            updated_employees.to_csv(employees_file, index=False)
            print(f"✅ Added {len(new_employees)} new employees to CSV")
        else:
            # Create new file with all employees
            all_employees_export = []
            for _, employee in all_employees.iterrows():
                emp_location_id = employee.get('location_id', 1)
                location_name = next(loc["name"] for loc in locations if loc["id"] == emp_location_id)
                
                export_employee = employee.copy()
                export_employee['original_id'] = export_employee['id']
                export_employee['id'] = export_employee['id'] + (emp_location_id - 1) * 1000
                export_employee['location_id'] = emp_location_id
                export_employee['location_name'] = location_name
                export_employee['export_timestamp'] = datetime.now().isoformat()
                
                all_employees_export.append(export_employee)
            
            all_employees_df = pd.DataFrame(all_employees_export)
            all_employees_df.to_csv(employees_file, index=False)
            print(f"✅ Created new employees file with {len(all_employees)} employees")
        
        # Update time logs and system logs for new employees
        for new_emp in new_employees:
            emp_id = new_emp['original_id']
            emp_location_id = new_emp['location_id']
            location_name = new_emp['location_name']
            
            # Add time logs for this employee
            time_logs_file = 'powerbi_exports/all_locations_time_logs_fixed.csv'
            new_time_logs = pd.read_sql_query(
                f"SELECT * FROM time_logs WHERE employee_id = {emp_id}", 
                conn
            )
            
            if not new_time_logs.empty:
                for idx, time_log in new_time_logs.iterrows():
                    time_log_copy = time_log.copy()
                    time_log_copy['original_employee_id'] = time_log_copy['employee_id']
                    time_log_copy['employee_id'] = time_log_copy['employee_id'] + (emp_location_id - 1) * 1000
                    time_log_copy['location_id'] = emp_location_id
                    time_log_copy['location_name'] = location_name
                    time_log_copy['export_timestamp'] = datetime.now().isoformat()
                    
                    # Add to existing time logs file
                    if os.path.exists(time_logs_file):
                        existing_time_logs = pd.read_csv(time_logs_file)
                        new_time_log_df = pd.DataFrame([time_log_copy])
                        updated_time_logs = pd.concat([existing_time_logs, new_time_log_df], ignore_index=True)
                        updated_time_logs.to_csv(time_logs_file, index=False)
                    else:
                        new_time_log_df = pd.DataFrame([time_log_copy])
                        new_time_log_df.to_csv(time_logs_file, index=False)
                
                print(f"✅ Added {len(new_time_logs)} time logs for {new_emp['name']}")
            
            # Add system logs for this employee
            system_logs_file = 'powerbi_exports/all_locations_system_logs_fixed.csv'
            new_system_logs = pd.read_sql_query(
                f"SELECT * FROM system_logs WHERE employee_id = {emp_id}", 
                conn
            )
            
            if not new_system_logs.empty:
                for idx, system_log in new_system_logs.iterrows():
                    system_log_copy = system_log.copy()
                    system_log_copy['original_employee_id'] = system_log_copy['employee_id']
                    system_log_copy['employee_id'] = system_log_copy['employee_id'] + (emp_location_id - 1) * 1000
                    system_log_copy['location_id'] = emp_location_id
                    system_log_copy['location_name'] = location_name
                    system_log_copy['export_timestamp'] = datetime.now().isoformat()
                    
                    # Add to existing system logs file
                    if os.path.exists(system_logs_file):
                        existing_system_logs = pd.read_csv(system_logs_file)
                        new_system_log_df = pd.DataFrame([system_log_copy])
                        updated_system_logs = pd.concat([existing_system_logs, new_system_log_df], ignore_index=True)
                        updated_system_logs.to_csv(system_logs_file, index=False)
                    else:
                        new_system_log_df = pd.DataFrame([system_log_copy])
                        new_system_log_df.to_csv(system_logs_file, index=False)
                
                print(f"✅ Added {len(new_system_logs)} system logs for {new_emp['name']}")
        
        conn.close()
        print(f"🎉 Power BI export files updated successfully! Added {len(new_employees)} new employees")
        
    except Exception as e:
        print(f"❌ Error updating Power BI exports: {e}")


def interactive_registration():
    """
    Interactive employee registration
    """
    print("🎯 Smart Time Entry System - Employee Registration")
    print("=" * 50)
    
    # Available locations
    locations = {
        1: "Main Office",
        2: "Branch Office", 
        3: "West Coast Office"
    }
    
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
            
            # Location selection
            print("\n📍 Available Locations:")
            for loc_id, loc_name in locations.items():
                print(f"  {loc_id}. {loc_name}")
            
            location_input = input("Enter location ID (1-3, default 1): ").strip()
            location_id = int(location_input) if location_input.isdigit() and int(location_input) in locations else 1
            
            if name:
                success = registration_manager.register_employee_with_camera(name, email, department, location_id)
                if success:
                    print(f"✅ Employee '{name}' registered successfully at {locations[location_id]}!")
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
            
            # Location selection
            print("\n📍 Available Locations:")
            for loc_id, loc_name in locations.items():
                print(f"  {loc_id}. {loc_name}")
            
            location_input = input("Enter location ID (1-3, default 1): ").strip()
            location_id = int(location_input) if location_input.isdigit() and int(location_input) in locations else 1
            
            if name and image_path:
                success = registration_manager.register_employee_from_image(name, image_path, email, department, location_id)
                if success:
                    print(f"✅ Employee '{name}' registered successfully at {locations[location_id]}!")
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
            # Run Power BI update before exiting
            try:
                update_powerbi_exports()
                print("✅ Power BI export files updated automatically")
            except Exception as e:
                print(f"❌ Power BI update failed: {e}")
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
    parser.add_argument('--location', type=int, choices=[1, 2, 3], default=1,
                       help='Employee location ID (1=Main Office, 2=Branch Office, 3=West Coast Office)')
    parser.add_argument('--camera', action='store_true', 
                       help='Use camera to capture face')
    parser.add_argument('--list', action='store_true', 
                       help='List all employees')
    parser.add_argument('--remove', type=str, help='Remove employee by name')
    
    args = parser.parse_args()
    
    # Always run Power BI update at the end, regardless of what happened
    def run_powerbi_update():
        try:
            update_powerbi_exports()
            print("✅ Power BI export files updated automatically")
        except Exception as e:
            print(f"❌ Power BI update failed: {e}")
    
    # Register the cleanup function to run at exit
    import atexit
    atexit.register(run_powerbi_update)
    
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
                        args.name, args.email, args.department, args.location
                    )
                elif args.image:
                    success = registration_manager.register_employee_from_image(
                        args.name, args.image, args.email, args.department, args.location
                    )
                else:
                    print("❌ Either --camera or --image must be specified")
                    sys.exit(1)
                
                if success:
                    locations = {1: "Main Office", 2: "Branch Office", 3: "West Coast Office"}
                    print(f"✅ Employee '{args.name}' registered successfully at {locations[args.location]}!")
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
    
    # Always run Power BI update at the end
    try:
        update_powerbi_exports()
        print("✅ Power BI export files updated automatically")
    except Exception as e:
        print(f"❌ Power BI update failed: {e}")


if __name__ == '__main__':
    main() 