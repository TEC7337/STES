#!/usr/bin/env python3
"""
Fix Multi-Location Export with Unique Employee IDs
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def fix_multi_location_export():
    """Export data with unique employee IDs for each location"""
    print("🔧 Fixing multi-location export with unique employee IDs...")
    
    # Sample location configurations
    locations = [
        {"id": 1, "name": "Main Office", "db_path": "stes.db"},
        {"id": 2, "name": "Branch Office", "db_path": "stes.db"},
        {"id": 3, "name": "West Coast Office", "db_path": "stes.db"}
    ]
    
    all_employees = []
    all_time_logs = []
    all_system_logs = []
    
    for location in locations:
        location_id = location["id"]
        location_name = location["name"]
        
        print(f"\n🚀 Processing Location {location_id}: {location_name}")
        
        try:
            # Connect to SQLite database
            conn = sqlite3.connect(location["db_path"])
            
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
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error processing Location {location_id}: {e}")
    
    # Combine all data
    if all_employees:
        combined_employees = pd.concat(all_employees, ignore_index=True)
        combined_employees.to_csv('powerbi_exports/all_locations_employees_fixed.csv', index=False)
        print(f"\n✅ Combined employees: {len(combined_employees)} records")
    
    if all_time_logs:
        combined_time_logs = pd.concat(all_time_logs, ignore_index=True)
        combined_time_logs.to_csv('powerbi_exports/all_locations_time_logs_fixed.csv', index=False)
        print(f"✅ Combined time_logs: {len(combined_time_logs)} records")
    
    if all_system_logs:
        combined_system_logs = pd.concat(all_system_logs, ignore_index=True)
        combined_system_logs.to_csv('powerbi_exports/all_locations_system_logs_fixed.csv', index=False)
        print(f"✅ Combined system_logs: {len(combined_system_logs)} records")
    
    # Verify no duplicates
    print(f"\n🔍 Verifying unique employee IDs...")
    print(f"Unique employee IDs: {combined_employees['id'].nunique()}")
    print(f"Total employees: {len(combined_employees)}")
    
    duplicates = combined_employees['id'].value_counts()
    duplicate_ids = duplicates[duplicates > 1]
    
    if len(duplicate_ids) == 0:
        print("✅ No duplicate employee IDs found!")
    else:
        print(f"❌ Still found {len(duplicate_ids)} duplicate IDs")
    
    print(f"\n🎯 Fixed files created:")
    print(f"   - all_locations_employees_fixed.csv")
    print(f"   - all_locations_time_logs_fixed.csv")
    print(f"   - all_locations_system_logs_fixed.csv")
    
    print(f"\n📋 Employee ID ranges:")
    for location in locations:
        location_employees = combined_employees[combined_employees['location_id'] == location['id']]
        if not location_employees.empty:
            min_id = location_employees['id'].min()
            max_id = location_employees['id'].max()
            print(f"   - {location['name']}: IDs {min_id} to {max_id}")

if __name__ == "__main__":
    fix_multi_location_export() 