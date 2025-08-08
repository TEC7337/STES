"""
Database connection utilities for Smart Time Entry System (STES)
Handles database connections and session management
"""

import os
import sys
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Base, Employee, TimeLog, SystemLog
from config.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database manager class to handle connections and operations
    """
    
    def __init__(self, config_env='default'):
        """
        Initialize database manager
        
        Args:
            config_env (str): Configuration environment ('default', 'development', 'production')
        """
        self.config = get_config(config_env)
        self.engine = None
        self.session_maker = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database engine and session maker"""
        try:
            # Create database engine
            self.engine = create_engine(
                self.config.DATABASE_URL,
                echo=self.config.DEBUG,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600    # Recycle connections after 1 hour
            )
            
            # Create session maker
            self.session_maker = sessionmaker(bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            logger.info(f"✅ Database initialized successfully: {self.config.DATABASE_URL}")
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions
        
        Yields:
            Session: SQLAlchemy session object
        """
        session = self.session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_employee(self, name, face_encoding, email=None, department=None, location_id=1):
        """
        Create a new employee record
        
        Args:
            name (str): Employee name
            face_encoding (numpy.ndarray): Face encoding array
            email (str, optional): Employee email
            department (str, optional): Employee department
            location_id (int, optional): Employee location ID (default: 1)
            
        Returns:
            int: Created employee's ID
        """
        with self.get_session() as session:
            employee = Employee(
                name=name,
                email=email,
                department=department,
                location_id=location_id
            )
            employee.set_face_encoding(face_encoding)
            session.add(employee)
            session.flush()  # Get the ID without committing
            logger.info(f"✅ Employee created: {name} (ID: {employee.id}, Location: {location_id})")
            return employee.id
    
    def get_employee_by_name(self, name):
        """
        Get employee by name
        
        Args:
            name (str): Employee name
            
        Returns:
            dict: Dictionary with employee id and name, or None
        """
        with self.get_session() as session:
            emp = session.query(Employee).filter_by(name=name, is_active=True).first()
            if emp:
                return {'id': emp.id, 'name': emp.name}
            return None
    
    def get_all_employees(self):
        """
        Get all active employees as dictionaries
        
        Returns:
            list: List of employee dictionaries with id, name, email, department, is_active, created_at
        """
        with self.get_session() as session:
            employees = session.query(Employee).filter_by(is_active=True).all()
            return [
                {
                    'id': emp.id,
                    'name': emp.name,
                    'email': emp.email,
                    'department': emp.department,
                    'is_active': emp.is_active,
                    'created_at': emp.created_at
                }
                for emp in employees
            ]
    
    def update_employee_name(self, old_name, new_name):
        """
        Update employee name
        
        Args:
            old_name (str): Current employee name
            new_name (str): New employee name
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.get_session() as session:
            emp = session.query(Employee).filter_by(name=old_name, is_active=True).first()
            if emp:
                emp.name = new_name
                logger.info(f"✅ Employee name updated from '{old_name}' to '{new_name}'")
                return True
            return False
    
    def create_time_log(self, employee_id, clock_in=None, clock_out=None, date=None):
        """
        Create a new time log record
        
        Args:
            employee_id (int): Employee ID
            clock_in (datetime, optional): Clock-in time
            clock_out (datetime, optional): Clock-out time
            date (datetime, optional): Date of the session
            
        Returns:
            int: Created time log ID
        """
        from datetime import datetime
        
        with self.get_session() as session:
            time_log = TimeLog(
                employee_id=employee_id,
                clock_in=clock_in,
                clock_out=clock_out,
                date=date or datetime.now().date()
            )
            time_log.update_status()
            session.add(time_log)
            session.flush()
            logger.info(f"✅ Time log created for employee {employee_id}")
            return time_log.id
    
    def get_latest_time_log(self, employee_id, date=None):
        """
        Get the latest time log for an employee on a specific date as dictionary
        
        Args:
            employee_id (int): Employee ID
            date (datetime, optional): Date to check (defaults to today)
            
        Returns:
            dict: Latest time log dictionary or None
        """
        from datetime import datetime
        from sqlalchemy import func
        
        if date is None:
            date = datetime.now().date()
        
        with self.get_session() as session:
            # Convert date to datetime for comparison, or use date() function
            log = session.query(TimeLog).filter(
                TimeLog.employee_id == employee_id,
                func.date(TimeLog.date) == date
            ).order_by(TimeLog.created_at.desc()).first()
            
            if log:
                return {
                    'id': log.id,
                    'employee_id': log.employee_id,
                    'clock_in': log.clock_in,
                    'clock_out': log.clock_out,
                    'date': log.date,
                    'duration_hours': log.duration_hours,
                    'status': log.status,
                    'created_at': log.created_at
                }
            return None
    
    def update_time_log_checkin(self, time_log_id, clock_in_time):
        """
        Update time log with clock-in time
        
        Args:
            time_log_id (int): Time log ID
            clock_in_time (datetime): Clock-in time
            
        Returns:
            dict: Updated time log dictionary or None
        """
        with self.get_session() as session:
            time_log = session.query(TimeLog).get(time_log_id)
            if time_log:
                time_log.clock_in = clock_in_time
                time_log.update_status()
                logger.info(f"✅ Time log updated with clock-in: {time_log_id}")
                
                # Return as dictionary to avoid session binding issues
                return {
                    'id': time_log.id,
                    'employee_id': time_log.employee_id,
                    'clock_in': time_log.clock_in,
                    'clock_out': time_log.clock_out,
                    'date': time_log.date,
                    'duration_hours': time_log.duration_hours,
                    'status': time_log.status,
                    'created_at': time_log.created_at
                }
            return None

    def update_time_log_checkout(self, time_log_id, clock_out_time):
        """
        Update time log with clock-out time
        
        Args:
            time_log_id (int): Time log ID
            clock_out_time (datetime): Clock-out time
            
        Returns:
            dict: Updated time log dictionary or None
        """
        with self.get_session() as session:
            time_log = session.query(TimeLog).get(time_log_id)
            if time_log:
                time_log.clock_out = clock_out_time
                time_log.calculate_duration()
                time_log.update_status()
                logger.info(f"✅ Time log updated with clock-out: {time_log_id}")
                
                # Return as dictionary to avoid session binding issues
                return {
                    'id': time_log.id,
                    'employee_id': time_log.employee_id,
                    'clock_in': time_log.clock_in,
                    'clock_out': time_log.clock_out,
                    'date': time_log.date,
                    'duration_hours': time_log.duration_hours,
                    'status': time_log.status,
                    'created_at': time_log.created_at
                }
            return None
    
    def log_system_event(self, event_type, message, employee_id=None, details=None):
        """
        Log a system event
        
        Args:
            event_type (str): Type of event
            message (str): Event message
            employee_id (int, optional): Employee ID if applicable
            details (dict, optional): Additional details
            
        Returns:
            SystemLog: Created system log object
        """
        with self.get_session() as session:
            system_log = SystemLog(
                event_type=event_type,
                message=message,
                employee_id=employee_id
            )
            if details:
                system_log.set_details(details)
            session.add(system_log)
            session.flush()
            logger.info(f"📝 System event logged: {event_type}")
            return system_log
    
    def get_time_logs_by_date_range(self, start_date, end_date):
        """
        Get time logs within a date range as dictionaries
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            list: List of time log dictionaries
        """
        with self.get_session() as session:
            logs = session.query(TimeLog).filter(
                TimeLog.date >= start_date,
                TimeLog.date <= end_date
            ).all()
            
            return [
                {
                    'id': log.id,
                    'employee_id': log.employee_id,
                    'employee_name': log.employee.name if log.employee else 'Unknown',
                    'employee_department': log.employee.department if log.employee else 'N/A',
                    'clock_in': log.clock_in,
                    'clock_out': log.clock_out,
                    'date': log.date,
                    'duration_hours': log.duration_hours,
                    'status': log.status,
                    'created_at': log.created_at
                }
                for log in logs
            ]
    
    def get_employee_stats(self, employee_id, start_date=None, end_date=None):
        """
        Get statistics for an employee
        
        Args:
            employee_id (int): Employee ID
            start_date (datetime, optional): Start date for stats
            end_date (datetime, optional): End date for stats
            
        Returns:
            dict: Employee statistics
        """
        with self.get_session() as session:
            query = session.query(TimeLog).filter(TimeLog.employee_id == employee_id)
            
            if start_date:
                query = query.filter(TimeLog.date >= start_date)
            if end_date:
                query = query.filter(TimeLog.date <= end_date)
            
            logs = query.all()
            
            total_days = len(logs)
            completed_days = len([log for log in logs if log.status == 'completed'])
            total_hours = sum([float(log.duration_hours) for log in logs if log.duration_hours])
            
            return {
                'total_days': total_days,
                'completed_days': completed_days,
                'active_days': total_days - completed_days,
                'total_hours': total_hours,
                'average_hours': total_hours / total_days if total_days > 0 else 0
            }


# Global database manager instance
db_manager = None

def get_database_manager(config_env='default'):
    """
    Get the global database manager instance
    
    Args:
        config_env (str): Configuration environment
        
    Returns:
        DatabaseManager: Database manager instance
    """
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(config_env)
    return db_manager

def init_database(config_env='default'):
    """
    Initialize the database
    
    Args:
        config_env (str): Configuration environment
        
    Returns:
        DatabaseManager: Database manager instance
    """
    return get_database_manager(config_env) 