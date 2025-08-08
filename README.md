# Smart Time Entry System (STES)

A Python-based automated employee time tracking system using face recognition and computer vision technologies. Built for Nsight Inc. internship demonstration.

Note that this is NOT complete. Currently out of the two ways to connect data into Power BI, only using CSV files on a single desktop works. Getting it to function through SQL server is still incomplete and can be worked on in the future.

## 🚀 Features

- **Real-time Face Recognition**: Uses webcam to detect and recognize employee faces
- **Automated Time Logging**: Automatically logs clock-in and clock-out timestamps
- **Duplicate Prevention**: Prevents duplicate entries with configurable cooldown period
- **SQL Database Integration**: Stores time logs in PostgreSQL or SQLite
- **Streamlit Web Interface**: Modern web UI for real-time monitoring
- **Employee Registration**: Easy utility to add new employees to the system
- **Tableau Integration**: Optional dashboard visualization (future enhancement)

## 🛠️ Technologies Used

- **Python 3.8+**: Core programming language
- **OpenCV**: Computer vision and image processing
- **face_recognition**: Face detection and recognition (dlib-based)
- **SQLAlchemy**: Database ORM
- **Streamlit**: Web application framework
- **pandas**: Data analysis and manipulation
- **PostgreSQL/SQLite**: Database storage
- **Power BI**: Data visualization

## 📁 Project Structure

```
STES/
├── models/           # Database models and schemas
├── db/              # Database connection and utilities
├── ui/              # Streamlit web interface
├── utils/           # Utility functions and helpers
├── data/            # Face encodings and employee photos
├── config/          # Configuration files
├── requirements.txt # Python dependencies
└── README.md       # This file
```

## 🔧 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd STES
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install face_recognition and dependencies:**
   ```bash
   pip install cmake
   pip install dlib
   pip install face_recognition
   ```

4. **Set up the database:**
   ```bash
   python db/setup_database.py
   ```

5. **Configure the application:**
   - Copy `.env.example` to `.env`
   - Update configuration values as needed

## 🚀 Usage

1. **Register employees:**
   ```bash
   python utils/register_employee.py
   ```

2. **Run the Streamlit application:**
   ```bash
   streamlit run ui/main.py
   ```

3. **Access the web interface:**
   Open your browser and navigate to `http://localhost:8501`

## ⚙️ Configuration

Key configuration options in `config/config.py`:

- `FACE_RECOGNITION_TOLERANCE`: Sensitivity of face recognition (0.6 default)
- `COOLDOWN_MINUTES`: Minimum time between clock-in/out (10 minutes default)
- `DATABASE_URL`: Database connection string
- `CAMERA_INDEX`: Which camera to use (0 for default)

## 🎯 How It Works

1. **Initialization**: System loads saved face encodings of known employees
2. **Detection**: Webcam continuously scans for faces in real-time
3. **Recognition**: When a face is detected, it's compared against known encodings
4. **Logging**: 
   - First recognition of the day → Clock-in
   - Subsequent recognition after cooldown → Clock-out
5. **Storage**: Timestamps stored in SQL database with duplicate prevention

## 🗄️ Database Schema

```sql
CREATE TABLE time_logs (
    id SERIAL PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL,
    clock_in TIMESTAMP,
    clock_out TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    face_encoding TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 Demo and Testing

The system includes sample employee data for testing:
- Mock employee photos in `data/employee_photos/`
- Pre-computed face encodings in `data/face_encodings.pkl`
- Test database with sample records

## 🤝 Contributing

This is an internship project for Nsight Inc. For questions or suggestions, please contact the development team.

## 📄 License

This project is developed for educational and demonstration purposes as part of the Nsight Inc. internship program.

## 🎓 Learning Objectives

This project demonstrates proficiency in:
- Computer Vision and Face Recognition
- Database Design and Management
- Web Application Development
- Python Programming Best Practices
- Real-time Data Processing
- User Interface Design

---

**Built with ❤️ during Nsight Inc. Internship**