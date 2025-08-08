#!/usr/bin/env python3
"""
Test Power BI SQL Server Connection
Verifies that Power BI can connect to SQL Server and see the latest data
"""

import json
import pyodbc
import pandas as pd
from datetime import datetime

def test_powerbi_sql_server_connection():
    """Test Power BI connection to SQL Server"""
    print("🔍 Testing Power BI SQL Server Connection")
    print("=" * 50)
    
    try:
        # Load SQL Server configuration
        with open('sql_server_config.json', 'r') as f:
            config = json.load(f)
        
        # Create connection string
        conn_str = (
            f"DRIVER={config['driver']};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"PWD={config['password']};"
            "Trusted_Connection=no;"
        )
        
        # Connect to SQL Server
        print("🔌 Connecting to SQL Server...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to SQL Server: {version.split()[0]} {version.split()[1]}")
        
        # Check table counts
        print("\n📊 Current Data Counts:")
        cursor.execute("SELECT COUNT(*) FROM employees")
        employee_count = cursor.fetchone()[0]
        print(f"   Employees: {employee_count}")
        
        cursor.execute("SELECT COUNT(*) FROM time_logs")
        time_log_count = cursor.fetchone()[0]
        print(f"   Time Logs: {time_log_count}")
        
        cursor.execute("SELECT COUNT(*) FROM system_logs")
        system_log_count = cursor.fetchone()[0]
        print(f"   System Logs: {system_log_count}")
        
        # Check recent time logs
        print("\n🕒 Recent Time Logs (Last 5):")
        cursor.execute("""
            SELECT TOP 5 
                tl.id, 
                e.name as employee_name,
                tl.clock_in,
                tl.clock_out,
                tl.status
            FROM time_logs tl
            LEFT JOIN employees e ON tl.employee_id = e.id
            ORDER BY tl.id DESC
        """)
        
        recent_logs = cursor.fetchall()
        for log in recent_logs:
            clock_in = log[2].strftime('%H:%M:%S') if log[2] else 'N/A'
            clock_out = log[3].strftime('%H:%M:%S') if log[3] else 'N/A'
            print(f"   ID {log[0]}: {log[1]} - {clock_in} to {clock_out} ({log[4]})")
        
        # Check location distribution
        print("\n📍 Location Distribution:")
        cursor.execute("""
            SELECT 
                stes_location_name,
                COUNT(*) as employee_count
            FROM employees
            GROUP BY stes_location_name
            ORDER BY employee_count DESC
        """)
        
        locations = cursor.fetchall()
        for location in locations:
            print(f"   {location[0]}: {location[1]} employees")
        
        conn.close()
        
        print("\n✅ SQL Server connection test successful!")
        print("\n💡 Power BI Connection Instructions:")
        print("1. Open Power BI Desktop")
        print("2. Click 'Get Data' → 'SQL Server'")
        print("3. Enter server: " + config['server'])
        print("4. Enter database: " + config['database'])
        print("5. Use SQL Server authentication")
        print("6. Username: " + config['username'])
        print("7. Import the following tables:")
        print("   - employees")
        print("   - time_logs") 
        print("   - system_logs")
        print("8. Set up automatic refresh in Power BI Service")
        
    except Exception as e:
        print(f"❌ Error testing SQL Server connection: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Check if SQL Server is running")
        print("2. Verify connection details in sql_server_config.json")
        print("3. Ensure SQL Server authentication is enabled")
        print("4. Check if the database exists")

if __name__ == "__main__":
    test_powerbi_sql_server_connection()

