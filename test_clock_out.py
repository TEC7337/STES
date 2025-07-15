#!/usr/bin/env python3
"""
Test Clock-out Flow
"""

import sys
sys.path.append('.')

from utils.time_entry_manager import TimeEntryManager
import time

def test_clock_out():
    """Test the clock-out flow"""
    print("🕐 Testing Clock-out Flow")
    print("=" * 50)
    
    # Initialize manager
    manager = TimeEntryManager()
    
    # Clear cooldown for testing
    manager.recent_recognitions = {}
    
    # Check current status
    print("\n1️⃣ Current Status:")
    status = manager.get_employee_status('Arnav Mehta')
    print(f"Status: {status['status']}")
    print(f"Message: {status['message']}")
    
    # Simulate clock-out
    print("\n2️⃣ Simulating Clock-out:")
    results = manager.handle_face_recognition(['Arnav Mehta'])
    if results:
        result = results[0]
        print(f"Success: {result['success']}")
        print(f"Action: {result['action']}")
        print(f"Message: {result['message']}")
        if 'duration_hours' in result:
            print(f"Duration: {result['duration_hours']} hours")
    else:
        print("No results returned")
    
    # Check final status
    print("\n3️⃣ Final Status:")
    status = manager.get_employee_status('Arnav Mehta')
    print(f"Status: {status['status']}")
    print(f"Message: {status['message']}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_clock_out() 