#!/usr/bin/env python3
"""
Multi-Location STES Export Script
Exports and aggregates data from multiple locations for Power BI
"""

import sqlite3
import pandas as pd
import os
import glob
from datetime import datetime
import json

class MultiLocationExporter:
    def __init__(self, base_directory="."):
        self.base_directory = base_directory
        self.export_dir = os.path.join(base_directory, 'powerbi_exports')
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_single_location(self, location_id: int, location_name: str, db_path: str):
        """Export data for a single location"""
        print(f"🚀 Exporting data for Location {location_id}: {location_name}")
        
        try:
            # Connect to location's SQLite database
            conn = sqlite3.connect(db_path)
            
            # Export each table with location information
            tables = ['employees', 'time_logs', 'system_logs']
            
            for table in tables:
                # Read data from SQLite
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                
                if not df.empty:
                    # Add location information
                    df['location_id'] = location_id
                    df['location_name'] = location_name
                    df['export_timestamp'] = datetime.now().isoformat()
                    
                    # Save with location prefix
                    filename = f'location_{location_id:02d}_{table}.csv'
                    filepath = os.path.join(self.export_dir, filename)
                    df.to_csv(filepath, index=False)
                    
                    print(f"   ✅ {table}: {len(df)} records → {filename}")
                else:
                    print(f"   ⚠️  {table}: No data found")
            
            conn.close()
            print(f"✅ Location {location_id} export completed")
            
        except Exception as e:
            print(f"❌ Error exporting Location {location_id}: {e}")
    
    def aggregate_all_locations(self):
        """Combine data from all locations into single files"""
        print("🔄 Aggregating data from all locations...")
        
        # Find all location CSV files
        location_files = glob.glob(os.path.join(self.export_dir, 'location_*_*.csv'))
        
        if not location_files:
            print("❌ No location files found. Run export_single_location first.")
            return
        
        # Group files by table type
        table_groups = {}
        for file in location_files:
            filename = os.path.basename(file)
            parts = filename.split('_')
            if len(parts) >= 3:
                table_name = '_'.join(parts[2:]).replace('.csv', '')
                if table_name not in table_groups:
                    table_groups[table_name] = []
                table_groups[table_name].append(file)
        
        # Combine each table type
        for table_name, files in table_groups.items():
            print(f"📊 Combining {table_name} from {len(files)} locations...")
            
            all_data = []
            for file in files:
                df = pd.read_csv(file)
                all_data.append(df)
            
            if all_data:
                # Combine all dataframes
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # Save combined file
                combined_filename = f'all_locations_{table_name}.csv'
                combined_filepath = os.path.join(self.export_dir, combined_filename)
                combined_df.to_csv(combined_filepath, index=False)
                
                print(f"   ✅ Combined {len(combined_df)} records → {combined_filename}")
        
        print("✅ Multi-location aggregation completed")
    
    def create_location_summary(self):
        """Create a summary of all locations"""
        print("📋 Creating location summary...")
        
        summary_data = []
        location_files = glob.glob(os.path.join(self.export_dir, 'location_*_employees.csv'))
        
        for file in location_files:
            filename = os.path.basename(file)
            parts = filename.split('_')
            if len(parts) >= 3:
                location_id = int(parts[1])
                
                # Read employees to get location info
                df = pd.read_csv(file)
                if not df.empty:
                    location_name = df['location_name'].iloc[0]
                    employee_count = len(df)
                    
                    summary_data.append({
                        'location_id': location_id,
                        'location_name': location_name,
                        'employee_count': employee_count,
                        'export_file': filename
                    })
        
        # Save summary
        summary_df = pd.DataFrame(summary_data)
        summary_file = os.path.join(self.export_dir, 'locations_summary.csv')
        summary_df.to_csv(summary_file, index=False)
        
        print(f"✅ Location summary saved: {len(summary_data)} locations")
        return summary_df
    
    def export_sample_locations(self):
        """Export sample data for demonstration"""
        print("🎯 Creating sample multi-location data...")
        
        # Sample location configurations
        sample_locations = [
            {"id": 1, "name": "Main Office", "db_path": "stes.db"},
            {"id": 2, "name": "Branch Office", "db_path": "stes.db"},  # Using same DB for demo
            {"id": 3, "name": "West Coast Office", "db_path": "stes.db"}
        ]
        
        for location in sample_locations:
            self.export_single_location(
                location["id"], 
                location["name"], 
                location["db_path"]
            )
        
        # Aggregate all locations
        self.aggregate_all_locations()
        
        # Create summary
        summary = self.create_location_summary()
        
        print("\n🎉 Sample multi-location export completed!")
        print("📁 Files created in powerbi_exports/")
        print("📊 Summary:")
        for _, row in summary.iterrows():
            print(f"   - Location {row['location_id']}: {row['location_name']} ({row['employee_count']} employees)")

def main():
    """Main function for multi-location export"""
    exporter = MultiLocationExporter()
    
    print("🌍 STES Multi-Location Export Tool")
    print("=" * 50)
    
    # For demonstration, create sample multi-location data
    exporter.export_sample_locations()
    
    print("\n🎯 Next steps for Power BI:")
    print("1. Open Power BI Desktop")
    print("2. Click 'Get Data' → 'Text/CSV'")
    print("3. Import these files:")
    print("   - all_locations_employees.csv")
    print("   - all_locations_time_logs.csv")
    print("   - all_locations_system_logs.csv")
    print("4. Create relationships between tables")
    print("5. Use 'location_name' field for location-based filtering")

if __name__ == "__main__":
    main() 