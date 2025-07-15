"""
Time Entry Manager for Smart Time Entry System (STES)
Handles clock-in/out logic with face recognition and cooldown prevention
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging
import threading
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_database_manager
from utils.face_recognition_utils import FaceRecognitionManager
from config.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeEntryManager:
    """
    Manager class for handling time entry operations
    Integrates face recognition with database logging
    """
    
    def __init__(self, config_env='default'):
        """
        Initialize Time Entry Manager
        
        Args:
            config_env (str): Configuration environment
        """
        self.config = get_config(config_env)
        self.db_manager = get_database_manager(config_env)
        
        # Track recent recognitions to prevent duplicate entries
        self.recent_recognitions = {}  # {employee_name: datetime}
        
        # Statistics
        self.stats = {
            'total_recognitions': 0,
            'successful_clock_ins': 0,
            'successful_clock_outs': 0,
            'duplicate_preventions': 0,
            'unknown_faces': 0
        }
        
        logger.info("✅ Time Entry Manager initialized")
    
    def is_within_cooldown(self, employee_name: str) -> bool:
        """
        Check if employee recognition is within cooldown period
        
        Args:
            employee_name (str): Name of the employee
            
        Returns:
            bool: True if within cooldown period
        """
        if employee_name not in self.recent_recognitions:
            return False
        
        last_recognition = self.recent_recognitions[employee_name]
        cooldown_period = self.config.get_cooldown_timedelta()
        
        return datetime.now() - last_recognition < cooldown_period
    
    def update_recent_recognition(self, employee_name: str):
        """
        Update the recent recognition timestamp for an employee
        
        Args:
            employee_name (str): Name of the employee
        """
        self.recent_recognitions[employee_name] = datetime.now()
    
    def get_employee_status(self, employee_name: str) -> Dict:
        """
        Get current status of an employee
        
        Args:
            employee_name (str): Name of the employee
            
        Returns:
            Dict: Employee status information
        """
        try:
            # Check cooldown first
            if self.is_within_cooldown(employee_name):
                return {
                    'exists': True,
                    'status': 'cooldown',
                    'message': f'{employee_name} is in cooldown period'
                }
            
            # Get employee from database
            employee = self.db_manager.get_employee_by_name(employee_name)
            
            if not employee:
                return {
                    'exists': False,
                    'status': 'not_found',
                    'message': f'{employee_name} not found in database'
                }
            
            # Get today's time log
            today = datetime.now().date()
            time_log = self.db_manager.get_latest_time_log(employee['id'], today)
            
            if not time_log:
                return {
                    'exists': True,
                    'employee_id': employee['id'],
                    'status': 'not_clocked_in',
                    'message': f'{employee_name} has not clocked in today',
                    'time_log': None
                }
            
            # Check if this is a ready record (no clock_in yet)
            if not time_log['clock_in'] and time_log['status'] == 'ready':
                return {
                    'exists': True,
                    'employee_id': employee['id'],
                    'status': 'not_clocked_in',
                    'message': f'{employee_name} has not clocked in today',
                    'time_log': time_log
                }
            
            if time_log['clock_in'] and not time_log['clock_out']:
                return {
                    'exists': True,
                    'employee_id': employee['id'],
                    'status': 'clocked_in',
                    'message': f'{employee_name} is currently clocked in since {time_log["clock_in"].strftime("%H:%M")}',
                    'time_log': time_log
                }
            
            if time_log['clock_in'] and time_log['clock_out']:
                return {
                    'exists': True,
                    'employee_id': employee['id'],
                    'status': 'clocked_out',
                    'message': f'{employee_name} clocked out at {time_log["clock_out"].strftime("%H:%M")}',
                    'time_log': time_log
                }
            
            return {
                'exists': True,
                'employee_id': employee['id'],
                'status': 'incomplete',
                'message': f'{employee_name} has incomplete time log',
                'time_log': time_log
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting employee status: {e}")
            return {
                'exists': False,
                'status': 'error',
                'message': f'Error retrieving status for {employee_name}: {str(e)}'
            }
    
    def process_clock_in(self, employee_name: str) -> Dict:
        """
        Process clock-in for an employee
        
        Args:
            employee_name (str): Name of the employee
            
        Returns:
            Dict: Result of clock-in operation
        """
        try:
            employee_status = self.get_employee_status(employee_name)
            
            if not employee_status['exists']:
                return {
                    'success': False,
                    'action': 'clock_in',
                    'message': employee_status['message']
                }
            
            if employee_status['status'] == 'clocked_in':
                return {
                    'success': False,
                    'action': 'clock_in',
                    'message': f'{employee_name} is already clocked in'
                }
            
            # Update existing time log with clock-in or create new one
            now = datetime.now()
            
            if employee_status.get('time_log') and employee_status['time_log']['status'] == 'ready':
                # Update existing ready record
                time_log_id = employee_status['time_log']['id']
                self.db_manager.update_time_log_checkin(time_log_id, now)
            else:
                # Create new time log
                time_log_id = self.db_manager.create_time_log(
                    employee_id=employee_status['employee_id'],
                    clock_in=now,
                    date=now.date()
                )
            
            # Log system event
            self.db_manager.log_system_event(
                event_type='clock_in',
                message=f'{employee_name} clocked in',
                employee_id=employee_status['employee_id'],
                details={
                    'timestamp': now.isoformat(),
                    'time_log_id': time_log_id
                }
            )
            
            # Update statistics
            self.stats['successful_clock_ins'] += 1
            
            logger.info(f"✅ Clock-in successful: {employee_name} at {now.strftime('%H:%M:%S')}")
            
            return {
                'success': True,
                'action': 'clock_in',
                'message': f'{employee_name} clocked in successfully at {now.strftime("%H:%M:%S")}',
                'employee_name': employee_name,
                'time_log_id': time_log_id,
                'timestamp': now
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing clock-in: {e}")
            return {
                'success': False,
                'action': 'clock_in',
                'message': f'Error processing clock-in for {employee_name}: {str(e)}'
            }
    
    def process_clock_out(self, employee_name: str) -> Dict:
        """
        Process clock-out for an employee
        
        Args:
            employee_name (str): Name of the employee
            
        Returns:
            Dict: Result of clock-out operation
        """
        try:
            employee_status = self.get_employee_status(employee_name)
            
            if not employee_status['exists']:
                return {
                    'success': False,
                    'action': 'clock_out',
                    'message': employee_status['message']
                }
            
            if employee_status['status'] != 'clocked_in':
                return {
                    'success': False,
                    'action': 'clock_out',
                    'message': f'{employee_name} is not currently clocked in'
                }
            
            # Update time log with clock-out
            now = datetime.now()
            time_log = self.db_manager.update_time_log_checkout(
                employee_status['time_log']['id'],
                now
            )
            
            # Log system event
            self.db_manager.log_system_event(
                event_type='clock_out',
                message=f'{employee_name} clocked out',
                employee_id=employee_status['employee_id'],
                details={
                    'timestamp': now.isoformat(),
                    'time_log_id': time_log['id'] if time_log else None,
                    'duration_hours': time_log['duration_hours'] if time_log else None
                }
            )
            
            # Update statistics
            self.stats['successful_clock_outs'] += 1
            
            logger.info(f"✅ Clock-out successful: {employee_name} at {now.strftime('%H:%M:%S')}")
            
            return {
                'success': True,
                'action': 'clock_out',
                'message': f'{employee_name} clocked out successfully at {now.strftime("%H:%M:%S")}',
                'employee_name': employee_name,
                'time_log_id': time_log['id'] if time_log else None,
                'timestamp': now,
                'duration_hours': time_log['duration_hours'] if time_log else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing clock-out: {e}")
            return {
                'success': False,
                'action': 'clock_out',
                'message': f'Error processing clock-out for {employee_name}: {str(e)}'
            }
    
    def handle_face_recognition(self, recognized_names: List[str]) -> List[Dict]:
        """
        Handle face recognition results and process time entries
        
        Args:
            recognized_names (List[str]): List of recognized names from face recognition
            
        Returns:
            List[Dict]: List of processing results
        """
        results = []
        
        for name in recognized_names:
            # Update statistics
            self.stats['total_recognitions'] += 1
            
            # Skip unknown faces
            if name == "Unknown":
                self.stats['unknown_faces'] += 1
                continue
            
            # Check cooldown period
            if self.is_within_cooldown(name):
                self.stats['duplicate_preventions'] += 1
                logger.info(f"⏰ Cooldown active for {name}, skipping recognition")
                continue
            
            # Get employee status and decide action
            employee_status = self.get_employee_status(name)
            
            if not employee_status['exists']:
                results.append({
                    'employee_name': name,
                    'success': False,
                    'action': 'none',
                    'message': f'Employee {name} not found in database'
                })
                continue
            
            # Decide whether to clock in or out
            if employee_status['status'] == 'not_clocked_in':
                # Clock in
                result = self.process_clock_in(name)
                result['employee_name'] = name
                results.append(result)
                
                # Update recent recognition only on success
                if result['success']:
                    self.update_recent_recognition(name)
                
            elif employee_status['status'] == 'clocked_in':
                # Clock out
                result = self.process_clock_out(name)
                result['employee_name'] = name
                results.append(result)
                
                # Update recent recognition only on success
                if result['success']:
                    self.update_recent_recognition(name)
                
            else:
                # Already clocked out or other status
                results.append({
                    'employee_name': name,
                    'success': False,
                    'action': 'none',
                    'message': employee_status['message']
                })
        
        return results
    
    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """
        Get daily summary of time entries
        
        Args:
            date (Optional[datetime]): Date for summary (defaults to today)
            
        Returns:
            Dict: Daily summary
        """
        try:
            if date is None:
                date = datetime.now().date()
            
            # Get all time logs for the date
            time_logs = self.db_manager.get_time_logs_by_date_range(date, date)
            
            summary = {
                'date': date.isoformat(),
                'total_employees': len(time_logs),
                'clocked_in': 0,
                'clocked_out': 0,
                'incomplete': 0,
                'total_hours': 0.0,
                'employees': []
            }
            
            for log in time_logs:
                employee_info = {
                    'name': log.employee.name,
                    'clock_in': log.clock_in.strftime('%H:%M:%S') if log.clock_in else None,
                    'clock_out': log.clock_out.strftime('%H:%M:%S') if log.clock_out else None,
                    'duration_hours': log.duration_hours,
                    'status': log.status
                }
                
                summary['employees'].append(employee_info)
                
                # Update counters
                if log.status == 'completed':
                    summary['clocked_out'] += 1
                    if log.duration_hours:
                        summary['total_hours'] += float(log.duration_hours)
                elif log.status == 'active':
                    summary['clocked_in'] += 1
                else:
                    summary['incomplete'] += 1
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error getting daily summary: {e}")
            return {
                'date': date.isoformat() if date else 'unknown',
                'error': str(e)
            }
    
    def get_system_statistics(self) -> Dict:
        """
        Get system statistics
        
        Returns:
            Dict: System statistics
        """
        return {
            'runtime_stats': self.stats,
            'recent_recognitions': {
                name: timestamp.strftime('%H:%M:%S')
                for name, timestamp in self.recent_recognitions.items()
            },
            'cooldown_minutes': self.config.COOLDOWN_MINUTES,
            'database_url': self.config.DATABASE_URL
        }
    
    def cleanup_old_recognitions(self, hours_old: int = 24):
        """
        Clean up old recognition entries
        
        Args:
            hours_old (int): Remove recognitions older than this many hours
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            
            # Remove old entries
            to_remove = []
            for name, timestamp in self.recent_recognitions.items():
                if timestamp < cutoff_time:
                    to_remove.append(name)
            
            for name in to_remove:
                del self.recent_recognitions[name]
            
            if to_remove:
                logger.info(f"🧹 Cleaned up {len(to_remove)} old recognition entries")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up old recognitions: {e}")


class TimeEntryService:
    """
    Service class that combines face recognition with time entry management
    """
    
    def __init__(self, config_env='default'):
        """
        Initialize Time Entry Service
        
        Args:
            config_env (str): Configuration environment
        """
        self.config = get_config(config_env)
        self.time_manager = TimeEntryManager(config_env)
        self.face_manager = FaceRecognitionManager(self.config)
        
        # Service state
        self.is_running = False
        self.processing_thread = None
        
        # Event callbacks
        self.on_face_recognized = None
        self.on_time_entry_processed = None
        
        logger.info("✅ Time Entry Service initialized")
    
    def start_service(self):
        """Start the time entry service"""
        try:
            self.is_running = True
            logger.info("🚀 Time Entry Service started")
            
        except Exception as e:
            logger.error(f"❌ Error starting service: {e}")
            raise
    
    def stop_service(self):
        """Stop the time entry service"""
        try:
            self.is_running = False
            
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
            
            logger.info("⏹️ Time Entry Service stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping service: {e}")
    
    def process_frame(self, frame):
        """
        Process a single frame for face recognition and time entry
        
        Args:
            frame: Video frame from camera
            
        Returns:
            Tuple: (processed_frame, recognition_results)
        """
        try:
            # Process frame with face recognition
            processed_frame, recognized_names = self.face_manager.process_frame(frame)
            
            # Handle time entries if faces are recognized
            results = []
            if recognized_names:
                results = self.time_manager.handle_face_recognition(recognized_names)
                
                # Trigger callbacks
                if self.on_face_recognized:
                    self.on_face_recognized(recognized_names)
                
                if self.on_time_entry_processed and results:
                    self.on_time_entry_processed(results)
            
            return processed_frame, results
            
        except Exception as e:
            logger.error(f"❌ Error processing frame: {e}")
            return frame, []
    
    def get_service_status(self) -> Dict:
        """
        Get comprehensive service status
        
        Returns:
            Dict: Service status information
        """
        return {
            'is_running': self.is_running,
            'face_recognition_stats': self.face_manager.get_face_statistics(),
            'time_entry_stats': self.time_manager.get_system_statistics(),
            'daily_summary': self.time_manager.get_daily_summary(),
            'config': {
                'cooldown_minutes': self.config.COOLDOWN_MINUTES,
                'face_recognition_tolerance': self.config.FACE_RECOGNITION_TOLERANCE,
                'detection_model': self.config.FACE_DETECTION_MODEL
            }
        } 