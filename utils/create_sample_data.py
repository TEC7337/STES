#!/usr/bin/env python3
"""
Sample Data Generator for Smart Time Entry System (STES)
Creates mock face encodings and test data for demonstration purposes
"""

import os
import sys
import numpy as np
import cv2
import logging
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import pickle

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_database_manager
from config.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_mock_face_encoding(seed=None):
    """
    Generate a mock face encoding for testing
    
    Args:
        seed (int, optional): Random seed for reproducible results
        
    Returns:
        numpy.ndarray: Mock face encoding (128-dimensional vector)
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Face encodings are typically 128-dimensional vectors with values between -1 and 1
    encoding = np.random.uniform(-1, 1, 128)
    return encoding

def create_mock_face_image(name, width=400, height=400, save_path=None):
    """
    Create a mock face image for testing
    
    Args:
        name (str): Name to display on the image
        width (int): Image width
        height (int): Image height
        save_path (str, optional): Path to save the image
        
    Returns:
        str: Path to the saved image
    """
    try:
        # Create a colored background
        colors = [
            (100, 149, 237),  # Cornflower blue
            (144, 238, 144),  # Light green
            (255, 182, 193),  # Light pink
            (255, 218, 185),  # Peach
            (221, 160, 221),  # Plum
            (176, 224, 230),  # Powder blue
        ]
        
        # Use hash of name to select consistent color
        color_index = hash(name) % len(colors)
        background_color = colors[color_index]
        
        # Create image
        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Draw a simple face-like circle
        face_size = min(width, height) // 3
        face_x = (width - face_size) // 2
        face_y = (height - face_size) // 2
        
        # Face outline
        draw.ellipse([face_x, face_y, face_x + face_size, face_y + face_size], 
                    fill=(255, 228, 196), outline=(0, 0, 0), width=3)
        
        # Eyes
        eye_size = face_size // 10
        left_eye_x = face_x + face_size // 3
        right_eye_x = face_x + 2 * face_size // 3
        eye_y = face_y + face_size // 3
        
        draw.ellipse([left_eye_x - eye_size, eye_y - eye_size, 
                     left_eye_x + eye_size, eye_y + eye_size], fill=(0, 0, 0))
        draw.ellipse([right_eye_x - eye_size, eye_y - eye_size, 
                     right_eye_x + eye_size, eye_y + eye_size], fill=(0, 0, 0))
        
        # Simple smile
        smile_y = face_y + 2 * face_size // 3
        draw.arc([face_x + face_size // 4, smile_y - face_size // 8, 
                 face_x + 3 * face_size // 4, smile_y + face_size // 8], 
                start=0, end=180, fill=(0, 0, 0), width=3)
        
        # Add name text
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        text_y = height - 60
        draw.text((width // 2, text_y), name, fill=(0, 0, 0), 
                 font=font, anchor="mm")
        
        # Add "MOCK DATA" watermark
        draw.text((width // 2, 30), "MOCK DATA", fill=(255, 0, 0), 
                 font=font, anchor="mm")
        
        # Save image
        if save_path:
            img.save(save_path)
            logger.info(f"📸 Mock face image created: {save_path}")
        
        return save_path
        
    except Exception as e:
        logger.error(f"❌ Error creating mock face image: {e}")
        return None

def create_sample_employees():
    """
    Create sample employees with mock face encodings
    
    Returns:
        list: List of created employee data dicts
    """
    sample_employees = [
        {
            'name': 'Alice Johnson',
            'email': 'alice.johnson@nsight.com',
            'department': 'Engineering',
            'location_id': 3,  # West Coast Office
            'seed': 1001
        },
        {
            'name': 'Bob Smith',
            'email': 'bob.smith@nsight.com',
            'department': 'Data Science',
            'location_id': 2,  # Branch Office
            'seed': 1002
        },
        {
            'name': 'Carol Davis',
            'email': 'carol.davis@nsight.com',
            'department': 'Product Management',
            'location_id': 1,  # Main Office
            'seed': 1003
        },
        {
            'name': 'David Wilson',
            'email': 'david.wilson@nsight.com',
            'department': 'Engineering',
            'location_id': 1,  # Main Office
            'seed': 1004
        },
        {
            'name': 'Emma Brown',
            'email': 'emma.brown@nsight.com',
            'department': 'Marketing',
            'location_id': 1,  # Main Office
            'seed': 1005
        }
    ]
    
    created_employees = []
    
    try:
        config = get_config()
        db_manager = get_database_manager()
        
        # Create employee photos directory
        os.makedirs(config.EMPLOYEE_PHOTOS_PATH, exist_ok=True)
        
        for emp_data in sample_employees:
            # Check if employee already exists
            existing_employee = db_manager.get_employee_by_name(emp_data['name'])
            if existing_employee:
                logger.info(f"👤 Employee already exists: {emp_data['name']}")
                # Add dict with id, name, email, department, and None for face_encoding (will fetch later)
                created_employees.append({
                    'id': existing_employee['id'],
                    'name': existing_employee['name'],
                    'email': emp_data['email'],
                    'department': emp_data['department'],
                    'face_encoding': None
                })
                continue
            
            # Generate mock face encoding
            face_encoding = generate_mock_face_encoding(emp_data['seed'])
            
            # Create mock face image
            image_filename = f"{emp_data['name'].replace(' ', '_').lower()}_mock.png"
            image_path = os.path.join(config.EMPLOYEE_PHOTOS_PATH, image_filename)
            
            create_mock_face_image(emp_data['name'], save_path=image_path)
            
            # Create employee record in database
            employee_id = db_manager.create_employee(
                name=emp_data['name'],
                face_encoding=face_encoding,
                email=emp_data['email'],
                department=emp_data['department'],
                location_id=emp_data.get('location_id', 1)  # Default to location 1
            )
            
            created_employees.append({
                'id': employee_id,
                'name': emp_data['name'],
                'email': emp_data['email'],
                'department': emp_data['department'],
                'face_encoding': face_encoding
            })
            logger.info(f"✅ Created sample employee: {emp_data['name']}")
        
        # For existing employees, fetch their face_encoding from DB
        for emp in created_employees:
            if emp['face_encoding'] is None:
                # Fetch face_encoding from DB
                with db_manager.get_session() as session:
                    from models.database import Employee
                    db_emp = session.query(Employee).filter_by(id=emp['id']).first()
                    if db_emp:
                        import numpy as np
                        emp['face_encoding'] = np.array(db_emp.get_face_encoding())
        
        return created_employees
        
    except Exception as e:
        logger.error(f"❌ Error creating sample employees: {e}")
        import traceback
        traceback.print_exc()
        return []

def create_sample_time_logs(employees, days_back=7):
    """
    Create sample time logs for testing
    
    Args:
        employees (list): List of employee dicts
        days_back (int): Number of days back to create logs for
        
    Returns:
        list: List of created time log objects
    """
    try:
        db_manager = get_database_manager()
        created_logs = []
        
        for employee in employees:
            for day in range(days_back):
                date = datetime.now() - timedelta(days=day)
                
                # Skip weekends for some realism
                if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    continue
                
                # Check if time log already exists
                existing_log = db_manager.get_latest_time_log(employee['id'], date.date())
                if existing_log:
                    logger.info(f"📅 Time log already exists for {employee['name']} on {date.date()}")
                    continue
                
                # Create realistic clock-in/out times with some variation
                base_clock_in = date.replace(hour=8, minute=30, second=0, microsecond=0)
                base_clock_out = date.replace(hour=17, minute=0, second=0, microsecond=0)
                
                # Add some variation (±30 minutes)
                clock_in_variation = np.random.randint(-30, 31)
                clock_out_variation = np.random.randint(-30, 31)
                
                clock_in_time = base_clock_in + timedelta(minutes=clock_in_variation)
                clock_out_time = base_clock_out + timedelta(minutes=clock_out_variation)
                
                # Sometimes create incomplete logs (no clock out)
                if np.random.random() < 0.1:  # 10% chance of incomplete log
                    clock_out_time = None
                
                # Create time log
                time_log = db_manager.create_time_log(
                    employee_id=employee['id'],
                    clock_in=clock_in_time,
                    clock_out=clock_out_time,
                    date=date.date()
                )
                
                created_logs.append(time_log)
                logger.info(f"✅ Created time log for {employee['name']} on {date.date()}")
        
        return created_logs
        
    except Exception as e:
        logger.error(f"❌ Error creating sample time logs: {e}")
        return []

def create_face_encodings_file():
    """
    Create a face encodings pickle file for faster loading
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        config = get_config()
        db_manager = get_database_manager()
        
        # Get all employees as dicts with id, name, and face_encoding
        employees = []
        with db_manager.get_session() as session:
            from models.database import Employee
            db_emps = session.query(Employee).filter_by(is_active=True).all()
            for db_emp in db_emps:
                import numpy as np
                employees.append({
                    'id': db_emp.id,
                    'name': db_emp.name,
                    'face_encoding': np.array(db_emp.get_face_encoding())
                })
        
        if not employees:
            logger.warning("⚠️ No employees found to create face encodings file")
            return False
        
        # Prepare data for pickle file
        encodings = [emp['face_encoding'] for emp in employees]
        names = [emp['name'] for emp in employees]
        
        # Save to pickle file
        os.makedirs(os.path.dirname(config.FACE_ENCODINGS_PATH), exist_ok=True)
        
        data = {
            'encodings': encodings,
            'names': names
        }
        
        import pickle
        with open(config.FACE_ENCODINGS_PATH, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"✅ Face encodings file created with {len(names)} employees")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating face encodings file: {e}")
        return False

def create_system_logs():
    """
    Create some sample system logs for testing
    """
    try:
        db_manager = get_database_manager()
        
        # Sample system events
        events = [
            ('system_startup', 'System started successfully'),
            ('face_detected', 'Face detected in video stream'),
            ('employee_registered', 'New employee registered'),
            ('clock_in', 'Employee clocked in'),
            ('clock_out', 'Employee clocked out'),
            ('error', 'Camera connection lost'),
            ('system_shutdown', 'System shutdown initiated'),
        ]
        
        for event_type, message in events:
            db_manager.log_system_event(
                event_type=event_type,
                message=message,
                details={
                    'timestamp': datetime.now().isoformat(),
                    'source': 'sample_data_generator'
                }
            )
        
        logger.info("✅ Sample system logs created")
        
    except Exception as e:
        logger.error(f"❌ Error creating system logs: {e}")

def main():
    """Main function to create all sample data"""
    
    logger.info("🚀 Starting sample data generation for STES...")
    
    try:
        # Create sample employees
        logger.info("👥 Creating sample employees...")
        employees = create_sample_employees()
        
        if employees:
            # Create sample time logs
            logger.info("📅 Creating sample time logs...")
            time_logs = create_sample_time_logs(employees)
            
            # Create face encodings file
            logger.info("🎯 Creating face encodings file...")
            create_face_encodings_file()
            
            # Create system logs
            logger.info("📝 Creating system logs...")
            create_system_logs()
            
            # Update Power BI export files
            logger.info("🔄 Updating Power BI export files...")
            try:
                from utils.register_employee import update_powerbi_exports
                update_powerbi_exports()  # For sample data, use default location assignment
                logger.info("✅ Power BI export files updated successfully!")
            except Exception as e:
                logger.error(f"❌ Error updating Power BI exports: {e}")
            
            logger.info("🎉 Sample data generation completed successfully!")
            
            # Print summary
            print("\n" + "="*50)
            print("📊 SAMPLE DATA SUMMARY")
            print("="*50)
            print(f"👥 Employees created: {len(employees)}")
            print(f"📅 Time logs created: {len(time_logs)}")
            print(f"🎯 Face encodings file: {'✅ Created' if os.path.exists(get_config().FACE_ENCODINGS_PATH) else '❌ Failed'}")
            print("✅ Power BI export files updated")
            print("="*50)
            
            print("\n🚀 Ready to run the STES system!")
            print("Use the following commands to start:")
            print("  1. Setup database: python db/setup_database.py --sample-data")
            print("  2. Start Streamlit: streamlit run ui/main.py")
            print("  3. Register employees: python utils/register_employee.py --interactive")
            
        else:
            logger.error("❌ Failed to create sample employees")
            
    except Exception as e:
        logger.error(f"❌ Sample data generation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 