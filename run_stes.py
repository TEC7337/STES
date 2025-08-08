#!/usr/bin/env python3
"""
Main launcher script for Smart Time Entry System (STES)
Provides easy commands to run different parts of the system
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print the STES banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║    🎯 Smart Time Entry System (STES)                         ║
    ║    Automated Employee Time Tracking with Face Recognition    ║
    ║                                                               ║
    ║    Built for Nsight Inc. Internship                          ║
    ║    Technologies: Python, OpenCV, face_recognition, SQL       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import cv2
        import streamlit
        import sqlalchemy
        import pandas
        import numpy
        import PIL
        
        # Face recognition is optional - we have mock implementation
        try:
            import face_recognition
            logger.info("✅ All required packages are installed (with real face recognition)")
        except ImportError:
            logger.info("✅ Core packages installed (using mock face recognition for demo)")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Missing required package: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        return False

def setup_database():
    """Set up the database"""
    try:
        logger.info("🔧 Setting up database...")
        result = subprocess.run([
            sys.executable, 'db/setup_database.py', '--sample-data'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Database setup completed")
            return True
        else:
            logger.error(f"❌ Database setup failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database setup error: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    try:
        logger.info("📊 Creating sample data...")
        result = subprocess.run([
            sys.executable, 'utils/create_sample_data.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Sample data created")
            return True
        else:
            logger.error(f"❌ Sample data creation failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Sample data creation error: {e}")
        return False

def run_streamlit():
    """Run the Streamlit web application"""
    try:
        logger.info("🚀 Starting Streamlit web application...")
        logger.info("📱 The web interface will open in your browser")
        logger.info("🔗 URL: http://localhost:8501")
        
        # Run streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'ui/main.py'
        ])
        
    except Exception as e:
        logger.error(f"❌ Streamlit startup error: {e}")

def register_employee():
    """Run the employee registration utility"""
    try:
        logger.info("👥 Starting employee registration...")
        subprocess.run([
            sys.executable, 'utils/register_employee.py', '--interactive'
        ])
        
    except Exception as e:
        logger.error(f"❌ Employee registration error: {e}")

def show_status():
    """Show system status"""
    try:
        from config.config import get_config
        from db.connection import get_database_manager
        
        config = get_config()
        db_manager = get_database_manager()
        
        print("\n" + "="*60)
        print("📊 SYSTEM STATUS")
        print("="*60)
        
        # Database status
        try:
            employees = db_manager.get_all_employees()
            print(f"📚 Database: ✅ Connected ({len(employees)} employees)")
        except Exception as e:
            print(f"📚 Database: ❌ Error - {e}")
        
        # Configuration
        print(f"⚙️  Config: {config.DATABASE_URL}")
        print(f"📹 Camera: Index {config.CAMERA_INDEX}")
        print(f"🎯 Face Recognition: Tolerance {config.FACE_RECOGNITION_TOLERANCE}")
        print(f"⏰ Cooldown: {config.COOLDOWN_MINUTES} minutes")
        
        # File system
        face_encodings_exists = os.path.exists(config.FACE_ENCODINGS_PATH)
        photos_dir_exists = os.path.exists(config.EMPLOYEE_PHOTOS_PATH)
        
        print(f"📁 Face Encodings: {'✅' if face_encodings_exists else '❌'} {config.FACE_ENCODINGS_PATH}")
        print(f"📸 Photos Directory: {'✅' if photos_dir_exists else '❌'} {config.EMPLOYEE_PHOTOS_PATH}")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")

def main():
    """Main function"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description='Smart Time Entry System (STES) - Main Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_stes.py setup           # Set up database and create sample data
  python run_stes.py run             # Run the Streamlit web application
  python run_stes.py register        # Register new employees
  python run_stes.py status          # Show system status
        """
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'run', 'register', 'status', 'install'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force operation (skip confirmations)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'install':
            # Install requirements
            logger.info("📦 Installing requirements...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ])
            
        elif args.command == 'setup':
            # Full system setup
            logger.info("🔧 Setting up STES system...")
            
            if not check_requirements():
                logger.error("❌ Please install requirements first: python run_stes.py install")
                sys.exit(1)
            
            if setup_database():
                logger.info("✅ Database setup completed")
            else:
                logger.error("❌ Database setup failed")
                sys.exit(1)
            
            if create_sample_data():
                logger.info("✅ Sample data created")
            else:
                logger.error("❌ Sample data creation failed")
                sys.exit(1)
            
            logger.info("🎉 STES system setup completed successfully!")
            logger.info("🚀 Run 'python run_stes.py run' to start the web interface")
            
        elif args.command == 'run':
            # Run the main application
            if not check_requirements():
                logger.error("❌ Please install requirements first: python run_stes.py install")
                sys.exit(1)
            
            run_streamlit()
            
        elif args.command == 'register':
            # Register new employees
            if not check_requirements():
                logger.error("❌ Please install requirements first: python run_stes.py install")
                sys.exit(1)
            
            register_employee()
            
        elif args.command == 'status':
            # Show system status
            show_status()
            
    except KeyboardInterrupt:
        logger.info("\n👋 Operation cancelled by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 