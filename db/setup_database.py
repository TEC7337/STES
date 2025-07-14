#!/usr/bin/env python3
"""
Database setup script for Smart Time Entry System (STES)
Initializes the database with tables and sample data
"""

import os
import sys
from datetime import datetime, timedelta
import logging

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

def setup_database(config_env='default'):
    """
    Set up the database with tables and initial data
    
    Args:
        config_env (str): Configuration environment
    """
    try:
        logger.info("🚀 Starting database setup...")
        
        # Get database manager
        db_manager = get_database_manager(config_env)
        
        logger.info("✅ Database tables created successfully!")
        
        # Create necessary directories
        config = get_config(config_env)
        os.makedirs(os.path.dirname(config.FACE_ENCODINGS_PATH), exist_ok=True)
        os.makedirs(config.EMPLOYEE_PHOTOS_PATH, exist_ok=True)
        os.makedirs(config.LOGS_PATH, exist_ok=True)
        
        logger.info("✅ Required directories created successfully!")
        
        # Log system startup
        db_manager.log_system_event(
            event_type='system_startup',
            message='Database setup completed successfully',
            details={
                'config_env': config_env,
                'database_url': config.DATABASE_URL,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        logger.info("🎉 Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

def create_sample_data(config_env='default'):
    """
    Create sample data for testing
    
    Args:
        config_env (str): Configuration environment
    """
    try:
        logger.info("📊 Creating sample data...")
        
        db_manager = get_database_manager(config_env)
        
        # Sample employees data
        import numpy as np
        sample_employees = [
            {
                'name': 'John Doe',
                'email': 'john.doe@nsight.com',
                'department': 'Engineering',
                'face_encoding': np.array([0.1] * 128)  # Mock face encoding as numpy array
            },
            {
                'name': 'Jane Smith',
                'email': 'jane.smith@nsight.com',
                'department': 'Data Science',
                'face_encoding': np.array([0.2] * 128)  # Mock face encoding as numpy array
            },
            {
                'name': 'Mike Johnson',
                'email': 'mike.johnson@nsight.com',
                'department': 'Product Management',
                'face_encoding': np.array([0.3] * 128)  # Mock face encoding as numpy array
            }
        ]
        
        # Create sample employees and get their IDs
        created_employee_ids = []
        for emp_data in sample_employees:
            # Check if employee already exists
            existing_employee = db_manager.get_employee_by_name(emp_data['name'])
            if not existing_employee:
                employee_id = db_manager.create_employee(
                    name=emp_data['name'],
                    face_encoding=emp_data['face_encoding'],
                    email=emp_data['email'],
                    department=emp_data['department']
                )
                created_employee_ids.append({'id': employee_id, 'name': emp_data['name']})
                logger.info(f"✅ Created sample employee: {emp_data['name']}")
            else:
                created_employee_ids.append({'id': existing_employee['id'], 'name': emp_data['name']})
                logger.info(f"👤 Employee already exists: {emp_data['name']}")
        
        # Create sample time logs
        now = datetime.now()
        for i, emp_info in enumerate(created_employee_ids):
            # Create time logs for the last 3 days
            for days_back in range(3):
                date = now - timedelta(days=days_back)
                
                # Create clock-in entry
                clock_in_time = date.replace(hour=9, minute=0, second=0, microsecond=0)
                clock_out_time = date.replace(hour=17, minute=30, second=0, microsecond=0)
                
                # Add some variation to the times
                clock_in_time += timedelta(minutes=i * 10)
                clock_out_time += timedelta(minutes=i * 15)
                
                # Check if time log already exists
                existing_log = db_manager.get_latest_time_log(emp_info['id'], date.date())
                if not existing_log:
                    time_log = db_manager.create_time_log(
                        employee_id=emp_info['id'],
                        clock_in=clock_in_time,
                        clock_out=clock_out_time,
                        date=date.date()
                    )
                    logger.info(f"✅ Created time log for {emp_info['name']} on {date.date()}")
        
        logger.info("🎉 Sample data created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Sample data creation failed: {e}")
        raise

def reset_database(config_env='default'):
    """
    Reset the database by dropping and recreating all tables
    
    Args:
        config_env (str): Configuration environment
    """
    try:
        logger.info("🔄 Resetting database...")
        
        db_manager = get_database_manager(config_env)
        
        # Drop all tables
        from models.database import Base
        Base.metadata.drop_all(db_manager.engine)
        
        # Recreate tables
        Base.metadata.create_all(db_manager.engine)
        
        logger.info("✅ Database reset completed!")
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        raise

def main():
    """Main function to run database setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description='STES Database Setup')
    parser.add_argument('--env', choices=['default', 'development', 'production'], 
                       default='default', help='Configuration environment')
    parser.add_argument('--reset', action='store_true', 
                       help='Reset database by dropping all tables')
    parser.add_argument('--sample-data', action='store_true', 
                       help='Create sample data for testing')
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            reset_database(args.env)
        
        setup_database(args.env)
        
        if args.sample_data:
            create_sample_data(args.env)
        
        logger.info("🎉 Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 