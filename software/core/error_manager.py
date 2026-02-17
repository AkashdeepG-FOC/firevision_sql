"""
Central Error Manager for Thread Health Monitoring

Responsibilities:
- Collect errors from all workers
- Log errors to file and console
- Emit UI notifications
- Decide recovery actions (restart vs disable)
- Track error patterns
"""

import os
import logging
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from collections import defaultdict


class ErrorManager(QObject):
    """
    Centralized error collection and recovery decision making.
    
    Signals:
        critical_error(str, str): Emits (worker_name, error_msg) for UI alerts
        worker_disabled(str, str): Emits (worker_name, reason) when feature disabled
        restart_requested(str): Emits (worker_name) when restart should be attempted
    """
    
    # Signals
    critical_error = pyqtSignal(str, str)  # worker_name, error_msg
    worker_disabled = pyqtSignal(str, str)  # worker_name, reason
    restart_requested = pyqtSignal(str)  # worker_name
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(ErrorManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize error manager (singleton)"""
        if self._initialized:
            return
            
        super().__init__()
        self._initialized = True
        
        # Setup logging
        self._setup_logging()
        
        # Track registered workers
        self.workers = {}
        
        # Track error counts per worker
        self.error_counts = defaultdict(int)
        
        # Track last error time per worker
        self.last_error_time = {}
        
        self.logger.info("ErrorManager initialized")
    
    def _setup_logging(self):
        """Setup file and console logging"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('ErrorManager')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        log_file = os.path.join(log_dir, 'errors.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def register_worker(self, worker):
        """
        Register a worker for error monitoring.
        
        Args:
            worker: BaseWorker instance to monitor
        """
        worker_name = worker.name
        
        if worker_name in self.workers:
            self.logger.warning(f"Worker '{worker_name}' already registered, replacing...")
        
        # Store worker reference
        self.workers[worker_name] = worker
        
        # Connect to worker signals
        worker.error_occurred.connect(self.handle_worker_error)
        worker.status_changed.connect(self.handle_status_change)
        worker.restart_attempted.connect(self.handle_restart_attempt)
        
        self.logger.info(f"Registered worker: {worker_name}")
    
    def unregister_worker(self, worker_name):
        """
        Unregister a worker from monitoring.
        
        Args:
            worker_name: Name of worker to unregister
        """
        if worker_name in self.workers:
            worker = self.workers[worker_name]
            
            # Disconnect signals
            try:
                worker.error_occurred.disconnect(self.handle_worker_error)
                worker.status_changed.disconnect(self.handle_status_change)
                worker.restart_attempted.disconnect(self.handle_restart_attempt)
            except:
                pass
            
            # Remove from tracking
            del self.workers[worker_name]
            self.logger.info(f"Unregistered worker: {worker_name}")
    
    def handle_worker_error(self, worker_name, error_msg, traceback_str):
        """
        Handle error from a worker.
        
        Args:
            worker_name: Name of worker that errored
            error_msg: Error message
            traceback_str: Full traceback string
        """
        # Increment error count
        self.error_counts[worker_name] += 1
        self.last_error_time[worker_name] = datetime.now()
        
        # Log the error
        self.logger.error(f"Worker '{worker_name}' error (count: {self.error_counts[worker_name]}): {error_msg}")
        self.logger.debug(f"Traceback:\n{traceback_str}")
        
        # Check if we should attempt restart
        if self.should_restart(worker_name):
            self.logger.info(f"Requesting restart for '{worker_name}'")
            self.restart_requested.emit(worker_name)
            
            # Attempt restart
            worker = self.workers.get(worker_name)
            if worker:
                success = worker.restart()
                if not success:
                    # Max restarts reached
                    self.disable_feature(worker_name, f"Max restart attempts reached after {worker.MAX_RESTART_ATTEMPTS} failures")
        else:
            # Emit critical error for UI
            self.critical_error.emit(worker_name, error_msg)
    
    def handle_status_change(self, worker_name, new_status):
        """
        Handle status change from a worker.
        
        Args:
            worker_name: Name of worker
            new_status: New status string
        """
        self.logger.debug(f"Worker '{worker_name}' status: {new_status}")
        
        # Reset error count if worker is running successfully
        if new_status == "RUNNING":
            if self.error_counts[worker_name] > 0:
                self.logger.info(f"Worker '{worker_name}' recovered, resetting error count")
                self.error_counts[worker_name] = 0
    
    def handle_restart_attempt(self, worker_name, attempt_number):
        """
        Handle restart attempt notification.
        
        Args:
            worker_name: Name of worker
            attempt_number: Current restart attempt number
        """
        self.logger.warning(f"Worker '{worker_name}' restart attempt {attempt_number}")
    
    def should_restart(self, worker_name):
        """
        Determine if a worker should be restarted.
        
        Args:
            worker_name: Name of worker
            
        Returns:
            bool: True if restart should be attempted
        """
        worker = self.workers.get(worker_name)
        if not worker:
            return False
        
        # Check if already disabled
        if worker.is_disabled():
            return False
        
        # Check if max restarts reached
        if worker.get_restart_count() >= worker.MAX_RESTART_ATTEMPTS:
            return False
        
        return True
    
    def disable_feature(self, worker_name, reason):
        """
        Disable a feature due to repeated failures.
        
        Args:
            worker_name: Name of worker to disable
            reason: Reason for disabling
        """
        self.logger.critical(f"DISABLING FEATURE '{worker_name}': {reason}")
        
        # Emit signal for UI
        self.worker_disabled.emit(worker_name, reason)
        
        # Stop the worker if it exists
        worker = self.workers.get(worker_name)
        if worker and worker.isRunning():
            worker.stop()
            worker.wait()
    
    def get_worker_status(self, worker_name):
        """
        Get status of a specific worker.
        
        Args:
            worker_name: Name of worker
            
        Returns:
            dict: Status information
        """
        worker = self.workers.get(worker_name)
        if not worker:
            return None
        
        return {
            'name': worker_name,
            'status': worker.get_status(),
            'restart_count': worker.get_restart_count(),
            'error_count': self.error_counts[worker_name],
            'last_error': self.last_error_time.get(worker_name),
            'is_disabled': worker.is_disabled()
        }
    
    def get_all_worker_status(self):
        """
        Get status of all registered workers.
        
        Returns:
            dict: Worker name -> status dict
        """
        return {
            name: self.get_worker_status(name)
            for name in self.workers.keys()
        }
    
    def reset_worker(self, worker_name):
        """
        Manually reset a worker's error state.
        
        Args:
            worker_name: Name of worker to reset
        """
        worker = self.workers.get(worker_name)
        if worker:
            worker.reset_restart_counter()
            self.error_counts[worker_name] = 0
            self.logger.info(f"Manually reset worker '{worker_name}'")
