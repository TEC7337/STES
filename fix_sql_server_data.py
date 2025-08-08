#!/usr/bin/env python3
"""
Fix SQL Server Data
Ensures perfect synchronization between SQLite and SQL Server
"""

import sqlite3
import pyodbc
import json
from datetime import datetime

def fix_sql_server_data():
    """Fix any data issues in SQL Server"""
    print("🔧 Fixing SQL Server Data")
    print("=" * 50)
    
    # Load SQL Server config
    with open('sql_server_config.json', 'r') as f:
        config = json.load(f)
    
    # SQL Server connection
    conn_str = (
        f"DRIVER={config['driver']};"
        f"SERVER={config['server']};"
        f"DATABASE={config['database']};"
        f"UID={config['username']};"
        f"PWD={config['password']};"
        "Trusted_Connection=no;"
    )
    
    try:
        # Connect to SQL Server
        sql_server_conn = pyodbc.connect(conn_str)
        sql_server_cursor = sql_server_conn.cursor()
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect('stes.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        print("✅ Connected to both databases")
        
        # Step 1: Clear all data from SQL Server
        print("\n🧹 Clearing SQL Server data...")
        sql_server_cursor.execute("DELETE FROM system_logs")
        sql_server_cursor.execute("DELETE FROM time_logs")
        sql_server_cursor.execute("DELETE FROM employees")
        sql_server_conn.commit()
        print("✅ Cleared all data from SQL Server")
        
        # Step 2: Re-sync employees
        print("\n👥 Re-syncing employees...")
        sqlite_cursor.execute("SELECT * FROM employees ORDER BY id")
        employees = sqlite_cursor.fetchall()
        
        for employee in employees:
            sql_server_cursor.execute("""
                INSERT INTO employees (
                    id, name, email, department, face_encoding, is_active,
                    created_at, updated_at, stes_location_id, stes_location_name, sync_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                employee[0], employee[1], employee[2], employee[3], employee[4], employee[5],
                employee[6], employee[7], config['stes_location_id'], config['stes_location_name'], datetime.now()
            ))
        
        sql_server_conn.commit()
        print(f"✅ Re-synced {len(employees)} employees")
        
        # Step 3: Re-sync time logs
        print("\n⏰ Re-syncing time logs...")
        sqlite_cursor.execute("SELECT * FROM time_logs ORDER BY id")
        time_logs = sqlite_cursor.fetchall()
        
        for time_log in time_logs:
            sql_server_cursor.execute("""
                INSERT INTO time_logs (
                    id, employee_id, clock_in, clock_out, date, duration_hours,
                    status, notes, created_at, updated_at, stes_location_id, 
                    stes_location_name, sync_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time_log[0], time_log[1], time_log[2], time_log[3], time_log[4], time_log[5],
                time_log[6], time_log[7], time_log[8], time_log[9],
                config['stes_location_id'], config['stes_location_name'], datetime.now()
            ))
        
        sql_server_conn.commit()
        print(f"✅ Re-synced {len(time_logs)} time logs")
        
        # Step 4: Re-sync system logs
        print("\n📊 Re-syncing system logs...")
        sqlite_cursor.execute("SELECT * FROM system_logs ORDER BY id")
        system_logs = sqlite_cursor.fetchall()
        
        for system_log in system_logs:
            # Handle None values
            employee_id = system_log[2] if system_log[2] is not None else None
            
            sql_server_cursor.execute("""
                INSERT INTO system_logs (
                    id, event_type, employee_id, message, details, timestamp,
                    stes_location_id, stes_location_name, sync_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                system_log[0], system_log[1], employee_id, system_log[3], system_log[4], system_log[5],
                config['stes_location_id'], config['stes_location_name'], datetime.now()
            ))
        
        sql_server_conn.commit()
        print(f"✅ Re-synced {len(system_logs)} system logs")
        
        # Step 5: Verify data integrity
        print("\n🔍 Verifying data integrity...")
        
        # Check employee count
        sqlite_cursor.execute("SELECT COUNT(*) FROM employees")
        sqlite_employee_count = sqlite_cursor.fetchone()[0]
        
        sql_server_cursor.execute("SELECT COUNT(*) FROM employees")
        sql_server_employee_count = sql_server_cursor.fetchone()[0]
        
        print(f"Employees - SQLite: {sqlite_employee_count}, SQL Server: {sql_server_employee_count}")
        
        # Check time logs count
        sqlite_cursor.execute("SELECT COUNT(*) FROM time_logs")
        sqlite_time_count = sqlite_cursor.fetchone()[0]
        
        sql_server_cursor.execute("SELECT COUNT(*) FROM time_logs")
        sql_server_time_count = sql_server_cursor.fetchone()[0]
        
        print(f"Time logs - SQLite: {sqlite_time_count}, SQL Server: {sql_server_time_count}")
        
        # Check system logs count
        sqlite_cursor.execute("SELECT COUNT(*) FROM system_logs")
        sqlite_system_count = sqlite_cursor.fetchone()[0]
        
        sql_server_cursor.execute("SELECT COUNT(*) FROM system_logs")
        sql_server_system_count = sql_server_cursor.fetchone()[0]
        
        print(f"System logs - SQLite: {sqlite_system_count}, SQL Server: {sql_server_system_count}")
        
        # Verify relationships
        print("\n🔗 Verifying relationships...")
        
        # Check for orphaned time logs
        sql_server_cursor.execute("""
            SELECT COUNT(*) FROM time_logs tl
            LEFT JOIN employees e ON tl.employee_id = e.id
            WHERE e.id IS NULL
        """)
        orphaned_time_logs = sql_server_cursor.fetchone()[0]
        
        if orphaned_time_logs == 0:
            print("✅ All time logs have valid employee relationships")
        else:
            print(f"❌ Found {orphaned_time_logs} orphaned time logs")
        
        # Check for orphaned system logs
        sql_server_cursor.execute("""
            SELECT COUNT(*) FROM system_logs sl
            LEFT JOIN employees e ON sl.employee_id = e.id
            WHERE sl.employee_id IS NOT NULL AND e.id IS NULL
        """)
        orphaned_system_logs = sql_server_cursor.fetchone()[0]
        
        if orphaned_system_logs == 0:
            print("✅ All system logs have valid employee relationships")
        else:
            print(f"❌ Found {orphaned_system_logs} orphaned system logs")
        
        sqlite_conn.close()
        sql_server_conn.close()
        
        print("\n✅ Data fix completed successfully!")
        print("\n💡 Next steps:")
        print("1. Restart SQL Server integration: python sql_server_integration.py")
        print("2. Connect Power BI to SQL Server")
        print("3. Set up automatic refresh in Power BI Service")
        
    except Exception as e:
        print(f"❌ Error fixing data: {e}")

if __name__ == "__main__":
    fix_sql_server_data()




