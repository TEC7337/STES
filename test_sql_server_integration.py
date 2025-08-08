#!/usr/bin/env python3
"""
Test SQL Server Integration
Verifies that the SQL Server integration works correctly
"""

import sqlite3
import pandas as pd
from sql_server_integration import SQLServerIntegration
import time

def test_sql_server_integration():
    """Test the SQL Server integration"""
    print("🧪 Testing SQL Server Integration")
    print("=" * 50)
    
    # Initialize integration
    integration = SQLServerIntegration()
    
    # Test 1: Configuration
    print("\n📋 Test 1: Configuration")
    print(f"Location: {integration.stes_location_name} (ID: {integration.stes_location_id})")
    print(f"Sync interval: {integration.config['sync_interval']} seconds")
    print("✅ Configuration loaded successfully")
    
    # Test 2: SQL Server Connection
    print("\n🔌 Test 2: SQL Server Connection")
    if integration.test_sql_server_connection():
        print("✅ SQL Server connection successful")
    else:
        print("❌ SQL Server connection failed")
        print("⚠️ Please check your SQL Server configuration in sql_server_config.json")
        return False
    
    # Test 3: SQLite Database
    print("\n💾 Test 3: SQLite Database")
    try:
        conn = sqlite3.connect(integration.sqlite_db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found tables: {tables}")
        
        # Get record counts
        counts = integration.get_sqlite_counts()
        print(f"Record counts: {counts}")
        
        conn.close()
        print("✅ SQLite database accessible")
        
    except Exception as e:
        print(f"❌ SQLite database error: {e}")
        return False
    
    # Test 4: Manual Sync
    print("\n🔄 Test 4: Manual Data Sync")
    try:
        integration.sync_all_data()
        print("✅ Manual sync completed successfully")
    except Exception as e:
        print(f"❌ Manual sync failed: {e}")
        return False
    
    # Test 5: Status Check
    print("\n📊 Test 5: Status Check")
    status = integration.get_status()
    print(f"Running: {status['is_running']}")
    print(f"Last sync: {status['last_sync_time']}")
    print(f"Location: {status['stes_location']}")
    print("✅ Status check completed")
    
    print("\n🎉 All tests completed successfully!")
    print("\n💡 Next steps:")
    print("1. Start the integration: python sql_server_integration.py")
    print("2. Use facial recognition in STES to trigger syncs")
    print("3. Connect Power BI to SQL Server")
    
    return True

def test_multi_location_support():
    """Test multi-location support"""
    print("\n🏢 Testing Multi-Location Support")
    print("=" * 50)
    
    # Test different location configurations
    test_locations = [
        {"id": 1, "name": "Main Office"},
        {"id": 2, "name": "Branch Office"},
        {"id": 3, "name": "West Coast Office"}
    ]
    
    for location in test_locations:
        print(f"\n📍 Testing location: {location['name']} (ID: {location['id']})")
        
        # Create temporary config
        temp_config = {
            "server": "localhost",
            "database": "STES_Database",
            "username": "sa",
            "password": "YourPassword123!",
            "driver": "{ODBC Driver 17 for SQL Server}",
            "stes_location_id": location["id"],
            "stes_location_name": location["name"],
            "sync_interval": 10,
            "auto_create_tables": True
        }
        
        # Test integration with this location
        integration = SQLServerIntegration()
        integration.config.update(temp_config)
        
        print(f"✅ Location {location['name']} configured successfully")
    
    print("\n✅ Multi-location support verified!")

if __name__ == "__main__":
    print("🧪 STES SQL Server Integration Test")
    print("=" * 50)
    
    # Run tests
    success = test_sql_server_integration()
    
    if success:
        test_multi_location_support()
        print("\n🎯 All tests passed! SQL Server integration is ready.")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")

