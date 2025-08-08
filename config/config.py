"""
Configuration file for Smart Time Entry System (STES)
Contains all configurable parameters for the application
"""

import os
from datetime import timedelta

class Config:
    """Main configuration class for STES"""
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///stes.db')
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'
    
    # Face Recognition Configuration
    FACE_RECOGNITION_TOLERANCE = float(os.getenv('FACE_RECOGNITION_TOLERANCE', '0.6'))
    FACE_DETECTION_MODEL = os.getenv('FACE_DETECTION_MODEL', 'hog')  # 'hog' or 'cnn'
    
    # Time Entry Configuration
    COOLDOWN_MINUTES = int(os.getenv('COOLDOWN_MINUTES', '10'))  # Minutes between clock-in/out
    AUTO_CHECKOUT_HOURS = int(os.getenv('AUTO_CHECKOUT_HOURS', '12'))  # Auto checkout after hours
    
    # Video Configuration
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))  # Default camera
    VIDEO_FRAME_WIDTH = int(os.getenv('VIDEO_FRAME_WIDTH', '640'))
    VIDEO_FRAME_HEIGHT = int(os.getenv('VIDEO_FRAME_HEIGHT', '480'))
    
    # File Paths
    FACE_ENCODINGS_PATH = os.getenv('FACE_ENCODINGS_PATH', 'data/face_encodings.pkl')
    EMPLOYEE_PHOTOS_PATH = os.getenv('EMPLOYEE_PHOTOS_PATH', 'data/employee_photos/')
    LOGS_PATH = os.getenv('LOGS_PATH', 'logs/')
    
    # Streamlit Configuration
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', '8501'))
    STREAMLIT_HOST = os.getenv('STREAMLIT_HOST', 'localhost')
    
    # Tableau Configuration (Optional)
    TABLEAU_SERVER_URL = os.getenv('TABLEAU_SERVER_URL', '')
    TABLEAU_USERNAME = os.getenv('TABLEAU_USERNAME', '')
    TABLEAU_PASSWORD = os.getenv('TABLEAU_PASSWORD', '')
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'nsight-stes-secret-key')
    
    @classmethod
    def get_cooldown_timedelta(cls):
        """Get cooldown period as timedelta object"""
        return timedelta(minutes=cls.COOLDOWN_MINUTES)
    
    @classmethod
    def get_auto_checkout_timedelta(cls):
        """Get auto checkout period as timedelta object"""
        return timedelta(hours=cls.AUTO_CHECKOUT_HOURS)

# Development Configuration
class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    DATABASE_URL = 'sqlite:///stes_dev.db'

# Production Configuration
class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/stes')

# Configuration mapping
config_mapping = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': Config
}

def get_config(env='default'):
    """Get configuration based on environment"""
    return config_mapping.get(env, Config) 