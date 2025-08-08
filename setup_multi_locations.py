#!/usr/bin/env python3
"""
Multi-Location Setup Script
Helps set up and test multiple STES locations
"""

import os
import sqlite3
import shutil
from datetime import datetime
import sys

class MultiLocationSetup:
    def __init__(self):
        self.locations = [
            {
                "id": 1,
                "name": "Main Office",
                "timezone": "America/New_York",
                "db_name": "stes_location_1.db"
            },
            {
                "id": 2,
                "name": "Branch Office", 
                "timezone": "America/Chicago",
                "db_name": "stes_location_2.db"
            },
            {
                "id": 3,
                "name": "West Coast Office",
                "timezone": "America/Los_Angeles", 
                "db_name": "stes_location_3.db"
            }
        ]
    
    def setup_location_database(self, location):
        """Set up database for a specific location"""
        print(f"🚀 Setting up database for Location {location['id']}: {location['name']}")
        
        # Create location-specific database
        db_path = location['db_name']
        
        if os.path.exists(db_path):
            print(f"   ⚠️  Database {db_path} already exists")
            return db_path
        
        # Copy existing database structure
        if os.path.exists('stes.db'):
            shutil.copy('stes.db', db_path)
            print(f"   ✅ Created {db_path} from existing database")
        else:
            # Create new database with proper schema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create tables (basic schema)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    department TEXT,
                    face_encoding TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    clock_in TIMESTAMP,
                    clock_out TIMESTAMP,
                    date DATE NOT NULL,
                    duration_hours TEXT,
                    status TEXT DEFAULT 'active',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    employee_id INTEGER,
                    message TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"   ✅ Created new database {db_path} with schema")
        
        return db_path
    
    def add_sample_data_to_location(self, location, db_path):
        """Add sample data specific to this location"""
        print(f"📊 Adding sample data for Location {location['id']}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add sample employees for this location
        sample_employees = [
            (f"Alice Johnson - {location['name']}", f"alice.{location['id']}@company.com", "Engineering"),
            (f"Bob Smith - {location['name']}", f"bob.{location['id']}@company.com", "Sales"),
            (f"Carol Davis - {location['name']}", f"carol.{location['id']}@company.com", "Marketing"),
            (f"David Wilson - {location['name']}", f"david.{location['id']}@company.com", "HR")
        ]
        
        for name, email, department in sample_employees:
            cursor.execute('''
                INSERT OR IGNORE INTO employees (name, email, department, face_encoding)
                VALUES (?, ?, ?, ?)
            ''', (name, email, department, "sample_encoding"))
        
        # Add sample time logs
        cursor.execute('SELECT id FROM employees LIMIT 2')
        employee_ids = [row[0] for row in cursor.fetchall()]
        
        for emp_id in employee_ids:
            cursor.execute('''
                INSERT INTO time_logs (employee_id, clock_in, date, status)
                VALUES (?, ?, ?, ?)
            ''', (emp_id, datetime.now(), datetime.now().date(), 'active'))
        
        conn.commit()
        conn.close()
        print(f"   ✅ Added sample data to {db_path}")
    
    def test_location_independently(self, location, db_path):
        """Test that a location can operate independently"""
        print(f"🧪 Testing Location {location['id']} independently")
        
        try:
            # Test database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test employee count
            cursor.execute('SELECT COUNT(*) FROM employees')
            employee_count = cursor.fetchone()[0]
            
            # Test time logs count
            cursor.execute('SELECT COUNT(*) FROM time_logs')
            time_logs_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"   ✅ Location {location['id']} test passed:")
            print(f"      - Employees: {employee_count}")
            print(f"      - Time logs: {time_logs_count}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Location {location['id']} test failed: {e}")
            return False
    
    def setup_all_locations(self):
        """Set up all locations"""
        print("🌍 Setting up Multi-Location STES")
        print("=" * 50)
        
        successful_locations = []
        
        for location in self.locations:
            print(f"\n📍 Processing Location {location['id']}: {location['name']}")
            
            # Set up database
            db_path = self.setup_location_database(location)
            
            # Add sample data
            self.add_sample_data_to_location(location, db_path)
            
            # Test location
            if self.test_location_independently(location, db_path):
                successful_locations.append(location)
        
        print(f"\n🎉 Setup complete! {len(successful_locations)} locations ready")
        return successful_locations
    
    def run_multi_location_export(self):
        """Run the multi-location export to aggregate data"""
        print("\n📊 Running multi-location export...")
        
        try:
            # Import and run the multi-location export
            from multi_location_export import MultiLocationExporter
            
            exporter = MultiLocationExporter()
            
            # Export each location
            for location in self.locations:
                db_path = location['db_name']
                if os.path.exists(db_path):
                    exporter.export_single_location(
                        location['id'],
                        location['name'], 
                        db_path
                    )
            
            # Aggregate all locations
            exporter.aggregate_all_locations()
            exporter.create_location_summary()
            
            print("✅ Multi-location export completed successfully!")
            
        except Exception as e:
            print(f"❌ Multi-location export failed: {e}")

def main():
    """Main function"""
    setup = MultiLocationSetup()
    
    print("🌍 STES Multi-Location Setup")
    print("=" * 50)
    print("This script will:")
    print("1. Create separate databases for each location")
    print("2. Add sample data to each location")
    print("3. Test each location independently")
    print("4. Run multi-location export")
    print("=" * 50)
    
    # Set up all locations
    successful_locations = setup.setup_all_locations()
    
    if successful_locations:
        # Run multi-location export
        setup.run_multi_location_export()
        
        print("\n🎯 Next Steps:")
        print("1. Each location now has its own database")
        print("2. Multi-location data has been exported to powerbi_exports/")
        print("3. You can now run 'python multi_location_export.py' anytime")
        print("4. Import the CSV files into Power BI for multi-location reporting")
        
    else:
        print("❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main() 