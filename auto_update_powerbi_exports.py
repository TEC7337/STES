#!/usr/bin/env python3
"""
Auto-Updating Power BI Export Script
Updates the "fixed" CSV files with fresh data for Power BI refresh
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoUpdatingExporter:
    def __init__(self, db_path="stes.db", export_dir="powerbi_exports"):
        self.db_path = db_path
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)
        
    def update_fixed_files(self):
        """Update the 'fixed' CSV files with fresh data"""
        print("🔄 Updating Power BI export files with fresh data...")
        
        try:
            # Connect to SQLite database
            conn = sqlite3.connect(self.db_path)
            print(f"✅ Connected to {self.db_path}")
            
            # Sample location configurations (same as fix_multi_location_export.py)
            locations = [
                {"id": 1, "name": "Main Office", "db_path": self.db_path},
                {"id": 2, "name": "Branch Office", "db_path": self.db_path},
                {"id": 3, "name": "West Coast Office", "db_path": self.db_path}
            ]
            
            all_employees = []
            all_time_logs = []
            all_system_logs = []
            
            for location in locations:
                location_id = location["id"]
                location_name = location["name"]
                
                print(f"\n📊 Processing Location {location_id}: {location_name}")
                
                # Export employees with unique IDs
                employees_df = pd.read_sql_query("SELECT * FROM employees", conn)
                if not employees_df.empty:
                    # Create unique employee IDs for this location
                    employees_df['original_id'] = employees_df['id']
                    employees_df['id'] = employees_df['id'] + (location_id - 1) * 1000  # Unique range per location
                    employees_df['location_id'] = location_id
                    employees_df['location_name'] = location_name
                    employees_df['export_timestamp'] = datetime.now().isoformat()
                    
                    all_employees.append(employees_df)
                    print(f"   ✅ employees: {len(employees_df)} records")
                
                # Export time logs with updated employee IDs
                time_logs_df = pd.read_sql_query("SELECT * FROM time_logs", conn)
                if not time_logs_df.empty:
                    # Update employee_id to match the new unique IDs
                    time_logs_df['original_employee_id'] = time_logs_df['employee_id']
                    time_logs_df['employee_id'] = time_logs_df['employee_id'] + (location_id - 1) * 1000
                    time_logs_df['location_id'] = location_id
                    time_logs_df['location_name'] = location_name
                    time_logs_df['export_timestamp'] = datetime.now().isoformat()
                    
                    all_time_logs.append(time_logs_df)
                    print(f"   ✅ time_logs: {len(time_logs_df)} records")
                
                # Export system logs with updated employee IDs
                system_logs_df = pd.read_sql_query("SELECT * FROM system_logs", conn)
                if not system_logs_df.empty:
                    # Update employee_id to match the new unique IDs (only for non-null values)
                    system_logs_df['original_employee_id'] = system_logs_df['employee_id']
                    system_logs_df['employee_id'] = system_logs_df['employee_id'].apply(
                        lambda x: x + (location_id - 1) * 1000 if pd.notna(x) else x
                    )
                    system_logs_df['location_id'] = location_id
                    system_logs_df['location_name'] = location_name
                    system_logs_df['export_timestamp'] = datetime.now().isoformat()
                    
                    all_system_logs.append(system_logs_df)
                    print(f"   ✅ system_logs: {len(system_logs_df)} records")
            
            # Combine all data and overwrite the "fixed" files
            if all_employees:
                combined_employees = pd.concat(all_employees, ignore_index=True)
                fixed_employees_path = os.path.join(self.export_dir, 'all_locations_employees_fixed.csv')
                combined_employees.to_csv(fixed_employees_path, index=False)
                print(f"\n✅ Updated employees: {len(combined_employees)} records → {fixed_employees_path}")
            
            if all_time_logs:
                combined_time_logs = pd.concat(all_time_logs, ignore_index=True)
                fixed_time_logs_path = os.path.join(self.export_dir, 'all_locations_time_logs_fixed.csv')
                combined_time_logs.to_csv(fixed_time_logs_path, index=False)
                print(f"✅ Updated time_logs: {len(combined_time_logs)} records → {fixed_time_logs_path}")
            
            if all_system_logs:
                combined_system_logs = pd.concat(all_system_logs, ignore_index=True)
                fixed_system_logs_path = os.path.join(self.export_dir, 'all_locations_system_logs_fixed.csv')
                combined_system_logs.to_csv(fixed_system_logs_path, index=False)
                print(f"✅ Updated system_logs: {len(combined_system_logs)} records → {fixed_system_logs_path}")
            
            conn.close()
            
            print(f"\n🎉 Power BI export files updated successfully!")
            print(f"📁 Files updated in: {self.export_dir}/")
            print(f"🔄 Power BI will now refresh with the latest data!")
            
        except Exception as e:
            logger.error(f"❌ Error updating export files: {e}")
            raise
    
    def run_continuous_update(self, interval_minutes=15):
        """Run continuous updates at specified intervals"""
        print(f"🔄 Starting continuous updates every {interval_minutes} minutes...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.update_fixed_files()
                print(f"\n⏰ Next update in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n🛑 Continuous updates stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in continuous update: {e}")

def main():
    """Main function"""
    print("🔄 STES Auto-Updating Power BI Export Tool")
    print("=" * 50)
    
    exporter = AutoUpdatingExporter()
    
    # Check if running in continuous mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = 15  # Default 15 minutes
        if len(sys.argv) > 2:
            try:
                interval = int(sys.argv[2])
            except ValueError:
                pass
        exporter.run_continuous_update(interval)
    else:
        # Single update
        exporter.update_fixed_files()
        
        print(f"\n🎯 Next steps:")
        print(f"1. Power BI will automatically refresh from the updated files")
        print(f"2. Or manually refresh in Power BI Desktop")
        print(f"3. For continuous updates, run: python auto_update_powerbi_exports.py --continuous [minutes]")

if __name__ == "__main__":
    main() 