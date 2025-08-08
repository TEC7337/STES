#!/usr/bin/env python3
"""
Test Clock Out and SQL Server Sync
"""

import sqlite3
import pyodbc
import json
from datetime import datetime

def test_clock_out():
    """Test clock-out functionality and sync"""
    print("⏰ Testing Clock Out and SQL Server Sync")
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
        # Check current counts
        print("📊 Current Database Counts:")
        
        # SQLite counts
        sqlite_conn = sqlite3.connect('stes.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlite_cursor.execute("SELECT COUNT(*) FROM time_logs")
        sqlite_time_logs = sqlite_cursor.fetchone()[0]
        
        sqlite_cursor.execute("SELECT COUNT(*) FROM system_logs")
        sqlite_system_logs = sqlite_cursor.fetchone()[0]
        
        print(f"  SQLite: {sqlite_time_logs} time logs, {sqlite_system_logs} system logs")
        
        # SQL Server counts
        sql_server_conn = pyodbc.connect(conn_str)
        sql_server_cursor = sql_server_conn.cursor()
        
        sql_server_cursor.execute("SELECT COUNT(*) FROM time_logs")
        sql_server_time_logs = sql_server_cursor.fetchone()[0]
        
        sql_server_cursor.execute("SELECT COUNT(*) FROM system_logs")
        sql_server_system_logs = sql_server_cursor.fetchone()[0]
        
        print(f"  SQL Server: {sql_server_time_logs} time logs, {sql_server_system_logs} system logs")
        
        # Test clock-out for employee 1 (John Doe)
        print(f"\n⏰ Testing clock-out for Employee 1 (John Doe)...")
        
        # Add a test time log
        clock_in = datetime.now()
        clock_out = datetime.now()
        
        sqlite_cursor.execute("""
            INSERT INTO time_logs (employee_id, clock_in, clock_out, date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, clock_in, clock_out, clock_in.date(), 'completed', clock_in, clock_out))
        
        sqlite_conn.commit()
        
        # Get the new time log ID
        new_time_log_id = sqlite_cursor.lastrowid
        print(f"  ✅ Added time log ID {new_time_log_id} to SQLite")
        
        # Check SQLite count again
        sqlite_cursor.execute("SELECT COUNT(*) FROM time_logs")
        new_sqlite_time_logs = sqlite_cursor.fetchone()[0]
        print(f"  SQLite time logs: {sqlite_time_logs} → {new_sqlite_time_logs}")
        
        sqlite_conn.close()
        
        # Wait a moment for sync
        print(f"\n⏳ Waiting 15 seconds for SQL Server sync...")
        import time
        time.sleep(15)
        
        # Check SQL Server count
        sql_server_cursor.execute("SELECT COUNT(*) FROM time_logs")
        new_sql_server_time_logs = sql_server_cursor.fetchone()[0]
        print(f"  SQL Server time logs: {sql_server_time_logs} → {new_sql_server_time_logs}")
        
        if new_sql_server_time_logs > sql_server_time_logs:
            print("  ✅ Time log synced to SQL Server!")
        else:
            print("  ❌ Time log NOT synced to SQL Server")
        
        # Check if the specific time log exists in SQL Server
        sql_server_cursor.execute("SELECT id, employee_id, clock_in, clock_out FROM time_logs WHERE id = ?", (new_time_log_id,))
        result = sql_server_cursor.fetchone()
        
        if result:
            print(f"  ✅ Found time log {new_time_log_id} in SQL Server")
        else:
            print(f"  ❌ Time log {new_time_log_id} NOT found in SQL Server")
        
        sql_server_conn.close()
        
        print(f"\n💡 The SQL Server integration should detect the new time log and sync it automatically.")
        print(f"   If it doesn't sync, there might be an issue with the change detection logic.")
        
    except Exception as e:
        print(f"❌ Error testing clock-out: {e}")

if __name__ == "__main__":
    test_clock_out() 