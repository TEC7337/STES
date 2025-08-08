# 🚀 Getting Started with STES

Welcome to the Smart Time Entry System (STES)!

## 📋 Prerequisites

- **Python 3.8+** installed on your system
- **Webcam** (built-in or external USB camera)
- **Windows 10/11** (the system is optimized for Windows)

## 🔧 Quick Setup (Recommended)

The easiest way to get started is using our automated setup script:

### Step 1: Install Dependencies
```bash
python run_stes.py install
```

### Step 2: Setup the System
```bash
python run_stes.py setup
```

### Step 3: Run the Application
```bash
python run_stes.py run
```

That's it! Your browser should open automatically to `http://localhost:8501`

## 📖 Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
python db/setup_database.py --sample-data
```

### 3. Create Sample Data
```bash
python utils/create_sample_data.py
```

### 4. Run Streamlit App
```bash
streamlit run ui/main.py
```

## Setting up Power BI Dashboards with CSV Files (Single Location)
-Create a Power BI Dashboard (depending on how you want the visualizations)
-Import data -> CSV file
-Import all_locations_employees_fixed.csv, all_locations_system_logs_fixed.csv, all_locations_time_logs_fixed.csv
-Should be good to go, just hit refresh whenever an update is needed on the dashboard

## Setting up Power BI Dashboards with SQL Server (Multi-Locational if built upon)
### **Step 1: Install Prerequisites**
```bash
# Install SQL Server (Express, Standard, or Enterprise)
# Install ODBC Driver 17 for SQL Server
# Install Python dependency
pip install pyodbc>=4.0.39
```

### **Step 2: Configure SQL Server**
```sql
-- Create database
CREATE DATABASE STES_Database;
GO

-- Create user and permissions
CREATE LOGIN STES_User WITH PASSWORD = 'YourSecurePassword123!';
CREATE USER STES_User FOR LOGIN STES_User;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO STES_User;
GRANT CREATE TABLE TO STES_User;
```

### **Step 3: Update Configuration**
Edit `sql_server_config.json`:
```json
{
  "server": "your-sql-server-address",
  "database": "STES_Database",
  "username": "STES_User",
  "password": "YourSecurePassword123!",
  "driver": "{ODBC Driver 17 for SQL Server}",
  "stes_location_id": 1,
  "stes_location_name": "Main Office",
  "sync_interval": 10,
  "auto_create_tables": true
}
```

### **Step 4: Test Integration**
```bash
python test_sql_server_integration.py
```

### **Step 5: Start Integration**
```bash
python sql_server_integration.py
```

## 👥 Adding Real Employees

To register real employees (instead of using mock data):

```bash
python utils/register_employee.py --interactive
```

The interactive mode will prompt you for:
- Employee name
- Email (optional)
- Department (optional)
- **Location selection** (1=Main Office, 2=Branch Office, 3=West Coast Office)

Or register from command line:
```bash
# Using camera
python utils/register_employee.py --name "John Doe" --email "john@nsight.com" --department "Engineering" --location 2 --camera

# Using image file
python utils/register_employee.py --name "Jane Smith" --image "path/to/photo.jpg" --email "jane@nsight.com" --location 1
```

### 📍 Available Locations
- **Location 1**: Main Office
- **Location 2**: Branch Office  
- **Location 3**: West Coast Office

## 🎯 Using the System

### Web Interface Features

1. **🏠 Home Page**
   - Start/Stop the face recognition system
   - Live video feed with face detection
   - Real-time recognition results
   - System status monitoring

2. **📅 Daily Summary**
   - View time logs by date
   - Employee attendance statistics
   - Export data to CSV

3. **👥 Employee Management**
   - View all registered employees
   - Employee statistics by department
   - Registration instructions

4. **⚙️ System Logs**
   - Monitor system events
   - Filter logs by event type
   - Troubleshooting information

### Face Recognition Flow

1. **System Startup**: Loads known employee face encodings
2. **Face Detection**: Continuously scans webcam for faces
3. **Recognition**: Compares detected faces with known employees
4. **Time Logging**: 
   - First recognition of the day → **Clock In**
   - Next recognition after cooldown → **Clock Out**
5. **Database Storage**: All entries saved with timestamps

## ⚙️ Configuration

Key settings in `config/config.py`:

- **COOLDOWN_MINUTES**: Prevent duplicate entries (default: 10 minutes)
- **FACE_RECOGNITION_TOLERANCE**: Face matching sensitivity (default: 0.6)
- **CAMERA_INDEX**: Which camera to use (default: 0)
- **DATABASE_URL**: Database connection string

## 🔍 System Status

Check if everything is working:
```bash
python run_stes.py status
```

## 📊 Demo Data

The system comes with 5 sample employees:
- Alice Johnson (Engineering)
- Bob Smith (Data Science)  
- Carol Davis (Product Management)
- David Wilson (Engineering)
- Emma Brown (Marketing)

Each has mock face encodings and sample time logs for the past week.

## 🎥 Presentation Tips

For your Nsight demo:

1. **Start with Status Check**: Show the system is properly configured
2. **Demo Face Recognition**: Use the sample employees or register yourself
3. **Show Reports**: Display daily summaries and employee statistics
4. **Highlight Features**: Real-time detection, cooldown prevention, data export

## 📱 Camera Setup

- **Position**: Place camera at eye level, well-lit area
- **Distance**: Sit 2-3 feet from the camera
- **Lighting**: Avoid backlighting, use natural or soft lighting
- **Background**: Plain background works best

## 🚨 Troubleshooting

### Camera Issues
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

### Face Recognition Issues
- Ensure good lighting
- Face the camera directly
- Remove glasses/masks if needed
- Check face recognition tolerance settings

### Database Issues
```bash
# Reset database
python db/setup_database.py --reset --sample-data
```

### Package Issues
```bash
# Reinstall all packages
pip install --force-reinstall -r requirements.txt
```

## 🎯 Key Technologies Demonstrated

- **Computer Vision**: OpenCV for video processing
- **Face Recognition**: dlib-based face encoding and matching
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL
- **Web Framework**: Streamlit for modern UI
- **Data Analysis**: pandas for time tracking analytics
- **Real-time Processing**: Live video stream analysis

## 📈 Future Enhancements

Potential additions for your presentation discussion:

1. **Tableau Integration**: Connect to Tableau for advanced visualizations
2. **Mobile App**: React Native app for remote check-ins
3. **Multi-location**: Support for multiple office locations
4. **Analytics**: Attendance patterns and productivity insights
5. **Security**: Enhanced authentication and audit logging

## 🔄 Power BI Integration

The system automatically updates Power BI export files when:
- New employees are registered (with chosen location assignment)
- Sample data is created
- Database is set up

**Files automatically updated:**
- `all_locations_employees_fixed.csv`
- `all_locations_time_logs_fixed.csv`
- `all_locations_system_logs_fixed.csv`

**Smart Updates**: New employees are automatically detected and added to your chosen location without duplicating existing data. The system intelligently syncs database changes to CSV files, ensuring your Power BI dashboard always reflects the latest information!

## 🤝 Support

If you encounter any issues:

1. Check the **System Logs** page in the web interface
2. Run `python run_stes.py status` to diagnose problems
3. Review the console output for error messages
4. Ensure your camera permissions are enabled

---

*This system demonstrates practical application of computer vision, database management, and web development skills learned during your internship.* 