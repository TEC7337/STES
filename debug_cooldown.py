#!/usr/bin/env python3
"""
Debug Cooldown Issue
"""

import sys
sys.path.append('.')

from utils.time_entry_manager import TimeEntryManager
from datetime import datetime

def debug_cooldown():
    """Debug the cooldown logic"""
    print("🐛 Debugging Cooldown Issue")
    print("=" * 50)
    
    # Initialize manager
    manager = TimeEntryManager()
    
    print(f"Cooldown minutes: {manager.config.COOLDOWN_MINUTES}")
    print(f"Recent recognitions: {manager.recent_recognitions}")
    
    # Check if Arnav is in cooldown
    is_cooldown = manager.is_within_cooldown('Arnav Mehta')
    print(f"Is Arnav in cooldown? {is_cooldown}")
    
    # Check the actual status
    status = manager.get_employee_status('Arnav Mehta')
    print(f"Employee status: {status}")
    
    # Clear cooldown and try again
    print("\n--- Clearing cooldown ---")
    manager.recent_recognitions = {}
    
    is_cooldown = manager.is_within_cooldown('Arnav Mehta')
    print(f"Is Arnav in cooldown after clearing? {is_cooldown}")
    
    # Try the handle_face_recognition method step by step
    print("\n--- Testing handle_face_recognition ---")
    
    # Check if name is unknown
    name = 'Arnav Mehta'
    if name == "Unknown":
        print("Name is Unknown - would skip")
    else:
        print(f"Name is: {name}")
    
    # Check cooldown in handle_face_recognition
    if manager.is_within_cooldown(name):
        print(f"❌ {name} is in cooldown - would skip")
    else:
        print(f"✅ {name} is NOT in cooldown - would process")
        
        # Get employee status
        employee_status = manager.get_employee_status(name)
        print(f"Employee status in handle_face_recognition: {employee_status}")

if __name__ == "__main__":
    debug_cooldown() 