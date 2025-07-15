#!/usr/bin/env python3
"""
Full Debug Script for STES Face Recognition Issue
"""

import sys
import sqlite3
from datetime import datetime, timedelta
sys.path.append('.')

from utils.time_entry_manager import TimeEntryManager
from config.config import get_config

def debug_everything():
    """Debug all aspects of the system"""
    print("🔍 FULL SYSTEM DEBUG")
    print("=" * 60)
    
    # 1. Check database state
    print("\n1️⃣ DATABASE STATE:")
    conn = sqlite3.connect('stes.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, employee_id, clock_in, clock_out, status, created_at FROM time_logs WHERE employee_id = 9 ORDER BY created_at DESC LIMIT 3')
    rows = cursor.fetchall()
    print("Recent time logs for Arnav (ID 9):")
    for row in rows:
        print(f"  ID: {row[0]}, Clock-in: {row[2]}, Clock-out: {row[3]}, Status: {row[4]}, Created: {row[5]}")
    
    conn.close()
    
    # 2. Check configuration
    print("\n2️⃣ CONFIGURATION:")
    config = get_config()
    print(f"  Cooldown minutes: {config.COOLDOWN_MINUTES}")
    print(f"  Cooldown timedelta: {config.get_cooldown_timedelta()}")
    
    # 3. Initialize TimeEntryManager
    print("\n3️⃣ TIME ENTRY MANAGER:")
    manager = TimeEntryManager()
    print(f"  Recent recognitions: {manager.recent_recognitions}")
    print(f"  Stats: {manager.stats}")
    
    # 4. Check employee status step by step
    print("\n4️⃣ EMPLOYEE STATUS CHECK:")
    
    # 4a. Check cooldown directly
    is_cooldown = manager.is_within_cooldown('Arnav Mehta')
    print(f"  Is in cooldown (direct check): {is_cooldown}")
    
    # 4b. Get employee from database
    employee = manager.db_manager.get_employee_by_name('Arnav Mehta')
    print(f"  Employee found: {employee is not None}")
    if employee:
        print(f"  Employee ID: {employee['id']}")
    
    # 4c. Get time log
    if employee:
        today = datetime.now().date()
        time_log = manager.db_manager.get_latest_time_log(employee['id'], today)
        print(f"  Time log found: {time_log is not None}")
        if time_log:
            print(f"  Time log: {time_log}")
    
    # 4d. Full status check
    status = manager.get_employee_status('Arnav Mehta')
    print(f"  Full status: {status}")
    
    # 5. Try to manually clear cooldown and test
    print("\n5️⃣ MANUAL COOLDOWN CLEAR:")
    manager.recent_recognitions = {}
    print(f"  Cleared recent recognitions: {manager.recent_recognitions}")
    
    is_cooldown_after = manager.is_within_cooldown('Arnav Mehta')
    print(f"  Is in cooldown after clear: {is_cooldown_after}")
    
    # 6. Test the actual handle_face_recognition method
    print("\n6️⃣ TESTING HANDLE_FACE_RECOGNITION:")
    results = manager.handle_face_recognition(['Arnav Mehta'])
    print(f"  Results: {results}")
    
    # 7. Check if there's an issue with the cooldown calculation
    print("\n7️⃣ COOLDOWN CALCULATION DEBUG:")
    if 'Arnav Mehta' in manager.recent_recognitions:
        last_time = manager.recent_recognitions['Arnav Mehta']
        now = datetime.now()
        diff = now - last_time
        cooldown_period = manager.config.get_cooldown_timedelta()
        print(f"  Last recognition: {last_time}")
        print(f"  Current time: {now}")
        print(f"  Time difference: {diff}")
        print(f"  Cooldown period: {cooldown_period}")
        print(f"  Is within cooldown: {diff < cooldown_period}")
    else:
        print("  No recent recognition found")

if __name__ == "__main__":
    debug_everything() 