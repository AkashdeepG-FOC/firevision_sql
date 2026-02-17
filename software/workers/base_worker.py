"""
Base Worker Abstraction for Thread Health Monitoring

Provides a foundation class for all background workers with built-in:
- Lifecycle status tracking
- Automatic exception handling
- Controlled restart mechanism
- Error reporting via signals
"""

import time
import traceback
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime


class WorkerStatus:
    """Worker lifecycle status constants"""
    IDLE = "IDLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    RESTARTING = "RESTARTING"
    CRASHED = "CRASHED"
    STOPPED = "STOPPED"
    DISABLED = "DISABLED"


class BaseWorker(QThread):
    """
    Base class for all background workers with health monitoring.
    
    Signals:
        status_changed(str, str): Emits (worker_name, new_status)
        error_occurred(str, str, str): Emits (worker_name, error_msg, traceback)
        restart_attempted(str, int): Emits (worker_name, attempt_number)
    """
    
    # Signals
    status_changed = pyqtSignal(str, str)  # worker_name, status
    error_occurred = pyqtSignal(str, str, str)  # worker_name, error_msg, traceback
    restart_attempted = pyqtSignal(str, int)  # worker_name, attempt_number
    
    # Configuration
    MAX_RESTART_ATTEMPTS = 3
    RESTART_DELAYS = [2, 3, 5]  # seconds, exponential backoff
    RESTART_WINDOW = 300  # 5 minutes - reset counter if stable
    
    def __init__(self, name, parent=None):
        """
        Initialize base worker.
        
        Args:
            name: Unique identifier for this worker
            parent: Parent QObject
        """
        super().__init__(parent)
        self.name = name
        self.restart_count = 0
        self.last_successful_start = None
        self.current_status = WorkerStatus.IDLE
        self._running = False
        self._stop_requested = False
        
    def run(self):
        """
        Main thread execution with exception handling.
        DO NOT OVERRIDE - Override work() instead.
        """
        try:
            self._stop_requested = False
            self._running = True
            
            # Update status to STARTING
            self._update_status(WorkerStatus.STARTING)
            
            # Check if we should reset restart counter
            if self.last_successful_start:
                elapsed = time.time() - self.last_successful_start
                if elapsed > self.RESTART_WINDOW:
                    self.restart_count = 0
            
            # Mark successful start
            self.last_successful_start = time.time()
            
            # Update status to RUNNING
            self._update_status(WorkerStatus.RUNNING)
            
            # Execute the actual work
            self.work()
            
            # If we get here, work completed normally
            self._update_status(WorkerStatus.STOPPED)
            
        except Exception as e:
            # Capture full traceback
            tb = traceback.format_exc()
            error_msg = str(e)
            
            # Update status to CRASHED
            self._update_status(WorkerStatus.CRASHED)
            
            # Emit error signal
            self.error_occurred.emit(self.name, error_msg, tb)
            
            # Log to console
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Worker '{self.name}' crashed: {error_msg}")
            print(tb)
            
        finally:
            self._running = False
    
    def work(self):
        """
        Override this method to implement worker logic.
        This is called by run() with automatic exception handling.
        """
        raise NotImplementedError("Subclasses must implement work()")
    
    def stop(self):
        """
        Request graceful shutdown of the worker.
        Override stop_work() for custom cleanup logic.
        """
        self._stop_requested = True
        self._update_status(WorkerStatus.STOPPED)
        self.stop_work()
        
    def stop_work(self):
        """
        Override this method for custom cleanup logic.
        Called when stop() is requested.
        """
        pass
    
    def is_running(self):
        """Check if worker is currently running"""
        return self._running and not self._stop_requested
    
    def should_stop(self):
        """Check if stop has been requested"""
        return self._stop_requested
    
    def restart(self):
        """
        Attempt to restart the worker with controlled retry logic.
        
        Returns:
            bool: True if restart was attempted, False if max attempts reached
        """
        # Check if we've exceeded max attempts
        if self.restart_count >= self.MAX_RESTART_ATTEMPTS:
            self._update_status(WorkerStatus.DISABLED)
            return False
        
        # Increment restart counter
        self.restart_count += 1
        
        # Emit restart attempt signal
        self.restart_attempted.emit(self.name, self.restart_count)
        
        # Update status
        self._update_status(WorkerStatus.RESTARTING)
        
        # Get delay for this attempt
        delay_index = min(self.restart_count - 1, len(self.RESTART_DELAYS) - 1)
        delay = self.RESTART_DELAYS[delay_index]
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Restarting '{self.name}' (attempt {self.restart_count}/{self.MAX_RESTART_ATTEMPTS}) after {delay}s delay...")
        
        # Wait before restart
        time.sleep(delay)
        
        # Restart the thread
        if self.isRunning():
            self.quit()
            self.wait()
        
        self.start()
        return True
    
    def reset_restart_counter(self):
        """Manually reset the restart counter"""
        self.restart_count = 0
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Reset restart counter for '{self.name}'")
    
    def _update_status(self, new_status):
        """Internal method to update and emit status changes"""
        if self.current_status != new_status:
            self.current_status = new_status
            self.status_changed.emit(self.name, new_status)
    
    def get_status(self):
        """Get current worker status"""
        return self.current_status
    
    def get_restart_count(self):
        """Get number of restart attempts"""
        return self.restart_count
    
    def is_disabled(self):
        """Check if worker has been disabled due to too many failures"""
        return self.current_status == WorkerStatus.DISABLED
