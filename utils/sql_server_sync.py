"""
SQL Server Sync Service for Smart Time Entry System (STES)
Handles real-time synchronization between SQLite and SQL Server
"""

import threading
import time
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLServerSyncService:
    """
    Real-time sync service for SQL Server integration
    """
    
    def __init__(self, sql_server_manager, sqlite_db_manager, sync_interval=30):
        """
        Initialize sync service
        
        Args:
            sql_server_manager: SQL Server manager instance
            sqlite_db_manager: SQLite database manager instance
            sync_interval (int): Sync interval in seconds
        """
        self.sql_server_manager = sql_server_manager
        self.sqlite_db_manager = sqlite_db_manager
        self.sync_interval = sync_interval
        self.is_running = False
        self.sync_thread = None
        self.last_sync_time = None
        self.sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync_duration': 0
        }
    
    def start_sync_service(self):
        """Start the sync service"""
        if self.is_running:
            logger.warning("⚠️ Sync service is already running")
            return
        
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info(f"✅ SQL Server sync service started (interval: {self.sync_interval}s)")
    
    def stop_sync_service(self):
        """Stop the sync service"""
        if not self.is_running:
            logger.warning("⚠️ Sync service is not running")
            return
        
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("⏹️ SQL Server sync service stopped")
    
    def _sync_loop(self):
        """Main sync loop"""
        while self.is_running:
            try:
                start_time = time.time()
                self._sync_recent_data()
                duration = time.time() - start_time
                
                self.sync_stats['total_syncs'] += 1
                self.sync_stats['successful_syncs'] += 1
                self.sync_stats['last_sync_duration'] = duration
                self.last_sync_time = datetime.now()
                
                logger.info(f"✅ Sync completed in {duration:.2f}s")
                time.sleep(self.sync_interval)
                
            except Exception as e:
                self.sync_stats['failed_syncs'] += 1
                logger.error(f"❌ Sync error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _sync_recent_data(self):
        """Sync recent data from SQLite to SQL Server"""
        try:
            # Get recent time logs from SQLite
            recent_time_logs = self._get_recent_sqlite_time_logs()
            
            # Get recent system logs from SQLite
            recent_system_logs = self._get_recent_sqlite_system_logs()
            
            # Sync time logs
            for time_log in recent_time_logs:
                self.sql_server_manager.sync_time_log(time_log)
            
            # Sync system logs
            for system_log in recent_system_logs:
                self.sql_server_manager.sync_system_log(system_log)
            
            logger.info(f"✅ Synced {len(recent_time_logs)} time logs and {len(recent_system_logs)} system logs")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync recent data: {e}")
            raise
    
    def _get_recent_sqlite_time_logs(self) -> List[Dict]:
        """Get recent time logs from SQLite database"""
        try:
            # Get time logs from the last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            with self.sqlite_db_manager.get_session() as session:
                from models.database import TimeLog, Employee
                
                recent_logs = session.query(TimeLog).filter(
                    TimeLog.created_at >= cutoff_time
                ).order_by(TimeLog.created_at.desc()).all()
                
                time_log_data = []
                for log in recent_logs:
                    # Get employee name for reference
                    employee = session.query(Employee).filter_by(id=log.employee_id).first()
                    
                    time_log_data.append({
                        'id': log.id,
                        'employee_id': log.employee_id,
                        'employee_name': employee.name if employee else 'Unknown',
                        'clock_in': log.clock_in,
                        'clock_out': log.clock_out,
                        'date': log.date,
                        'duration_hours': log.duration_hours,
                        'status': log.status,
                        'notes': log.notes,
                        'created_at': log.created_at,
                        'updated_at': log.updated_at
                    })
                
                return time_log_data
                
        except Exception as e:
            logger.error(f"❌ Failed to get recent SQLite time logs: {e}")
            return []
    
    def _get_recent_sqlite_system_logs(self) -> List[Dict]:
        """Get recent system logs from SQLite database"""
        try:
            # Get system logs from the last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            with self.sqlite_db_manager.get_session() as session:
                from models.database import SystemLog
                
                recent_logs = session.query(SystemLog).filter(
                    SystemLog.timestamp >= cutoff_time
                ).order_by(SystemLog.timestamp.desc()).all()
                
                system_log_data = []
                for log in recent_logs:
                    system_log_data.append({
                        'id': log.id,
                        'event_type': log.event_type,
                        'employee_id': log.employee_id,
                        'message': log.message,
                        'details': log.get_details() if log.details else {},
                        'timestamp': log.timestamp
                    })
                
                return system_log_data
                
        except Exception as e:
            logger.error(f"❌ Failed to get recent SQLite system logs: {e}")
            return []
    
    def sync_single_time_log(self, time_log_data: Dict) -> bool:
        """
        Sync a single time log immediately
        
        Args:
            time_log_data (dict): Time log data to sync
            
        Returns:
            bool: True if sync successful
        """
        try:
            success = self.sql_server_manager.sync_time_log(time_log_data)
            if success:
                logger.info(f"✅ Immediate sync successful for time log {time_log_data.get('id')}")
            return success
        except Exception as e:
            logger.error(f"❌ Immediate sync failed for time log: {e}")
            return False
    
    def sync_single_system_log(self, system_log_data: Dict) -> bool:
        """
        Sync a single system log immediately
        
        Args:
            system_log_data (dict): System log data to sync
            
        Returns:
            bool: True if sync successful
        """
        try:
            success = self.sql_server_manager.sync_system_log(system_log_data)
            if success:
                logger.info(f"✅ Immediate sync successful for system log {system_log_data.get('event_type')}")
            return success
        except Exception as e:
            logger.error(f"❌ Immediate sync failed for system log: {e}")
            return False
    
    def trigger_immediate_sync(self):
        """Trigger an immediate sync"""
        try:
            logger.info("🔄 Triggering immediate sync...")
            self._sync_recent_data()
            logger.info("✅ Immediate sync completed")
        except Exception as e:
            logger.error(f"❌ Immediate sync failed: {e}")
    
    def get_sync_status(self) -> Dict:
        """Get sync service status"""
        return {
            'is_running': self.is_running,
            'sync_interval': self.sync_interval,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_stats': self.sync_stats.copy(),
            'sql_server_status': self.sql_server_manager.get_sync_status()
        }
    
    def get_sync_health(self) -> Dict:
        """Get sync health information"""
        try:
            # Test SQL Server connection
            sql_server_ok = self.sql_server_manager.test_connection()
            
            # Get sync statistics
            stats = self.get_sync_status()
            
            return {
                'sql_server_connected': sql_server_ok,
                'sync_service_running': self.is_running,
                'last_sync_successful': stats['sync_stats']['failed_syncs'] == 0,
                'total_syncs': stats['sync_stats']['total_syncs'],
                'success_rate': (stats['sync_stats']['successful_syncs'] / max(stats['sync_stats']['total_syncs'], 1)) * 100,
                'last_sync_duration': stats['sync_stats']['last_sync_duration']
            }
        except Exception as e:
            logger.error(f"❌ Failed to get sync health: {e}")
            return {
                'sql_server_connected': False,
                'sync_service_running': self.is_running,
                'last_sync_successful': False,
                'error': str(e)
            } 