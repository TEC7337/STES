"""
SQL Server Database Manager for Smart Time Entry System (STES)
Handles SQL Server connections and data synchronization
"""

import pyodbc
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLServerManager:
    """
    SQL Server database manager for STES system
    Handles connections and data synchronization
    """
    
    def __init__(self, connection_string):
        """
        Initialize SQL Server manager
        
        Args:
            connection_string (str): SQL Server connection string
        """
        self.connection_string = connection_string
        self.engine = None
        self.session_maker = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQL Server connection"""
        try:
            self.engine = create_engine(
                self.connection_string,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self.session_maker = sessionmaker(bind=self.engine)
            logger.info("✅ SQL Server connection established")
        except Exception as e:
            logger.error(f"❌ SQL Server connection failed: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"SQL Server session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self):
        """Test SQL Server connection"""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT 1"))
                logger.info("✅ SQL Server connection test successful")
                return True
        except Exception as e:
            logger.error(f"❌ SQL Server connection test failed: {e}")
            return False
    
    def create_tables(self):
        """Create tables in SQL Server if they don't exist"""
        try:
            with self.get_session() as session:
                # Create employees table
                session.execute(text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='employees' AND xtype='U')
                    CREATE TABLE employees (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        name NVARCHAR(100) NOT NULL UNIQUE,
                        email NVARCHAR(100) UNIQUE,
                        department NVARCHAR(50),
                        face_encoding NVARCHAR(MAX) NOT NULL,
                        is_active BIT DEFAULT 1,
                        created_at DATETIME2 DEFAULT GETDATE(),
                        updated_at DATETIME2 DEFAULT GETDATE()
                    )
                """))
                
                # Create time_logs table
                session.execute(text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='time_logs' AND xtype='U')
                    CREATE TABLE time_logs (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        employee_id INT NOT NULL,
                        clock_in DATETIME2,
                        clock_out DATETIME2,
                        date DATE NOT NULL,
                        duration_hours NVARCHAR(10),
                        status NVARCHAR(20) DEFAULT 'active',
                        notes NVARCHAR(MAX),
                        created_at DATETIME2 DEFAULT GETDATE(),
                        updated_at DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (employee_id) REFERENCES employees(id)
                    )
                """))
                
                # Create system_logs table
                session.execute(text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='system_logs' AND xtype='U')
                    CREATE TABLE system_logs (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        event_type NVARCHAR(50) NOT NULL,
                        employee_id INT,
                        message NVARCHAR(MAX) NOT NULL,
                        details NVARCHAR(MAX),
                        timestamp DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (employee_id) REFERENCES employees(id)
                    )
                """))
                
                session.commit()
                logger.info("✅ SQL Server tables created successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create SQL Server tables: {e}")
            return False
    
    def sync_employee(self, employee_data):
        """
        Sync a single employee to SQL Server
        
        Args:
            employee_data (dict): Employee data from SQLite
        """
        try:
            with self.get_session() as session:
                # Check if employee exists
                existing = session.execute(
                    text("SELECT id FROM employees WHERE name = :name"),
                    {"name": employee_data['name']}
                ).fetchone()
                
                if not existing:
                    # Insert new employee
                    session.execute(text("""
                        INSERT INTO employees (name, email, department, face_encoding, is_active, created_at, updated_at)
                        VALUES (:name, :email, :department, :face_encoding, :is_active, :created_at, :updated_at)
                    """), {
                        'name': employee_data['name'],
                        'email': employee_data['email'],
                        'department': employee_data['department'],
                        'face_encoding': employee_data['face_encoding'],
                        'is_active': employee_data['is_active'],
                        'created_at': employee_data['created_at'],
                        'updated_at': employee_data['updated_at']
                    })
                    logger.info(f"✅ Synced employee: {employee_data['name']}")
                else:
                    # Update existing employee
                    session.execute(text("""
                        UPDATE employees 
                        SET email = :email, department = :department, face_encoding = :face_encoding, 
                            is_active = :is_active, updated_at = :updated_at
                        WHERE name = :name
                    """), {
                        'name': employee_data['name'],
                        'email': employee_data['email'],
                        'department': employee_data['department'],
                        'face_encoding': employee_data['face_encoding'],
                        'is_active': employee_data['is_active'],
                        'updated_at': datetime.now()
                    })
                    logger.info(f"✅ Updated employee: {employee_data['name']}")
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to sync employee {employee_data['name']}: {e}")
            return False
    
    def sync_time_log(self, time_log_data):
        """
        Sync a single time log to SQL Server
        
        Args:
            time_log_data (dict): Time log data from SQLite
        """
        try:
            with self.get_session() as session:
                # Check if time log exists
                existing = session.execute(
                    text("""
                        SELECT id FROM time_logs 
                        WHERE employee_id = :employee_id AND date = :date
                    """),
                    {
                        'employee_id': time_log_data['employee_id'],
                        'date': time_log_data['date']
                    }
                ).fetchone()
                
                if not existing:
                    # Insert new time log
                    session.execute(text("""
                        INSERT INTO time_logs (employee_id, clock_in, clock_out, date, duration_hours, status, notes, created_at, updated_at)
                        VALUES (:employee_id, :clock_in, :clock_out, :date, :duration_hours, :status, :notes, :created_at, :updated_at)
                    """), {
                        'employee_id': time_log_data['employee_id'],
                        'clock_in': time_log_data['clock_in'],
                        'clock_out': time_log_data['clock_out'],
                        'date': time_log_data['date'],
                        'duration_hours': time_log_data['duration_hours'],
                        'status': time_log_data['status'],
                        'notes': time_log_data.get('notes'),
                        'created_at': time_log_data['created_at'],
                        'updated_at': time_log_data['updated_at']
                    })
                    logger.info(f"✅ Synced time log: {time_log_data['id']}")
                else:
                    # Update existing time log
                    session.execute(text("""
                        UPDATE time_logs 
                        SET clock_in = :clock_in, clock_out = :clock_out, duration_hours = :duration_hours,
                            status = :status, notes = :notes, updated_at = :updated_at
                        WHERE employee_id = :employee_id AND date = :date
                    """), {
                        'employee_id': time_log_data['employee_id'],
                        'clock_in': time_log_data['clock_in'],
                        'clock_out': time_log_data['clock_out'],
                        'date': time_log_data['date'],
                        'duration_hours': time_log_data['duration_hours'],
                        'status': time_log_data['status'],
                        'notes': time_log_data.get('notes'),
                        'updated_at': datetime.now()
                    })
                    logger.info(f"✅ Updated time log: {time_log_data['id']}")
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to sync time log {time_log_data['id']}: {e}")
            return False
    
    def sync_system_log(self, system_log_data):
        """
        Sync a single system log to SQL Server
        
        Args:
            system_log_data (dict): System log data from SQLite
        """
        try:
            with self.get_session() as session:
                # Insert system log (no updates needed for logs)
                session.execute(text("""
                    INSERT INTO system_logs (event_type, employee_id, message, details, timestamp)
                    VALUES (:event_type, :employee_id, :message, :details, :timestamp)
                """), {
                    'event_type': system_log_data['event_type'],
                    'employee_id': system_log_data.get('employee_id'),
                    'message': system_log_data['message'],
                    'details': json.dumps(system_log_data.get('details', {})) if system_log_data.get('details') else None,
                    'timestamp': system_log_data['timestamp']
                })
                
                session.commit()
                logger.info(f"✅ Synced system log: {system_log_data['event_type']}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to sync system log: {e}")
            return False
    
    def get_sync_status(self):
        """Get sync status and statistics"""
        try:
            with self.get_session() as session:
                # Get counts from SQL Server
                employee_count = session.execute(text("SELECT COUNT(*) FROM employees")).scalar()
                time_log_count = session.execute(text("SELECT COUNT(*) FROM time_logs")).scalar()
                system_log_count = session.execute(text("SELECT COUNT(*) FROM system_logs")).scalar()
                
                return {
                    'employees': employee_count,
                    'time_logs': time_log_count,
                    'system_logs': system_log_count,
                    'last_sync': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Failed to get sync status: {e}")
            return None 