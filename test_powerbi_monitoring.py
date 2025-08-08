#!/usr/bin/env python3
"""
Test Power BI Monitoring
Manually triggers Power BI file updates to test if monitoring is working
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from real_time_powerbi_updater import RealTimePowerBIUpdater
    print("🔄 Testing Power BI Monitoring...")
    
    # Initialize Power BI updater
    updater = RealTimePowerBIUpdater()
    
    # Check current file timestamps
    time_logs_file = "powerbi_exports/time_logs.csv"
    if os.path.exists(time_logs_file):
        old_time = os.path.getmtime(time_logs_file)
        print(f"📄 Current time_logs.csv timestamp: {datetime.fromtimestamp(old_time)}")
    
    # Manually update Power BI files
    print("🔄 Manually updating Power BI files...")
    updater.update_powerbi_files()
    
    # Check new timestamps
    if os.path.exists(time_logs_file):
        new_time = os.path.getmtime(time_logs_file)
        print(f"📄 New time_logs.csv timestamp: {datetime.fromtimestamp(new_time)}")
        
        if new_time > old_time:
            print("✅ Power BI files updated successfully!")
        else:
            print("❌ Power BI files were not updated")
    
    print("\n💡 To enable automatic updates:")
    print("1. Open http://localhost:8501 in your browser")
    print("2. Click 'Start System' button")
    print("3. Power BI monitoring will start automatically")
    
except Exception as e:
    print(f"❌ Error testing Power BI monitoring: {e}")


