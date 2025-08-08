import sqlite3
from datetime import datetime

conn = sqlite3.connect('stes.db')
cursor = conn.cursor()

print("=== TODAY'S RECORDS FOR ARNAV (ID 9) ===")
cursor.execute('SELECT id, employee_id, clock_in, clock_out, status FROM time_logs WHERE employee_id = 9 AND DATE(date) = ?', ('2025-07-15',))
rows = cursor.fetchall()
for row in rows:
    print(f'ID: {row[0]}, Employee: {row[1]}, Clock-in: {row[2]}, Clock-out: {row[3]}, Status: {row[4]}')

print("\n=== TESTING TimeEntryManager ===")
import sys
sys.path.append('.')
from utils.time_entry_manager import TimeEntryManager

manager = TimeEntryManager()
status = manager.get_employee_status('Arnav Mehta')
print(f"Employee status: {status}")

conn.close() 