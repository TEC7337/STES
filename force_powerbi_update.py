#!/usr/bin/env python3
"""
Force Power BI Update Script
Ensures all Power BI export files have the required columns
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os

def force_powerbi_update():
    """Force update Power BI files with all required columns"""
    
    print("Force updating Power BI export files...")
    
    # Connect to database
    conn = sqlite3.connect('stes.db')
    
    # Define location assignments
    location_assignments = {
        1: "Main Office",
        2: "Branch Office", 
        3: "West Coast Office"
    }
    
    employee_locations = {
        1: 3, 2: 1, 3: 1, 4: 3, 5: 1, 6: 1, 7: 1, 8: 1, 9: 3, 10: 1,
        11: 3, 12: 3, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 3, 19: 1,
        20: 1, 21: 1, 22: 1, 23: 1, 24: 1, 25: 1, 26: 1, 27: 1
    }
    
    # Export employees
    employees_df = pd.read_sql_query("SELECT * FROM employees", conn)
    if not employees_df.empty:
        employees_df['original_id'] = employees_df['id']
        employees_df['location_id'] = employees_df['id'].map(employee_locations).fillna(1)
        employees_df['location_name'] = employees_df['location_id'].map(location_assignments)
        employees_df['export_timestamp'] = datetime.now().isoformat()
        
        employees_path = 'powerbi_exports/all_locations_employees_fixed.csv'
        employees_df.to_csv(employees_path, index=False)
        print(f"Employees: {len(employees_df)} records, columns: {list(employees_df.columns)}")
    
    # Export time logs
    time_logs_df = pd.read_sql_query("SELECT * FROM time_logs", conn)
    if not time_logs_df.empty:
        time_logs_df['original_employee_id'] = time_logs_df['employee_id']
        time_logs_df['location_id'] = time_logs_df['employee_id'].map(employee_locations).fillna(1)
        time_logs_df['location_name'] = time_logs_df['location_id'].map(location_assignments)
        time_logs_df['export_timestamp'] = datetime.now().isoformat()
        
        time_logs_path = 'powerbi_exports/all_locations_time_logs_fixed.csv'
        time_logs_df.to_csv(time_logs_path, index=False)
        print(f"Time logs: {len(time_logs_df)} records, columns: {list(time_logs_df.columns)}")
    
    # Export system logs
    system_logs_df = pd.read_sql_query("SELECT * FROM system_logs", conn)
    if not system_logs_df.empty:
        system_logs_df['original_employee_id'] = system_logs_df['employee_id']
        system_logs_df['location_id'] = system_logs_df['employee_id'].map(employee_locations).fillna(1)
        system_logs_df['location_name'] = system_logs_df['location_id'].map(location_assignments)
        system_logs_df['export_timestamp'] = datetime.now().isoformat()
        
        system_logs_path = 'powerbi_exports/all_locations_system_logs_fixed.csv'
        system_logs_df.to_csv(system_logs_path, index=False)
        print(f"System logs: {len(system_logs_df)} records, columns: {list(system_logs_df.columns)}")
    
    conn.close()
    
    # Verify all required columns are present
    print("\nVerifying required columns...")
    
    # Check employees
    emp_df = pd.read_csv('powerbi_exports/all_locations_employees_fixed.csv')
    has_original_id = 'original_id' in emp_df.columns
    print(f"Employees has original_id: {has_original_id}")
    
    # Check time logs
    time_df = pd.read_csv('powerbi_exports/all_locations_time_logs_fixed.csv')
    has_original_employee_id_time = 'original_employee_id' in time_df.columns
    print(f"Time logs has original_employee_id: {has_original_employee_id_time}")
    
    # Check system logs
    sys_df = pd.read_csv('powerbi_exports/all_locations_system_logs_fixed.csv')
    has_original_employee_id_sys = 'original_employee_id' in sys_df.columns
    print(f"System logs has original_employee_id: {has_original_employee_id_sys}")
    
    if has_original_id and has_original_employee_id_time and has_original_employee_id_sys:
        print("\nAll required columns are present! Power BI should work now.")
    else:
        print("\nSome required columns are missing!")
    
    print(f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    force_powerbi_update() 