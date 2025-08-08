#!/usr/bin/env python3
"""
Test Integrated SQL Server Sync
Tests the SQL Server integration that starts/stops with the STES system
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_integrated_sql_server():
    """Test the integrated SQL Server sync"""
    print("🧪 Testing Integrated SQL Server Sync")
    print("=" * 50)
    
    try:
        from utils.time_entry_manager import TimeEntryService
        
        # Initialize the service
        print("🔧 Initializing Time Entry Service...")
        service = TimeEntryService()
        
        # Start the service (this should start SQL Server sync)
        print("🚀 Starting Time Entry Service...")
        service.start_service()
        
        # Wait a moment for SQL Server sync to start
        import time
        time.sleep(3)
        
        # Test a clock-in/clock-out
        print("⏰ Testing clock-in/clock-out...")
        from utils.time_entry_manager import TimeEntryManager
        time_manager = TimeEntryManager()
        
        # Simulate a clock-in
        result = time_manager.process_clock_in("John Doe")
        print(f"📊 Clock-in result: {result.get('success', False)}")
        
        # Wait for sync
        print("⏳ Waiting 10 seconds for SQL Server sync...")
        time.sleep(10)
        
        # Check if data was synced
        print("🔍 Checking SQL Server data...")
        try:
            import json
            import pyodbc
            
            # Load SQL Server configuration
            with open('sql_server_config.json', 'r') as f:
                config = json.load(f)
            
            # Connect to SQL Server
            conn_str = (
                f"DRIVER={config['driver']};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['username']};"
                f"PWD={config['password']};"
                "Trusted_Connection=no;"
            )
            
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Check recent time logs
            cursor.execute("SELECT COUNT(*) FROM time_logs")
            time_log_count = cursor.fetchone()[0]
            print(f"📊 SQL Server time logs: {time_log_count}")
            
            # Get the latest time log
            cursor.execute("""
                SELECT TOP 1 
                    tl.id, 
                    e.name as employee_name,
                    tl.clock_in,
                    tl.status
                FROM time_logs tl
                LEFT JOIN employees e ON tl.employee_id = e.id
                ORDER BY tl.id DESC
            """)
            
            latest_log = cursor.fetchone()
            if latest_log:
                clock_in = latest_log[2].strftime('%H:%M:%S') if latest_log[2] else 'N/A'
                print(f"🕒 Latest time log: ID {latest_log[0]} - {latest_log[1]} at {clock_in}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error checking SQL Server: {e}")
        
        # Stop the service (this should stop SQL Server sync)
        print("⏹️ Stopping Time Entry Service...")
        service.stop_service()
        
        print("\n✅ Integrated SQL Server sync test completed!")
        print("\n💡 To use this in the STES system:")
        print("1. Open http://localhost:8501 in your browser")
        print("2. Click 'Start System' to start SQL Server sync")
        print("3. Use facial recognition to clock in/out")
        print("4. Click 'Stop System' to stop SQL Server sync")
        
    except Exception as e:
        print(f"❌ Error testing integrated SQL Server sync: {e}")

if __name__ == "__main__":
    test_integrated_sql_server()


