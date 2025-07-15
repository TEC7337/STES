#!/usr/bin/env python3
"""
Test Face Recognition Flow
"""

import sys
sys.path.append('.')

from utils.time_entry_manager import TimeEntryManager

def test_face_recognition():
    """Test the complete face recognition flow"""
    print("🧪 Testing Face Recognition Flow")
    print("=" * 50)
    
    # Initialize manager
    manager = TimeEntryManager()
    
    # Clear any existing cooldown
    manager.recent_recognitions = {}
    
    # Test 1: Check initial status
    print("\n1️⃣ Initial Status Check:")
    status = manager.get_employee_status('Arnav Mehta')
    print(f"Status: {status['status']}")
    print(f"Message: {status['message']}")
    
    # Test 2: Simulate face recognition (clock-in)
    print("\n2️⃣ Simulating Face Recognition (Clock-in):")
    results = manager.handle_face_recognition(['Arnav Mehta'])
    if results:
        result = results[0]
        print(f"Success: {result['success']}")
        print(f"Action: {result['action']}")
        print(f"Message: {result['message']}")
    else:
        print("No results returned")
    
    # Test 3: Check status after clock-in
    print("\n3️⃣ Status After Clock-in:")
    status = manager.get_employee_status('Arnav Mehta')
    print(f"Status: {status['status']}")
    print(f"Message: {status['message']}")
    
    # Test 4: Simulate second face recognition (clock-out)
    print("\n4️⃣ Simulating Face Recognition (Clock-out):")
    # Clear cooldown for testing
    manager.recent_recognitions = {}
    results = manager.handle_face_recognition(['Arnav Mehta'])
    if results:
        result = results[0]
        print(f"Success: {result['success']}")
        print(f"Action: {result['action']}")
        print(f"Message: {result['message']}")
    else:
        print("No results returned")
    
    # Test 5: Final status check
    print("\n5️⃣ Final Status:")
    status = manager.get_employee_status('Arnav Mehta')
    print(f"Status: {status['status']}")
    print(f"Message: {status['message']}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_face_recognition() 