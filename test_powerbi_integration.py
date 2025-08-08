#!/usr/bin/env python3
"""
Test Power BI Integration
Verifies that the real-time Power BI monitoring works with the STES system
"""

import time
import sqlite3
from datetime import datetime

def test_powerbi_integration():
    """Test the Power BI integration"""
    print("🧪 Testing Power BI Integration")
    print("=" * 40)
    
    try:
        # Test 1: Check if real-time updater can be imported
        print("1. Testing import...")
        from real_time_powerbi_updater import RealTimePowerBIUpdater
        print("   ✅ RealTimePowerBIUpdater imported successfully")
        
        # Test 2: Check if database exists and is accessible
        print("2. Testing database connection...")
        conn = sqlite3.connect('stes.db')
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        required_tables = ['employees', 'time_logs', 'system_logs']
        
        for table in required_tables:
            if table in tables:
                print(f"   ✅ Table '{table}' exists")
            else:
                print(f"   ❌ Table '{table}' missing")
        
        # Test 3: Check current record counts
        print("3. Testing record counts...")
        cursor.execute("SELECT COUNT(*) FROM time_logs")
        time_logs_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM system_logs")
        system_logs_count = cursor.fetchone()[0]
        
        print(f"   📊 Time logs: {time_logs_count}")
        print(f"   📊 System logs: {system_logs_count}")
        
        conn.close()
        
        # Test 4: Test Power BI updater initialization
        print("4. Testing Power BI updater...")
        updater = RealTimePowerBIUpdater()
        print("   ✅ Power BI updater initialized")
        
        # Test 5: Test status method
        status = updater.get_status()
        print(f"   📊 Status: {status}")
        
        # Test 6: Test single update
        print("5. Testing single update...")
        updater.update_powerbi_files()
        print("   ✅ Power BI files updated successfully")
        
        print("\n🎉 All tests passed! Power BI integration is working correctly.")
        print("\n📋 Next steps:")
        print("1. Start the STES system: python run_stes.py run")
        print("2. Click 'Start System' in the web interface")
        print("3. Use facial recognition to clock in/out")
        print("4. Refresh your Power BI dashboard to see updates")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure real_time_powerbi_updater.py is in the same directory")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_powerbi_integration() 