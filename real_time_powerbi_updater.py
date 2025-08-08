#!/usr/bin/env python3
"""
Real-Time Power BI Updater
Monitors database changes and automatically updates Power BI export files
"""

import sqlite3
import pandas as pd
import os
import time
import threading
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealTimePowerBIUpdater:
    def __init__(self, db_path="stes.db", export_dir="powerbi_exports", check_interval=5):
        """
        Initialize real-time Power BI updater
        
        Args:
            db_path (str): Path to SQLite database
            export_dir (str): Directory for Power BI exports
            check_interval (int): Seconds between database checks
        """
        self.db_path = db_path
        self.export_dir = export_dir
        self.check_interval = check_interval
        self.last_update_time = None
        self.is_running = False
        self.thread = None
        
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Track last known record counts
        self.last_counts = {
            'time_logs': 0,
            'system_logs': 0
        }
        
        logger.info("🔄 Real-Time Power BI Updater initialized")
    
    def get_current_counts(self):
        """Get current record counts from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get counts
            cursor.execute("SELECT COUNT(*) FROM time_logs")
            time_logs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            system_logs_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'time_logs': time_logs_count,
                'system_logs': system_logs_count
            }
        except Exception as e:
            logger.error(f"❌ Error getting database counts: {e}")
            return self.last_counts
    
    def has_changes(self):
        """Check if database has new records"""
        current_counts = self.get_current_counts()
        
        # Check if any table has new records
        has_changes = (
            current_counts['time_logs'] > self.last_counts['time_logs'] or
            current_counts['system_logs'] > self.last_counts['system_logs']
        )
        
        if has_changes:
            logger.info(f"📊 Database changes detected:")
            logger.info(f"   Time logs: {self.last_counts['time_logs']} → {current_counts['time_logs']}")
            logger.info(f"   System logs: {self.last_counts['system_logs']} → {current_counts['system_logs']}")
        
        return has_changes, current_counts
    
    def update_powerbi_files(self):
        """Update Power BI export files with fresh data"""
        try:
            logger.info("🔄 Updating Power BI export files...")
            
            # Connect to SQLite database
            conn = sqlite3.connect(self.db_path)
            
            # Define original location assignments based on previous data
            location_assignments = {
                1: "Main Office",      # Location 1
                2: "Branch Office",    # Location 2  
                3: "West Coast Office" # Location 3
            }
            
            # Original employee location assignments (based on previous exports)
            employee_locations = {
                1: 3,   # John Doe -> West Coast Office
                2: 1,   # Jane Smith -> Main Office
                3: 1,   # Mike Johnson -> Main Office
                4: 3,   # Alice Johnson -> West Coast Office
                5: 1,   # Bob Smith -> Main Office
                6: 1,   # Carol Davis -> Main Office
                7: 1,   # David Wilson -> Main Office
                8: 1,   # Emma Brown -> Main Office
                9: 3,   # Arnav Mehta -> West Coast Office
                10: 1,  # Sarah Chen -> Main Office
                11: 3,  # Michael Rodriguez -> West Coast Office
                12: 3,  # Lisa Thompson -> West Coast Office
                13: 1,  # James Wilson -> Main Office
                14: 1,  # Emily Davis -> Main Office
                15: 1,  # Robert Kim -> Main Office
                16: 1,  # Jennifer Lee -> Main Office
                17: 1,  # David Martinez -> Main Office
                18: 3,  # Tristan Chang -> West Coast Office
                19: 1,  # Demo -> Main Office
                20: 1,  # demodemo -> Main Office
                21: 1,  # Demo3 -> Main Office
                22: 1,  # demo4 -> Main Office
                23: 1,  # Test Employee -> Main Office
                24: 1,  # demo5 -> Main Office
                25: 1,  # demo6 -> Main Office
                26: 1,  # demo7 -> Main Office
                27: 1,  # demo8 -> Main Office
            }
            
            # Export employees with original IDs (Power BI compatible)
            employees_df = pd.read_sql_query("SELECT * FROM employees", conn)
            if not employees_df.empty:
                # ALWAYS add required columns for Power BI compatibility
                employees_df['original_id'] = employees_df['id']  # Keep original ID for Power BI
                
                # Assign locations based on employee ID
                employees_df['location_id'] = employees_df['id'].map(employee_locations).fillna(1)
                employees_df['location_name'] = employees_df['location_id'].map(location_assignments)
                employees_df['export_timestamp'] = datetime.now().isoformat()
                
                # Ensure all required columns are present
                required_columns = ['id', 'name', 'email', 'department', 'face_encoding', 'is_active', 
                                  'created_at', 'updated_at', 'original_id', 'location_id', 'location_name', 'export_timestamp']
                for col in required_columns:
                    if col not in employees_df.columns:
                        if col == 'original_id':
                            employees_df[col] = employees_df['id']  # Original ID
                        else:
                            employees_df[col] = None
                
                # Save to fixed CSV file
                fixed_employees_path = os.path.join(self.export_dir, 'all_locations_employees_fixed.csv')
                employees_df.to_csv(fixed_employees_path, index=False)
                
                # Verify the file was written correctly
                verification_df = pd.read_csv(fixed_employees_path)
                has_original_id = 'original_id' in verification_df.columns
                logger.info(f"✅ Exported {len(employees_df)} employees with original location assignments")
                logger.info(f"📋 Employee columns: {list(employees_df.columns)}")
                logger.info(f"🔍 Verification - original_id present: {has_original_id}")
            
            # Export time logs with original IDs (Power BI compatible)
            time_logs_df = pd.read_sql_query("SELECT * FROM time_logs", conn)
            if not time_logs_df.empty:
                # ALWAYS add required columns for Power BI compatibility
                time_logs_df['original_employee_id'] = time_logs_df['employee_id']  # Keep original ID for Power BI
                
                # Assign locations based on employee ID
                time_logs_df['location_id'] = time_logs_df['employee_id'].map(employee_locations).fillna(1)
                time_logs_df['location_name'] = time_logs_df['location_id'].map(location_assignments)
                time_logs_df['export_timestamp'] = datetime.now().isoformat()
                
                # Ensure all required columns are present
                required_columns = ['id', 'employee_id', 'clock_in', 'clock_out', 'date', 'duration_hours', 
                                  'status', 'notes', 'created_at', 'updated_at', 'original_employee_id', 
                                  'location_id', 'location_name', 'export_timestamp']
                for col in required_columns:
                    if col not in time_logs_df.columns:
                        if col == 'original_employee_id':
                            time_logs_df[col] = time_logs_df['employee_id']
                        else:
                            time_logs_df[col] = None
                
                # Save to fixed CSV file
                fixed_time_logs_path = os.path.join(self.export_dir, 'all_locations_time_logs_fixed.csv')
                time_logs_df.to_csv(fixed_time_logs_path, index=False)
                
                # Verify the file was written correctly
                verification_df = pd.read_csv(fixed_time_logs_path)
                has_original_employee_id = 'original_employee_id' in verification_df.columns
                logger.info(f"✅ Exported {len(time_logs_df)} time logs with original location assignments")
                logger.info(f"📋 Time logs columns: {list(time_logs_df.columns)}")
                logger.info(f"🔍 Verification - original_employee_id present: {has_original_employee_id}")
            
            # Export system logs with original IDs (Power BI compatible)
            system_logs_df = pd.read_sql_query("SELECT * FROM system_logs", conn)
            if not system_logs_df.empty:
                # ALWAYS add required columns for Power BI compatibility
                system_logs_df['original_employee_id'] = system_logs_df['employee_id']  # Keep original ID for Power BI
                
                # Assign locations based on employee ID (handle NaN values)
                system_logs_df['location_id'] = system_logs_df['employee_id'].map(employee_locations).fillna(1)
                system_logs_df['location_name'] = system_logs_df['location_id'].map(location_assignments)
                system_logs_df['export_timestamp'] = datetime.now().isoformat()
                
                # Ensure all required columns are present
                required_columns = ['id', 'event_type', 'employee_id', 'message', 'details', 'timestamp', 
                                  'original_employee_id', 'location_id', 'location_name', 'export_timestamp']
                for col in required_columns:
                    if col not in system_logs_df.columns:
                        if col == 'original_employee_id':
                            system_logs_df[col] = system_logs_df['employee_id']
                        else:
                            system_logs_df[col] = None
                
                # Save to fixed CSV file
                fixed_system_logs_path = os.path.join(self.export_dir, 'all_locations_system_logs_fixed.csv')
                system_logs_df.to_csv(fixed_system_logs_path, index=False)
                
                # Verify the file was written correctly
                verification_df = pd.read_csv(fixed_system_logs_path)
                has_original_employee_id = 'original_employee_id' in verification_df.columns
                logger.info(f"✅ Exported {len(system_logs_df)} system logs with original location assignments")
                logger.info(f"📋 System logs columns: {list(system_logs_df.columns)}")
                logger.info(f"🔍 Verification - original_employee_id present: {has_original_employee_id}")
            
            conn.close()
            
            self.last_update_time = datetime.now()
            logger.info("✅ Power BI files updated successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error updating Power BI files: {e}")
    
    def monitor_database(self):
        """Monitor database for changes and update Power BI files"""
        logger.info(f"🔍 Starting database monitoring (checking every {self.check_interval} seconds)...")
        
        # Initialize last counts
        self.last_counts = self.get_current_counts()
        logger.info(f"📊 Initial database state: {self.last_counts}")
        
        while self.is_running:
            try:
                # Check for changes
                has_changes, current_counts = self.has_changes()
                
                if has_changes:
                    # Update Power BI files
                    self.update_powerbi_files()
                    
                    # Update last counts
                    self.last_counts = current_counts
                    
                    logger.info("🎯 Power BI files updated! You can now refresh your dashboard.")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in database monitoring: {e}")
                time.sleep(self.check_interval)
    
    def start_monitoring(self):
        """Start the real-time monitoring"""
        if self.is_running:
            logger.warning("⚠️ Monitoring is already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self.monitor_database, daemon=True)
        self.thread.start()
        
        logger.info("🚀 Real-time Power BI monitoring started!")
        logger.info("💡 Use facial recognition in the STES system to trigger updates")
        logger.info("🔄 Power BI files will update automatically when new data is detected")
    
    def stop_monitoring(self):
        """Stop the real-time monitoring"""
        if not self.is_running:
            logger.warning("⚠️ Monitoring is not running")
            return
        
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("🛑 Real-time Power BI monitoring stopped")
    
    def get_status(self):
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'last_update_time': self.last_update_time,
            'last_counts': self.last_counts,
            'check_interval': self.check_interval
        }

def main():
    """Main function"""
    print("🔄 STES Real-Time Power BI Updater")
    print("=" * 50)
    
    updater = RealTimePowerBIUpdater()
    
    try:
        # Start monitoring
        updater.start_monitoring()
        
        print("\n🎯 Instructions:")
        print("1. Keep this script running in the background")
        print("2. Use facial recognition in the STES system")
        print("3. Power BI files will update automatically")
        print("4. Refresh your Power BI dashboard to see new data")
        print("\nPress Ctrl+C to stop monitoring")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping real-time monitoring...")
        updater.stop_monitoring()
        print("✅ Monitoring stopped")

if __name__ == "__main__":
    main() 