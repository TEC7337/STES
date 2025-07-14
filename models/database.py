"""
Database models for Smart Time Entry System (STES)
Defines the database schema using SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import json

Base = declarative_base()

class Employee(Base):
    """
    Employee model to store employee information and face encodings
    """
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), unique=True)
    department = Column(String(50))
    face_encoding = Column(Text, nullable=False)  # JSON string of face encoding array
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to time logs
    time_logs = relationship("TimeLog", back_populates="employee")
    
    def set_face_encoding(self, encoding_array):
        """
        Convert face encoding array to JSON string for storage
        
        Args:
            encoding_array (numpy.ndarray): Face encoding array from face_recognition
        """
        self.face_encoding = json.dumps(encoding_array.tolist())
    
    def get_face_encoding(self):
        """
        Get face encoding as numpy array
        
        Returns:
            list: Face encoding as list (convert to numpy array when using)
        """
        return json.loads(self.face_encoding)
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', department='{self.department}')>"


class TimeLog(Base):
    """
    Time log model to store employee clock-in and clock-out records
    """
    __tablename__ = 'time_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    clock_in = Column(DateTime, nullable=True)
    clock_out = Column(DateTime, nullable=True)
    date = Column(DateTime, nullable=False)  # Date of the work session
    duration_hours = Column(String(10))  # Calculated work duration (e.g., "8.5")
    status = Column(String(20), default='active')  # 'active', 'completed', 'incomplete'
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to employee
    employee = relationship("Employee", back_populates="time_logs")
    
    def calculate_duration(self):
        """
        Calculate work duration in hours
        
        Returns:
            float: Duration in hours, or None if clock_out is not set
        """
        if self.clock_in and self.clock_out:
            duration = self.clock_out - self.clock_in
            hours = duration.total_seconds() / 3600
            self.duration_hours = f"{hours:.2f}"
            return hours
        return None
    
    def update_status(self):
        """Update status based on clock-in/out state"""
        if self.clock_in and self.clock_out:
            self.status = 'completed'
        elif self.clock_in and not self.clock_out:
            self.status = 'active'
        else:
            self.status = 'incomplete'
    
    def __repr__(self):
        return f"<TimeLog(id={self.id}, employee_id={self.employee_id}, date='{self.date}', status='{self.status}')>"


class SystemLog(Base):
    """
    System log model to track system events and errors
    """
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)  # 'face_detected', 'clock_in', 'clock_out', 'error'
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(Text)  # JSON string for additional details
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to employee (optional)
    employee = relationship("Employee")
    
    def set_details(self, details_dict):
        """
        Set details as JSON string
        
        Args:
            details_dict (dict): Dictionary of additional details
        """
        self.details = json.dumps(details_dict)
    
    def get_details(self):
        """
        Get details as dictionary
        
        Returns:
            dict: Details dictionary
        """
        return json.loads(self.details) if self.details else {}
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, event_type='{self.event_type}', timestamp='{self.timestamp}')>"


# Database utility functions
def create_tables(engine):
    """
    Create all database tables
    
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully!")


def get_session_maker(database_url):
    """
    Create a session maker for the database
    
    Args:
        database_url (str): Database connection URL
        
    Returns:
        sessionmaker: SQLAlchemy session maker
    """
    engine = create_engine(database_url, echo=False)
    return sessionmaker(bind=engine), engine


def init_database(database_url):
    """
    Initialize the database with tables
    
    Args:
        database_url (str): Database connection URL
        
    Returns:
        tuple: (session_maker, engine)
    """
    engine = create_engine(database_url, echo=False)
    create_tables(engine)
    session_maker = sessionmaker(bind=engine)
    return session_maker, engine 