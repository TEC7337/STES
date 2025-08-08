#!/usr/bin/env python3
"""
Test New Employee Sync
Tests that new employees are automatically synced to SQL Server
"""

import sqlite3
import pyodbc
import json
from datetime import datetime

def test_new_employee_sync():
    """Test that new employees are synced to SQL Server"""
    print("🧪 Test New Employee Sync")
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
        
        # Check current counts
        print("\n📊 Current Database Counts:")
        
        # SQLite counts
        sqlite_cursor.execute("SELECT COUNT(*) FROM employees")
        sqlite_employees = sqlite_cursor.fetchone()[0]
        
        sqlite_cursor.execute("SELECT COUNT(*) FROM time_logs")
        sqlite_time_logs = sqlite_cursor.fetchone()[0]
        
        sqlite_cursor.execute("SELECT COUNT(*) FROM system_logs")
        sqlite_system_logs = sqlite_cursor.fetchone()[0]
        
        print(f"   SQLite: {sqlite_employees} employees, {sqlite_time_logs} time logs, {sqlite_system_logs} system logs")
        
        # SQL Server counts
        sql_server_cursor.execute("SELECT COUNT(*) FROM employees")
        sql_server_employees = sql_server_cursor.fetchone()[0]
        
        sql_server_cursor.execute("SELECT COUNT(*) FROM time_logs")
        sql_server_time_logs = sql_server_cursor.fetchone()[0]
        
        sql_server_cursor.execute("SELECT COUNT(*) FROM system_logs")
        sql_server_system_logs = sql_server_cursor.fetchone()[0]
        
        print(f"   SQL Server: {sql_server_employees} employees, {sql_server_time_logs} time logs, {sql_server_system_logs} system logs")
        
        # Check if counts match
        if (sqlite_employees == sql_server_employees and 
            sqlite_time_logs == sql_server_time_logs and 
            sqlite_system_logs == sql_server_system_logs):
            print("✅ All counts match! SQL Server is in sync with SQLite.")
        else:
            print("❌ Counts don't match. SQL Server needs to be synced.")
        
        # Check recent employees
        print("\n👥 Recent Employees:")
        sqlite_cursor.execute("""
            SELECT id, name, department, created_at 
            FROM employees 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_employees = sqlite_cursor.fetchall()
        
        for emp_id, name, dept, created_at in recent_employees:
            print(f"   {emp_id}: {name} ({dept}) - {created_at}")
        
        # Check if SQL Server integration is running
        print("\n🔄 SQL Server Integration Status:")
        try:
            import psutil
            sql_server_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower() and proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'sql_server_integration.py' in cmdline:
                            sql_server_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if sql_server_processes:
                print("✅ SQL Server integration is running:")
                for proc in sql_server_processes:
                    print(f"   PID {proc['pid']}: {' '.join(proc['cmdline'])}")
            else:
                print("❌ SQL Server integration is NOT running")
                print("💡 Start it with: python sql_server_integration.py")
        except ImportError:
            print("⚠️ psutil not available, cannot check running processes")
        
        # Test manual sync
        print("\n🔄 Testing Manual Sync:")
        try:
            from sql_server_integration import SQLServerIntegration
            integration = SQLServerIntegration()
            integration.sync_all_data()
            print("✅ Manual sync completed successfully")
        except Exception as e:
            print(f"❌ Manual sync failed: {e}")
        
        sqlite_conn.close()
        sql_server_conn.close()
        
        print("\n✅ Test completed!")
        print("\n💡 To test automatic sync:")
        print("1. Register a new employee using the STES system")
        print("2. Wait a few seconds for the sync to complete")
        print("3. Check SQL Server to see if the new employee appears")
        
    except Exception as e:
        print(f"❌ Error testing sync: {e}")

if __name__ == "__main__":
    test_new_employee_sync()




