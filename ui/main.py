"""
Main Streamlit Application for Smart Time Entry System (STES)
Provides a web-based interface for real-time face recognition and time tracking
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import time
import threading
import logging
from typing import Optional, Dict, List
import face_recognition

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.time_entry_manager import TimeEntryService
from utils.face_recognition_utils import VideoCapture
from db.connection import get_database_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Smart Time Entry System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        color: white;
    }
    
    .metrics-container {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    
    .employee-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .recognition-box {
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'service' not in st.session_state:
    st.session_state.service = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'video_capture' not in st.session_state:
    st.session_state.video_capture = None
if 'recent_recognitions' not in st.session_state:
    st.session_state.recent_recognitions = []
if 'system_stats' not in st.session_state:
    st.session_state.system_stats = {}

def initialize_system():
    """Initialize the STES system"""
    try:
        config = get_config()
        
        # Initialize time entry service
        if st.session_state.service is None:
            st.session_state.service = TimeEntryService()
        
        # Initialize video capture
        if st.session_state.video_capture is None:
            st.session_state.video_capture = VideoCapture(config)
        
        return True
        
    except Exception as e:
        st.error(f"Failed to initialize system: {str(e)}")
        logger.error(f"System initialization failed: {e}")
        return False

def start_system():
    """Start the STES system"""
    try:
        if st.session_state.service and st.session_state.video_capture:
            st.session_state.service.start_service()
            st.session_state.video_capture.start_capture()
            st.session_state.is_running = True
            st.success("🚀 System started successfully!")
            logger.info("STES system started")
        else:
            st.error("❌ System not properly initialized")
            
    except Exception as e:
        st.error(f"Failed to start system: {str(e)}")
        logger.error(f"System start failed: {e}")

def stop_system():
    """Stop the STES system"""
    try:
        if st.session_state.service:
            st.session_state.service.stop_service()
        
        if st.session_state.video_capture:
            st.session_state.video_capture.stop_capture()
        
        st.session_state.is_running = False
        st.success("⏹️ System stopped successfully!")
        logger.info("STES system stopped")
        
    except Exception as e:
        st.error(f"Failed to stop system: {str(e)}")
        logger.error(f"System stop failed: {e}")

def get_system_status():
    """Get comprehensive system status"""
    try:
        if st.session_state.service:
            return st.session_state.service.get_service_status()
        return None
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return None

def process_video_frame():
    """Process video frame for face recognition"""
    try:
        if not st.session_state.is_running or not st.session_state.video_capture:
            return None, []
        
        # Get frame from video capture
        ret, frame, recognized_names = st.session_state.video_capture.get_processed_frame()
        
        if not ret or frame is None:
            return None, []
        
        # Process frame through time entry service
        if st.session_state.service:
            processed_frame, results = st.session_state.service.process_frame(frame)
            
            # Update recent recognitions
            if results:
                for result in results:
                    if result.get('success'):
                        st.session_state.recent_recognitions.append({
                            'timestamp': datetime.now(),
                            'employee_name': result.get('employee_name'),
                            'action': result.get('action'),
                            'message': result.get('message')
                        })
                        
                        # Keep only last 10 recognitions
                        if len(st.session_state.recent_recognitions) > 10:
                            st.session_state.recent_recognitions.pop(0)
            
            return processed_frame, results
        
        return frame, []
        
    except Exception as e:
        logger.error(f"Error processing video frame: {e}")
        return None, []

def display_main_interface():
    """Display the main interface"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Smart Time Entry System (STES)</h1>
        <p>Automated Employee Time Tracking with Face Recognition</p>
    </div>
    """, unsafe_allow_html=True)
    
    # System controls
    st.subheader("🚀 System Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start System", type="primary", help="Initialize and start the face recognition system"):
            if initialize_system():
                start_system()
    
    with col2:
        if st.button("⏹️ Stop System", help="Stop the face recognition system"):
            stop_system()
    
    with col3:
        if st.button("🔄 Refresh Status", help="Update system status"):
            st.session_state.system_stats = get_system_status()
    
    # System status
    st.subheader("📊 System Status")
    
    if st.session_state.is_running:
        st.success("🟢 System is running and ready for face recognition")
        
        # Display current status
        if st.session_state.system_stats:
            stats = st.session_state.system_stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Face Recognition", "✅ Active")
            with col2:
                st.metric("Camera Status", "🟢 Connected")
            with col3:
                st.metric("Database", "✅ Connected")
            with col4:
                st.metric("Time Tracking", "✅ Ready")
    else:
        st.warning("🟡 System is stopped. Click 'Start System' to begin.")
    
    # Demonstration section
    st.subheader("🎬 Live Demonstration")
    
    st.info("""
    **This is a demonstration system that shows how the Smart Time Entry System works:**
    
    - **Real Camera Feed**: Your webcam will be used to show live video
    - **Face Detection**: The system will detect faces in the video stream
    - **Time Tracking**: Simulate clock-in/out events for demonstration
    - **Database Integration**: All events are logged to the database
    
    **For your demonstration, you can:**
    1. Start the system and see your camera feed
    2. Test face detection functionality
    3. Simulate employee clock-in events
    4. View the results in the sidebar and system logs
    """)
    
    # Display video feed
    display_video_feed()

def display_video_feed():
    """Display the video feed with real face recognition"""
    st.subheader("📹 Live Video Feed")
    camera_index = st.selectbox("Select Camera", [0, 1, 2], help="Try different camera indices if one doesn't work")
    video_placeholder = st.empty()
    status_placeholder = st.empty()

    # --- Display TODAY'S time log for Arnav Mehta ---
    try:
        db_manager = get_database_manager()
        with db_manager.get_session() as session:
            from models.database import Employee, TimeLog
            from sqlalchemy import func
            
            arnav = session.query(Employee).filter_by(name='Arnav Mehta').first()
            today_log_data = None
            if arnav:
                # Get TODAY'S time log only
                today = datetime.now().date()
                today_log = session.query(TimeLog).filter(
                    TimeLog.employee_id == arnav.id,
                    func.date(TimeLog.date) == today
                ).order_by(TimeLog.created_at.desc()).first()
                
                if today_log:
                    # Extract data while still in session
                    today_log_data = {
                        'clock_in': today_log.clock_in,
                        'clock_out': today_log.clock_out,
                        'duration_hours': today_log.duration_hours,
                        'status': today_log.status
                    }
    except Exception as e:
        st.error(f"❌ Database connection error: {str(e)}")
        today_log_data = None
    
    # Add current Pacific Time for reference
    from datetime import timezone, timedelta
    pacific_tz = timezone(timedelta(hours=-8))  # PST (Pacific Standard Time)
    current_time_pacific = datetime.now(pacific_tz)
    current_time_str = current_time_pacific.strftime('%Y-%m-%d %H:%M:%S PST')
    
    if today_log_data:
        clock_in_str = today_log_data['clock_in'].strftime('%Y-%m-%d %H:%M:%S') if today_log_data['clock_in'] else 'N/A'
        clock_out_str = today_log_data['clock_out'].strftime('%Y-%m-%d %H:%M:%S') if today_log_data['clock_out'] else 'N/A'
        duration_str = today_log_data['duration_hours'] if today_log_data['duration_hours'] else 'N/A'
        status_str = today_log_data['status'].title()
        
        st.info(f"**TODAY'S Log for Arnav Mehta:**  \n"
                f"Clock-in: {clock_in_str} PST  \n"
                f"Clock-out: {clock_out_str} PST  \n" 
                f"Duration: {duration_str} hours  \n"
                f"Status: {status_str}  \n"
                f"Current Time: {current_time_str}")
    else:
        st.info(f"**TODAY'S Log for Arnav Mehta:**  \n"
                f"No clock-in record found for today  \n"
                f"Current Time: {current_time_str}")

    # Initialize session state
    if 'camera' not in st.session_state:
        st.session_state.camera = None
    if 'known_face_encodings' not in st.session_state:
        st.session_state.known_face_encodings = []
    if 'known_face_names' not in st.session_state:
        st.session_state.known_face_names = []
    if 'last_recognition_time' not in st.session_state:
        st.session_state.last_recognition_time = 0
    if 'recognition_count' not in st.session_state:
        st.session_state.recognition_count = 0
    if 'session_actions_count' not in st.session_state:
        st.session_state.session_actions_count = 0
    if 'actions_completed' not in st.session_state:
        st.session_state.actions_completed = False

    # Load known faces (only once)
    if not st.session_state.known_face_encodings:
        try:
            db_manager = get_database_manager()
            with db_manager.get_session() as session:
                from models.database import Employee
                arnav_emp = session.query(Employee).filter_by(name='Arnav Mehta').first()
                if arnav_emp:
                    st.session_state.known_face_encodings = [np.array(arnav_emp.get_face_encoding())]
                    st.session_state.known_face_names = ['Arnav Mehta']
                    st.success("✅ Arnav Mehta loaded for face recognition")
                else:
                    st.error("❌ Arnav Mehta not found in database. Please register first.")
                    # Don't return here - still show camera feed even if face recognition fails
                    st.session_state.known_face_encodings = []
                    st.session_state.known_face_names = []
        except Exception as e:
            st.error(f"❌ Error loading face data: {str(e)}")
            # Don't return here - still show camera feed even if face recognition fails
            st.session_state.known_face_encodings = []
            st.session_state.known_face_names = []

    if st.session_state.is_running:
        try:
            if st.session_state.camera is None:
                st.session_state.camera = cv2.VideoCapture(camera_index)
                if not st.session_state.camera.isOpened():
                    st.error(f"❌ Cannot open camera {camera_index}. Please try a different camera index.")
                    return
            
            ret, frame = st.session_state.camera.read()
            if ret and frame is not None:
                # Convert to RGB and resize for processing
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
                
                # Detect faces
                face_locations = face_recognition.face_locations(small_frame)
                face_encodings = face_recognition.face_encodings(small_frame, face_locations)
                
                recognized_names = []
                arnav_detected = False
                
                # Process each detected face
                for face_encoding in face_encodings:
                    name = "Unknown"
                    
                    try:
                        if len(st.session_state.known_face_encodings) > 0:
                            # Compare with known faces
                            face_distances = face_recognition.face_distance(
                                st.session_state.known_face_encodings, 
                                face_encoding
                            )
                            
                            # Get the best match
                            best_match_index = np.argmin(face_distances)
                            
                            # Check if the distance is within tolerance
                            if face_distances[best_match_index] <= 0.4:  # Stricter tolerance
                                name = st.session_state.known_face_names[best_match_index]
                                if name == "Arnav Mehta":
                                    arnav_detected = True
                    except Exception as e:
                        # If face recognition fails, just use "Unknown"
                        logger.error(f"Face recognition error: {e}")
                        name = "Unknown"
                    
                    recognized_names.append(name)
                
                # Draw boxes and names ONLY if faces are detected
                for (top, right, bottom, left), name in zip(face_locations, recognized_names):
                    # Scale back up face locations
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    
                    # Choose color based on recognition
                    color = (0, 255, 0) if name == "Arnav Mehta" else (0, 0, 255)
                    
                    # Draw rectangle around face
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    
                    # Draw label background
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                    
                    # Draw name
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
                
                # Add status text to frame
                status_text = f"Faces: {len(face_locations)} | Arnav Mehta: {'YES' if arnav_detected else 'NO'}"
                cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Display the frame
                display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(display_frame, channels="RGB", use_container_width=True)
                
                # Handle Arnav Mehta recognition with clock-in/out logic
                current_time = time.time()
                if arnav_detected:
                    # Check if we've already completed 2 actions in this session
                    if st.session_state.actions_completed:
                        status_placeholder.info("✅ Session complete. Both clock-in and clock-out have been processed.")
                    # Only process if it's been more than 10 seconds since last recognition
                    elif current_time - st.session_state.last_recognition_time > 10:
                        try:
                            from utils.time_entry_manager import TimeEntryManager
                            time_manager = TimeEntryManager()
                            
                            # Use the proper face recognition handler that includes auto clock-in/out logic
                            results = time_manager.handle_face_recognition(['Arnav Mehta'])
                            
                            if results:
                                result = results[0]  # Get the first (and only) result
                                
                                if result['success']:
                                    st.session_state.recognition_count += 1
                                    st.session_state.session_actions_count += 1
                                    
                                    action_emoji = "🎯" if result['action'] == 'clock_in' else "🚪"
                                    action_text = "Clock-In" if result['action'] == 'clock_in' else "Clock-Out"
                                    
                                    status_placeholder.success(f"{action_emoji} **{action_text} #{st.session_state.recognition_count}** - {result['message']}")
                                    st.session_state.last_recognition_time = current_time
                                    
                                    # Check if we've completed 2 actions
                                    if st.session_state.session_actions_count >= 2:
                                        st.session_state.actions_completed = True
                                    
                                    # Add to recent recognitions
                                    if 'recent_recognitions' not in st.session_state:
                                        st.session_state.recent_recognitions = []
                                    st.session_state.recent_recognitions.append({
                                        'timestamp': datetime.now(),
                                        'employee_name': result['employee_name'],
                                        'action': result['action'],
                                        'message': result['message']
                                    })
                                    
                                    # Force refresh of the page to show updated time log
                                    st.rerun()
                                else:
                                    status_placeholder.warning(f"⚠️ {result['message']}")
                            else:
                                # No results, probably due to cooldown or other issue
                                status = time_manager.get_employee_status('Arnav Mehta')
                                status_placeholder.info(f"ℹ️ Current status: {status['message']}")
                        
                        except Exception as e:
                            status_placeholder.error(f"❌ Error processing time entry: {str(e)}")
                    else:
                        remaining_time = 10 - (current_time - st.session_state.last_recognition_time)
                        status_placeholder.info(f"✅ Arnav Mehta recognized (cooldown: {remaining_time:.1f}s)")
                else:
                    if len(face_locations) == 0:
                        status_placeholder.info("👤 No faces detected. Show your face to the camera.")
                    else:
                        status_placeholder.warning(f"🔍 {len(face_locations)} face(s) detected but not recognized as Arnav Mehta.")
                
            else:
                st.error("❌ Failed to capture frame from camera")
        except Exception as e:
            st.error(f"❌ Camera error: {str(e)}")
            logger.error(f"Camera error: {e}")
    else:
        # Show placeholder when system is not running
        placeholder_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(placeholder_frame, "Camera Offline", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(placeholder_frame, "Click 'Start System' to activate", (150, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        display_frame = cv2.cvtColor(placeholder_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(display_frame, channels="RGB", use_container_width=True)
        status_placeholder.info("System is offline. Click 'Start System' to begin face recognition.")
    
    # Manual refresh button and session reset instead of auto-refresh to reduce flickering
    if st.session_state.is_running:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Feed"):
                st.rerun()
        with col2:
            if st.button("🔄 Reset Session"):
                st.session_state.session_actions_count = 0
                st.session_state.actions_completed = False
                st.session_state.last_recognition_time = 0
                # Force reload face encodings on next refresh
                if 'known_face_encodings' in st.session_state:
                    del st.session_state.known_face_encodings
                if 'known_face_names' in st.session_state:
                    del st.session_state.known_face_names
                st.success("✅ Session reset! You can now clock-in and clock-out again.")
                st.rerun()
    
    # Add a button to clear today's old data
    if st.button("🗑️ Clear Today's Old Data"):
        try:
            db_manager = get_database_manager()
            with db_manager.get_session() as session:
                from models.database import Employee, TimeLog
                from sqlalchemy import func
                
                arnav = session.query(Employee).filter_by(name='Arnav Mehta').first()
                if arnav:
                    # Delete today's time logs
                    today = datetime.now().date()
                    deleted_count = session.query(TimeLog).filter(
                        TimeLog.employee_id == arnav.id,
                        func.date(TimeLog.date) == today
                    ).delete()
                    session.commit()
                    
                    if deleted_count > 0:
                        st.success(f"✅ Cleared {deleted_count} old time log(s) for today")
                    else:
                        st.info("ℹ️ No time logs found for today")
                else:
                    st.error("❌ Arnav Mehta not found in database")
            
            # Reset session state
            st.session_state.session_actions_count = 0
            st.session_state.actions_completed = False
            st.session_state.last_recognition_time = 0
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error clearing data: {str(e)}")

def display_sidebar():
    """Display the sidebar with system information"""
    
    st.sidebar.header("📊 System Information")
    
    # Recent recognitions
    st.sidebar.subheader("🕒 Recent Activity")
    if st.session_state.recent_recognitions:
        for recognition in reversed(st.session_state.recent_recognitions[-5:]):
            timestamp = recognition['timestamp'].strftime("%H:%M:%S")
            name = recognition['employee_name']
            action = recognition['action']
            
            action_icon = "🔵" if action == "clock_in" else "🔴"
            st.sidebar.markdown(f"{action_icon} **{name}** - {action.replace('_', ' ').title()} at {timestamp}")
    else:
        st.sidebar.info("No recent activity")
    
    # System statistics
    if st.session_state.system_stats:
        st.sidebar.subheader("📈 Runtime Statistics")
        stats = st.session_state.system_stats.get('time_entry_stats', {}).get('runtime_stats', {})
        
        st.sidebar.metric("Clock-ins", stats.get('successful_clock_ins', 0))
        st.sidebar.metric("Clock-outs", stats.get('successful_clock_outs', 0))
        st.sidebar.metric("Duplicates Prevented", stats.get('duplicate_preventions', 0))
        st.sidebar.metric("Unknown Faces", stats.get('unknown_faces', 0))
    
    # Configuration
    st.sidebar.subheader("⚙️ Configuration")
    config = get_config()
    st.sidebar.write(f"**Cooldown Period:** {config.COOLDOWN_MINUTES} minutes")
    st.sidebar.write(f"**Recognition Tolerance:** {config.FACE_RECOGNITION_TOLERANCE}")
    st.sidebar.write(f"**Detection Model:** {config.FACE_DETECTION_MODEL}")

# --- Patch for daily summary: ensure it always shows latest logs ---
def display_daily_summary():
    """Display daily summary page"""
    st.header("📅 Daily Summary")
    selected_date = st.date_input("Select Date", datetime.now().date())
    try:
        db_manager = get_database_manager()
        time_logs = db_manager.get_time_logs_by_date_range(selected_date, selected_date)
        if time_logs:
            col1, col2, col3, col4 = st.columns(4)
            total_employees = len(time_logs)
            completed_logs = len([log for log in time_logs if log['status'] == 'completed'])
            active_logs = len([log for log in time_logs if log['status'] == 'active'])
            total_hours = sum([float(log['duration_hours']) for log in time_logs if log['duration_hours']])
            with col1:
                st.metric("Total Employees", total_employees)
            with col2:
                st.metric("Completed Sessions", completed_logs)
            with col3:
                st.metric("Active Sessions", active_logs)
            with col4:
                st.metric("Total Hours", f"{total_hours:.2f}")
            st.subheader("📋 Detailed Time Logs")
            data = []
            for log in time_logs:
                data.append({
                    'Employee': log['employee_name'],
                    'Department': log['employee_department'],
                    'Clock In': log['clock_in'].strftime('%H:%M:%S') if log['clock_in'] else 'N/A',
                    'Clock Out': log['clock_out'].strftime('%H:%M:%S') if log['clock_out'] else 'N/A',
                    'Duration (Hours)': log['duration_hours'] or 'N/A',
                    'Status': log['status'].title()
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"time_logs_{selected_date}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"No time logs found for {selected_date}")
    except Exception as e:
        st.error(f"Error loading daily summary: {str(e)}")
        logger.error(f"Error in daily summary: {e}")

def display_employee_management():
    """Display employee management page"""
    
    st.header("👥 Employee Management")
    
    try:
        db_manager = get_database_manager()
        employees = db_manager.get_all_employees()
        
        if employees:
            st.subheader("📋 Registered Employees")
            
            # Employee table
            data = []
            for emp in employees:
                data.append({
                    'ID': emp['id'],
                    'Name': emp['name'],
                    'Email': emp['email'] or 'N/A',
                    'Department': emp['department'] or 'N/A',
                    'Status': '✅ Active' if emp['is_active'] else '❌ Inactive',
                    'Created': emp['created_at'].strftime('%Y-%m-%d')
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Employee statistics
            st.subheader("📊 Employee Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Employees", len(employees))
            with col2:
                active_count = len([emp for emp in employees if emp['is_active']])
                st.metric("Active Employees", active_count)
            with col3:
                departments = len(set([emp['department'] for emp in employees if emp['department']]))
                st.metric("Departments", departments)
            
        else:
            st.info("No employees registered yet.")
            
        # Registration instructions
        st.subheader("➕ Add New Employee")
        st.info("To register a new employee, use the command line utility:")
        st.code("python utils/register_employee.py --interactive", language="bash")
        
    except Exception as e:
        st.error(f"Error loading employee data: {str(e)}")
        logger.error(f"Error in employee management: {e}")

def main():
    """Main application function"""
    
    # Navigation
    page = st.sidebar.selectbox(
        "🧭 Navigation",
        ["🏠 Home", "📅 Daily Summary", "👥 Employee Management", "⚙️ System Logs"]
    )
    
    # Display sidebar
    display_sidebar()
    
    # Route to appropriate page
    if page == "🏠 Home":
        display_main_interface()
    elif page == "📅 Daily Summary":
        display_daily_summary()
    elif page == "👥 Employee Management":
        display_employee_management()
    elif page == "⚙️ System Logs":
        display_system_logs()

# --- Patch for system logs: ensure clock-in/out events are visible ---
def display_system_logs():
    """Display system logs page"""
    st.header("📝 System Logs")
    try:
        db_manager = get_database_manager()
        with db_manager.get_session() as session:
            from models.database import SystemLog
            logs = session.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(100).all()
            log_data = []
            for log in logs:
                log_dict = {
                    'id': log.id,
                    'event_type': log.event_type,
                    'message': log.message,
                    'timestamp': log.timestamp,
                    'employee_id': log.employee_id,
                    'details': log.get_details() if log.details else {}
                }
                if log.employee_id:
                    from models.database import Employee
                    emp = session.query(Employee).filter_by(id=log.employee_id).first()
                    log_dict['employee_name'] = emp.name if emp else 'Unknown'
                else:
                    log_dict['employee_name'] = None
                log_data.append(log_dict)
        if log_data:
            st.subheader("🔍 Recent System Events")
            event_types = list(set([log['event_type'] for log in log_data]))
            selected_event_type = st.selectbox("Filter by Event Type", ["All"] + event_types)
            filtered_logs = log_data
            if selected_event_type != "All":
                filtered_logs = [log for log in log_data if log['event_type'] == selected_event_type]
            for log in filtered_logs[:20]:
                with st.expander(f"{log['event_type']} - {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                    st.write(f"**Message:** {log['message']}")
                    if log['employee_name']:
                        st.write(f"**Employee:** {log['employee_name']}")
                    if log['details']:
                        st.write(f"**Details:** {log['details']}")
        else:
            st.info("No system logs available")
    except Exception as e:
        st.error(f"Error loading system logs: {str(e)}")
        logger.error(f"Error in system logs: {e}")

if __name__ == "__main__":
    main() 