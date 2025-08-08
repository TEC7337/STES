#!/usr/bin/env python3
"""
STES Power BI Export Script
Exports SQLite database tables to CSV files for Power BI import
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def export_for_powerbi():
    """Export STES database tables to CSV files for Power BI"""
    
    print("🚀 Starting STES Power BI Export...")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('stes.db')
        print("✅ Connected to stes.db")
        
        # Export each table
        print("📊 Exporting tables...")
        
        # Employees table
        employees_df = pd.read_sql_query("SELECT * FROM employees", conn)
        print(f"   - employees: {len(employees_df)} records")
        
        # Time logs table
        time_logs_df = pd.read_sql_query("SELECT * FROM time_logs", conn)
        print(f"   - time_logs: {len(time_logs_df)} records")
        
        # System logs table
        system_logs_df = pd.read_sql_query("SELECT * FROM system_logs", conn)
        print(f"   - system_logs: {len(system_logs_df)} records")
        
        # Create exports directory
        export_dir = 'powerbi_exports'
        os.makedirs(export_dir, exist_ok=True)
        
        # Export to CSV with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        employees_file = f'{export_dir}/employees_{timestamp}.csv'
        time_logs_file = f'{export_dir}/time_logs_{timestamp}.csv'
        system_logs_file = f'{export_dir}/system_logs_{timestamp}.csv'
        
        employees_df.to_csv(employees_file, index=False)
        time_logs_df.to_csv(time_logs_file, index=False)
        system_logs_df.to_csv(system_logs_file, index=False)
        
        # Also create latest versions (without timestamp)
        employees_df.to_csv(f'{export_dir}/employees.csv', index=False)
        time_logs_df.to_csv(f'{export_dir}/time_logs.csv', index=False)
        system_logs_df.to_csv(f'{export_dir}/system_logs.csv', index=False)
        
        print(f"\n✅ Export completed successfully!")
        print(f"📁 Files saved in: {export_dir}/")
        print(f"   - employees.csv ({len(employees_df)} records)")
        print(f"   - time_logs.csv ({len(time_logs_df)} records)")
        print(f"   - system_logs.csv ({len(system_logs_df)} records)")
        print(f"\n🎯 Next steps:")
        print(f"   1. Open Power BI Desktop")
        print(f"   2. Click 'Get Data' → 'Text/CSV'")
        print(f"   3. Browse to {export_dir}/ folder")
        print(f"   4. Import each CSV file")
        print(f"   5. Create relationships between tables")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def create_sample_queries():
    """Create sample Power BI queries for reference"""
    
    queries = {
        "real_time_status": """
        SELECT 
            e.id,
            e.name,
            e.department,
            CASE 
                WHEN tl.clock_out IS NULL AND tl.clock_in IS NOT NULL THEN 'Clocked In'
                WHEN tl.clock_out IS NOT NULL THEN 'Clocked Out'
                ELSE 'Not Present'
            END as status,
            tl.clock_in,
            tl.clock_out,
            tl.date
        FROM employees e
        LEFT JOIN time_logs tl ON e.id = tl.employee_id AND tl.date = DATE('now')
        WHERE e.is_active = 1
        """,
        
        "daily_attendance": """
        SELECT 
            e.department,
            COUNT(DISTINCT e.id) as total_employees,
            COUNT(CASE WHEN tl.clock_in IS NOT NULL THEN 1 END) as clocked_in,
            COUNT(CASE WHEN tl.clock_out IS NOT NULL THEN 1 END) as clocked_out,
            ROUND((COUNT(CASE WHEN tl.clock_in IS NOT NULL THEN 1 END) * 100.0 / COUNT(DISTINCT e.id)), 2) as attendance_rate
        FROM employees e
        LEFT JOIN time_logs tl ON e.id = tl.employee_id AND tl.date = DATE('now')
        WHERE e.is_active = 1
        GROUP BY e.department
        """,
        
        "work_hours": """
        SELECT 
            e.name,
            e.department,
            tl.date,
            tl.clock_in,
            tl.clock_out,
            CAST((julianday(tl.clock_out) - julianday(tl.clock_in)) * 24 AS DECIMAL(4,2)) as hours_worked
        FROM employees e
        JOIN time_logs tl ON e.id = tl.employee_id
        WHERE tl.clock_out IS NOT NULL
        AND tl.date >= DATE('now', '-30 days')
        """
    }
    
    # Save queries to file
    with open('powerbi_exports/sample_queries.txt', 'w') as f:
        f.write("Power BI Sample Queries for STES\n")
        f.write("=" * 40 + "\n\n")
        
        for name, query in queries.items():
            f.write(f"{name.upper().replace('_', ' ')}:\n")
            f.write(query.strip())
            f.write("\n\n" + "-" * 40 + "\n\n")
    
    print("📝 Sample queries saved to: powerbi_exports/sample_queries.txt")

if __name__ == "__main__":
    export_for_powerbi()
    create_sample_queries() 