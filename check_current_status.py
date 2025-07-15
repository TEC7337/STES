import sqlite3

conn = sqlite3.connect('stes.db')
cursor = conn.cursor()

print("=== CURRENT STATUS FOR ARNAV ===")
cursor.execute('SELECT id, employee_id, clock_in, clock_out, status FROM time_logs WHERE employee_id = 9 AND DATE(date) = ?', ('2025-07-15',))
rows = cursor.fetchall()
for row in rows:
    print(f'ID: {row[0]}, Clock-in: {row[2]}, Clock-out: {row[3]}, Status: {row[4]}')

conn.close() 