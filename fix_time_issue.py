#!/usr/bin/env python3
"""
Fix Time Issues for STES
Check database and create today's record if needed
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database():
    """Check current database status"""
    print("🔍 Checking database status...")
    
    conn = sqlite3.connect('stes.db')
    cursor = conn.cursor()
    
    # Check system date
    system_date = datetime.now().date()
    system_time = datetime.now()
    print(f"📅 System date: {system_date}")
    print(f"🕐 System time: {system_time}")
    
    # Check for Arnav Mehta
    cursor.execute("SELECT id, name FROM employees WHERE name = 'Arnav Mehta'")
    arnav = cursor.fetchone()
    if arnav:
        print(f"👤 Found Arnav Mehta: ID {arnav[0]}")
        
        # Check today's records
        cursor.execute("SELECT COUNT(*) FROM time_logs WHERE employee_id = ? AND DATE(date) = ?", 
                      (arnav[0], system_date))
        today_count = cursor.fetchone()[0]
        print(f"📊 Today's records for Arnav: {today_count}")
        
        # Check recent records
        cursor.execute("SELECT date, clock_in, clock_out, status FROM time_logs WHERE employee_id = ? ORDER BY created_at DESC LIMIT 3", 
                      (arnav[0],))
        recent = cursor.fetchall()
        print(f"📋 Recent records:")
        for i, record in enumerate(recent, 1):
            print(f"  {i}. Date: {record[0]}, Clock-in: {record[1]}, Status: {record[3]}")
    else:
        print("❌ Arnav Mehta not found in database!")
    
    conn.close()

def create_fresh_record():
    """Create a fresh record for today"""
    print("\n🆕 Creating fresh record for today...")
    
    conn = sqlite3.connect('stes.db')
    cursor = conn.cursor()
    
    # Get Arnav's ID
    cursor.execute("SELECT id FROM employees WHERE name = 'Arnav Mehta'")
    arnav = cursor.fetchone()
    
    if not arnav:
        print("❌ Arnav Mehta not found!")
        conn.close()
        return
    
    arnav_id = arnav[0]
    today = datetime.now().date()
    
    # Delete any existing records for today
    cursor.execute("DELETE FROM time_logs WHERE employee_id = ? AND DATE(date) = ?", 
                  (arnav_id, today))
    deleted = cursor.rowcount
    if deleted > 0:
        print(f"🗑️ Deleted {deleted} old records for today")
    
    # Create a fresh record ready for clock-in
    now = datetime.now()
    cursor.execute("""
        INSERT INTO time_logs (employee_id, date, status, created_at, updated_at)
        VALUES (?, ?, 'ready', ?, ?)
    """, (arnav_id, today, now, now))
    
    conn.commit()
    conn.close()
    print("✅ Fresh record created for today!")

def main():
    """Main function"""
    print("🔧 STES Time Issue Fixer")
    print("=" * 50)
    
    check_database()
    
    choice = input("\n❓ Create fresh record for today? (y/n): ").lower().strip()
    if choice == 'y':
        create_fresh_record()
        print("\n✅ Done! Now try the face recognition again.")
    else:
        print("👋 No changes made.")

if __name__ == "__main__":
    main() 