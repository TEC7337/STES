#!/usr/bin/env python3
"""
Database Viewer for Smart Time Entry System (STES)
View employee data and time logs from the SQLite database
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def connect_to_database():
    """Connect to the STES database"""
    db_path = 'stes.db'
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found!")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        print(f"✅ Connected to database: {db_path}")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def view_employees(conn):
    """View all employees"""
    print("\n" + "="*60)
    print("👥 EMPLOYEES")
    print("="*60)
    
    query = """
    SELECT id, name, email, department, is_active, created_at 
    FROM employees 
    ORDER BY created_at DESC
    """
    
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        print(df.to_string(index=False))
        print(f"\nTotal employees: {len(df)}")
    else:
        print("No employees found.")

def view_time_logs(conn, limit=20):
    """View recent time logs"""
    print("\n" + "="*80)
    print("🕐 TIME LOGS (Most Recent)")
    print("="*80)
    
    query = """
    SELECT 
        tl.id,
        e.name as employee_name,
        e.department,
        tl.clock_in,
        tl.clock_out,
        tl.date,
        tl.duration_hours,
        tl.status,
        tl.created_at
    FROM time_logs tl
    JOIN employees e ON tl.employee_id = e.id
    ORDER BY tl.created_at DESC
    LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=[limit])
    if not df.empty:
        print(df.to_string(index=False))
        print(f"\nShowing {len(df)} most recent time logs")
    else:
        print("No time logs found.")

def view_todays_logs(conn):
    """View today's time logs"""
    print("\n" + "="*80)
    print("📅 TODAY'S TIME LOGS")
    print("="*80)
    
    today = datetime.now().date()
    
    query = """
    SELECT 
        tl.id,
        e.name as employee_name,
        e.department,
        tl.clock_in,
        tl.clock_out,
        tl.duration_hours,
        tl.status,
        tl.created_at
    FROM time_logs tl
    JOIN employees e ON tl.employee_id = e.id
    WHERE DATE(tl.date) = ?
    ORDER BY tl.created_at DESC
    """
    
    df = pd.read_sql_query(query, conn, params=[today])
    if not df.empty:
        print(df.to_string(index=False))
        print(f"\nToday's logs: {len(df)}")
    else:
        print("No time logs found for today.")

def view_employee_summary(conn, employee_name=None):
    """View summary for a specific employee"""
    if employee_name:
        print(f"\n" + "="*80)
        print(f"📊 SUMMARY FOR: {employee_name}")
        print("="*80)
        
        query = """
        SELECT 
            COUNT(*) as total_days,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_days,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_days,
            AVG(CASE WHEN duration_hours IS NOT NULL THEN CAST(duration_hours AS FLOAT) END) as avg_hours,
            SUM(CASE WHEN duration_hours IS NOT NULL THEN CAST(duration_hours AS FLOAT) END) as total_hours
        FROM time_logs tl
        JOIN employees e ON tl.employee_id = e.id
        WHERE e.name = ?
        """
        
        df = pd.read_sql_query(query, conn, params=[employee_name])
        if not df.empty:
            print(df.to_string(index=False))
        
        # Recent activity for this employee
        print(f"\n📋 RECENT ACTIVITY FOR {employee_name}:")
        query = """
        SELECT 
            tl.date,
            tl.clock_in,
            tl.clock_out,
            tl.duration_hours,
            tl.status
        FROM time_logs tl
        JOIN employees e ON tl.employee_id = e.id
        WHERE e.name = ?
        ORDER BY tl.date DESC, tl.created_at DESC
        LIMIT 10
        """
        
        df = pd.read_sql_query(query, conn, params=[employee_name])
        if not df.empty:
            print(df.to_string(index=False))
        else:
            print("No activity found for this employee.")

def view_system_logs(conn, limit=10):
    """View recent system logs"""
    print("\n" + "="*80)
    print("📝 SYSTEM LOGS (Most Recent)")
    print("="*80)
    
    query = """
    SELECT 
        sl.id,
        sl.event_type,
        sl.message,
        e.name as employee_name,
        sl.timestamp
    FROM system_logs sl
    LEFT JOIN employees e ON sl.employee_id = e.id
    ORDER BY sl.timestamp DESC
    LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=[limit])
    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("No system logs found.")

def export_to_csv(conn):
    """Export data to CSV files"""
    print("\n" + "="*60)
    print("📥 EXPORTING DATA TO CSV")
    print("="*60)
    
    # Export employees
    employees_df = pd.read_sql_query("SELECT * FROM employees", conn)
    employees_df.to_csv('employees_export.csv', index=False)
    print("✅ Exported employees to: employees_export.csv")
    
    # Export time logs
    time_logs_query = """
    SELECT 
        tl.id,
        e.name as employee_name,
        e.department,
        tl.clock_in,
        tl.clock_out,
        tl.date,
        tl.duration_hours,
        tl.status,
        tl.created_at
    FROM time_logs tl
    JOIN employees e ON tl.employee_id = e.id
    ORDER BY tl.created_at DESC
    """
    time_logs_df = pd.read_sql_query(time_logs_query, conn)
    time_logs_df.to_csv('time_logs_export.csv', index=False)
    print("✅ Exported time logs to: time_logs_export.csv")
    
    # Export system logs
    system_logs_df = pd.read_sql_query("SELECT * FROM system_logs", conn)
    system_logs_df.to_csv('system_logs_export.csv', index=False)
    print("✅ Exported system logs to: system_logs_export.csv")

def main():
    """Main function"""
    print("🗄️ STES Database Viewer")
    print("="*60)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # Show menu
        while True:
            print("\n📋 MENU:")
            print("1. View All Employees")
            print("2. View Recent Time Logs")
            print("3. View Today's Time Logs")
            print("4. View Employee Summary")
            print("5. View System Logs")
            print("6. Export Data to CSV")
            print("7. Custom SQL Query")
            print("8. Exit")
            
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                view_employees(conn)
            elif choice == '2':
                limit = input("Number of logs to show (default 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                view_time_logs(conn, limit)
            elif choice == '3':
                view_todays_logs(conn)
            elif choice == '4':
                employee_name = input("Enter employee name (e.g., 'Arnav Mehta'): ").strip()
                if employee_name:
                    view_employee_summary(conn, employee_name)
            elif choice == '5':
                limit = input("Number of logs to show (default 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                view_system_logs(conn, limit)
            elif choice == '6':
                export_to_csv(conn)
            elif choice == '7':
                query = input("Enter SQL query: ").strip()
                if query:
                    try:
                        df = pd.read_sql_query(query, conn)
                        print(df.to_string(index=False))
                    except Exception as e:
                        print(f"❌ Query error: {e}")
            elif choice == '8':
                break
            else:
                print("❌ Invalid choice. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        conn.close()
        print("✅ Database connection closed.")

if __name__ == "__main__":
    main() 