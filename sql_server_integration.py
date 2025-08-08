#!/usr/bin/env python3
"""
SQL Server Integration for STES
Automatically syncs data from SQLite to SQL Server for Power BI integration
Supports multiple STES systems in the future
"""

import sqlite3
import pandas as pd
import pyodbc
import os
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SQLServerIntegration:
    def __init__(self, sqlite_db_path="stes.db", config_file="sql_server_config.json"):
        """
        Initialize SQL Server integration
        
        Args:
            sqlite_db_path (str): Path to SQLite database
            config_file (str): Path to SQL Server configuration file
        """
        self.sqlite_db_path = sqlite_db_path
        self.config_file = config_file
        self.sql_server_conn = None
        self.is_running = False
        self.thread = None
        self.last_sync_time = None
        
        # Load SQL Server configuration
        self.config = self.load_config()
        
        # Track last known record counts for each table
        self.last_counts = {
            'employees': 0,
            'time_logs': 0,
            'system_logs': 0
        }
        
        # STES system identifier (for multi-location support)
        self.stes_location_id = self.config.get('stes_location_id', 1)
        self.stes_location_name = self.config.get('stes_location_name', 'Main Office')
        
        logger.info(f"🔄 SQL Server Integration initialized for location: {self.stes_location_name}")
    
    def load_config(self) -> Dict:
        """Load SQL Server configuration from file"""
        default_config = {
            'server': 'localhost',
            'database': 'STES_Database',
            'username': 'sa',
            'password': 'YourPassword123!',
            'driver': '{ODBC Driver 17 for SQL Server}',
            'stes_location_id': 1,
            'stes_location_name': 'Main Office',
            'sync_interval': 10,  # seconds
            'auto_create_tables': True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"❌ Error loading config: {e}")
                return default_config
        else:
            # Create default config file
            self.save_config(default_config)
            logger.info(f"📝 Created default config file: {self.config_file}")
            logger.info("⚠️ Please update the SQL Server connection details in the config file")
            return default_config
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Error saving config: {e}")
    
    def get_sql_server_connection(self):
        """Get SQL Server connection string"""
        return (
            f"DRIVER={self.config['driver']};"
            f"SERVER={self.config['server']};"
            f"DATABASE={self.config['database']};"
            f"UID={self.config['username']};"
            f"PWD={self.config['password']};"
            "Trusted_Connection=no;"
        )
    
    def test_sql_server_connection(self) -> bool:
        """Test SQL Server connection"""
        try:
            conn_str = self.get_sql_server_connection()
            conn = pyodbc.connect(conn_str)
            conn.close()
            logger.info("✅ SQL Server connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ SQL Server connection failed: {e}")
            return False
    
    def create_sql_server_tables(self):
        """Create tables in SQL Server if they don't exist"""
        try:
            conn_str = self.get_sql_server_connection()
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Create employees table
            employees_table = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='employees' AND xtype='U')
            CREATE TABLE employees (
                id INT PRIMARY KEY,
                name NVARCHAR(255) NOT NULL,
                email NVARCHAR(255),
                department NVARCHAR(100),
                face_encoding NVARCHAR(MAX),
                is_active BIT DEFAULT 1,
                created_at DATETIME2,
                updated_at DATETIME2,
                stes_location_id INT DEFAULT 1,
                stes_location_name NVARCHAR(100) DEFAULT 'Main Office',
                sync_timestamp DATETIME2 DEFAULT GETDATE()
            )
            """
            
            # Create time_logs table
            time_logs_table = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='time_logs' AND xtype='U')
            CREATE TABLE time_logs (
                id INT PRIMARY KEY,
                employee_id INT NOT NULL,
                clock_in DATETIME2,
                clock_out DATETIME2,
                date DATE,
                duration_hours DECIMAL(5,2),
                status NVARCHAR(50),
                notes NVARCHAR(MAX),
                created_at DATETIME2,
                updated_at DATETIME2,
                stes_location_id INT DEFAULT 1,
                stes_location_name NVARCHAR(100) DEFAULT 'Main Office',
                sync_timestamp DATETIME2 DEFAULT GETDATE()
            )
            """
            
            # Create system_logs table
            system_logs_table = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='system_logs' AND xtype='U')
            CREATE TABLE system_logs (
                id INT PRIMARY KEY,
                event_type NVARCHAR(100),
                employee_id INT,
                message NVARCHAR(MAX),
                details NVARCHAR(MAX),
                timestamp DATETIME2,
                stes_location_id INT DEFAULT 1,
                stes_location_name NVARCHAR(100) DEFAULT 'Main Office',
                sync_timestamp DATETIME2 DEFAULT GETDATE()
            )
            """
            
            # Execute table creation
            cursor.execute(employees_table)
            cursor.execute(time_logs_table)
            cursor.execute(system_logs_table)
            conn.commit()
            conn.close()
            
            logger.info("✅ SQL Server tables created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating SQL Server tables: {e}")
    
    def get_sqlite_counts(self) -> Dict[str, int]:
        """Get current record counts from SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM employees")
            employees_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM time_logs")
            time_logs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            system_logs_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'employees': employees_count,
                'time_logs': time_logs_count,
                'system_logs': system_logs_count
            }
        except Exception as e:
            logger.error(f"❌ Error getting SQLite counts: {e}")
            return self.last_counts
    
    def sync_employees_to_sql_server(self):
        """Sync employees from SQLite to SQL Server"""
        try:
            # Read from SQLite
            conn = sqlite3.connect(self.sqlite_db_path)
            employees_df = pd.read_sql_query("SELECT * FROM employees", conn)
            conn.close()
            
            if employees_df.empty:
                return
            
            # Connect to SQL Server
            conn_str = self.get_sql_server_connection()
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Get existing employee IDs in SQL Server (across all locations)
            cursor.execute("SELECT id FROM employees")
            existing_ids = {row[0] for row in cursor.fetchall()}
            
            # Find new employees that need to be added
            new_employees = []
            for _, row in employees_df.iterrows():
                if row['id'] not in existing_ids:
                    # This is a new employee - add with current location
                    new_employee = row.copy()
                    new_employee['stes_location_id'] = self.stes_location_id
                    new_employee['stes_location_name'] = self.stes_location_name
                    new_employee['sync_timestamp'] = datetime.now()
                    new_employees.append(new_employee)
            
            # Insert only new employees
            for employee in new_employees:
                cursor.execute("""
                    INSERT INTO employees (
                        id, name, email, department, face_encoding, is_active, 
                        created_at, updated_at, stes_location_id, stes_location_name, sync_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    employee['id'], employee['name'], employee.get('email'), employee.get('department'), 
                    employee.get('face_encoding'), employee.get('is_active', 1),
                    employee.get('created_at'), employee.get('updated_at'),
                    employee['stes_location_id'], employee['stes_location_name'], employee['sync_timestamp']
                ))
            
            conn.commit()
            conn.close()
            
            if new_employees:
                logger.info(f"✅ Added {len(new_employees)} new employees to SQL Server")
            else:
                logger.info("✅ No new employees to sync")
            
        except Exception as e:
            logger.error(f"❌ Error syncing employees: {e}")
    
    def sync_time_logs_to_sql_server(self):
        """Sync time logs from SQLite to SQL Server"""
        try:
            # Read from SQLite
            conn = sqlite3.connect(self.sqlite_db_path)
            time_logs_df = pd.read_sql_query("SELECT * FROM time_logs", conn)
            conn.close()
            
            if time_logs_df.empty:
                return
            
            # Connect to SQL Server
            conn_str = self.get_sql_server_connection()
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Get existing time log IDs in SQL Server (across all locations)
            cursor.execute("SELECT id FROM time_logs")
            existing_ids = {row[0] for row in cursor.fetchall()}
            
            # Find new time logs that need to be added
            new_time_logs = []
            for _, row in time_logs_df.iterrows():
                if row['id'] not in existing_ids:
                    # This is a new time log - add with current location
                    new_time_log = row.copy()
                    new_time_log['stes_location_id'] = self.stes_location_id
                    new_time_log['stes_location_name'] = self.stes_location_name
                    new_time_log['sync_timestamp'] = datetime.now()
                    new_time_logs.append(new_time_log)
            
            # Insert only new time logs
            for time_log in new_time_logs:
                cursor.execute("""
                    INSERT INTO time_logs (
                        id, employee_id, clock_in, clock_out, date, duration_hours,
                        status, notes, created_at, updated_at, stes_location_id, 
                        stes_location_name, sync_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    time_log['id'], time_log['employee_id'], time_log.get('clock_in'), time_log.get('clock_out'),
                    time_log.get('date'), time_log.get('duration_hours'), time_log.get('status'), time_log.get('notes'),
                    time_log.get('created_at'), time_log.get('updated_at'),
                    time_log['stes_location_id'], time_log['stes_location_name'], time_log['sync_timestamp']
                ))
            
            conn.commit()
            conn.close()
            
            if new_time_logs:
                logger.info(f"✅ Added {len(new_time_logs)} new time logs to SQL Server")
            else:
                logger.info("✅ No new time logs to sync")
            
        except Exception as e:
            logger.error(f"❌ Error syncing time logs: {e}")
    
    def sync_system_logs_to_sql_server(self):
        """Sync system logs from SQLite to SQL Server"""
        try:
            # Read from SQLite
            conn = sqlite3.connect(self.sqlite_db_path)
            system_logs_df = pd.read_sql_query("SELECT * FROM system_logs", conn)
            conn.close()
            
            if system_logs_df.empty:
                return
            
            # Connect to SQL Server
            conn_str = self.get_sql_server_connection()
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Get existing system log IDs in SQL Server (across all locations)
            cursor.execute("SELECT id FROM system_logs")
            existing_ids = {row[0] for row in cursor.fetchall()}
            
            # Find new system logs that need to be added
            new_system_logs = []
            for _, row in system_logs_df.iterrows():
                if row['id'] not in existing_ids:
                    # This is a new system log - add with current location
                    new_system_log = row.copy()
                    new_system_log['stes_location_id'] = self.stes_location_id
                    new_system_log['stes_location_name'] = self.stes_location_name
                    new_system_log['sync_timestamp'] = datetime.now()
                    new_system_logs.append(new_system_log)
            
            # Insert only new system logs
            for system_log in new_system_logs:
                # Handle None values and data type conversions
                employee_id = system_log.get('employee_id')
                if pd.isna(employee_id):
                    employee_id = None
                
                cursor.execute("""
                    INSERT INTO system_logs (
                        id, event_type, employee_id, message, details, timestamp,
                        stes_location_id, stes_location_name, sync_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    system_log['id'], system_log.get('event_type'), employee_id, 
                    system_log.get('message'), system_log.get('details'), system_log.get('timestamp'),
                    system_log['stes_location_id'], system_log['stes_location_name'], system_log['sync_timestamp']
                ))
            
            conn.commit()
            conn.close()
            
            if new_system_logs:
                logger.info(f"✅ Added {len(new_system_logs)} new system logs to SQL Server")
            else:
                logger.info("✅ No new system logs to sync")
            
        except Exception as e:
            logger.error(f"❌ Error syncing system logs: {e}")
    
    def sync_all_data(self):
        """Sync all data from SQLite to SQL Server"""
        try:
            logger.info("🔄 Starting SQL Server sync...")
            
            # Sync all tables
            self.sync_employees_to_sql_server()
            self.sync_time_logs_to_sql_server()
            self.sync_system_logs_to_sql_server()
            
            self.last_sync_time = datetime.now()
            logger.info("✅ SQL Server sync completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error during SQL Server sync: {e}")
    
    def has_changes(self) -> bool:
        """Check if SQLite database has new records"""
        current_counts = self.get_sqlite_counts()
        
        # Check if any table has new records
        has_changes = (
            current_counts['employees'] > self.last_counts['employees'] or
            current_counts['time_logs'] > self.last_counts['time_logs'] or
            current_counts['system_logs'] > self.last_counts['system_logs']
        )
        
        if has_changes:
            logger.info(f"📊 Database changes detected:")
            logger.info(f"   Employees: {self.last_counts['employees']} → {current_counts['employees']}")
            logger.info(f"   Time logs: {self.last_counts['time_logs']} → {current_counts['time_logs']}")
            logger.info(f"   System logs: {self.last_counts['system_logs']} → {current_counts['system_logs']}")
        
        return has_changes
    
    def monitor_and_sync(self):
        """Monitor SQLite database and sync changes to SQL Server"""
        logger.info(f"🔍 Starting SQL Server monitoring (checking every {self.config['sync_interval']} seconds)...")
        
        # Initialize last counts
        self.last_counts = self.get_sqlite_counts()
        logger.info(f"📊 Initial database state: {self.last_counts}")
        
        while self.is_running:
            try:
                # Check for changes
                has_changes = self.has_changes()
                
                if has_changes:
                    # Get current counts for logging
                    current_counts = self.get_sqlite_counts()
                    
                    # Sync to SQL Server
                    self.sync_all_data()
                    
                    # Update last counts
                    self.last_counts = current_counts
                    
                    logger.info("🎯 SQL Server updated! Power BI can now connect to SQL Server.")
                
                # Wait before next check
                time.sleep(self.config['sync_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in SQL Server monitoring: {e}")
                time.sleep(self.config['sync_interval'])
    
    def start_sync(self):
        """Start the SQL Server sync monitoring"""
        if self.is_running:
            logger.warning("⚠️ SQL Server sync is already running")
            return
        
        # Test connection first
        if not self.test_sql_server_connection():
            logger.error("❌ Cannot start sync - SQL Server connection failed")
            return
        
        # Create tables if needed
        if self.config.get('auto_create_tables', True):
            self.create_sql_server_tables()
        
        self.is_running = True
        self.thread = threading.Thread(target=self.monitor_and_sync, daemon=True)
        self.thread.start()
        
        logger.info("🚀 SQL Server sync monitoring started!")
        logger.info("💡 Use facial recognition in the STES system to trigger syncs")
        logger.info("🔄 SQL Server will update automatically when new data is detected")
    
    def stop_sync(self):
        """Stop the SQL Server sync monitoring"""
        if not self.is_running:
            logger.warning("⚠️ SQL Server sync is not running")
            return
        
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("🛑 SQL Server sync monitoring stopped")
    
    def get_status(self):
        """Get current sync status"""
        return {
            'is_running': self.is_running,
            'last_sync_time': self.last_sync_time,
            'last_counts': self.last_counts,
            'sync_interval': self.config['sync_interval'],
            'stes_location': f"{self.stes_location_name} (ID: {self.stes_location_id})"
        }

def main():
    """Main function"""
    print("🔄 STES SQL Server Integration")
    print("=" * 50)
    
    integration = SQLServerIntegration()
    
    try:
        # Start sync monitoring
        integration.start_sync()
        
        print("\n🎯 Instructions:")
        print("1. Keep this script running in the background")
        print("2. Use facial recognition in the STES system")
        print("3. SQL Server will update automatically")
        print("4. Connect Power BI to SQL Server instead of CSV files")
        print("\nPress Ctrl+C to stop monitoring")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping SQL Server sync...")
        integration.stop_sync()
        print("✅ Sync stopped")

if __name__ == "__main__":
    main()

