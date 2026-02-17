"""
System Health Panel - Real-time status monitoring for background workers

Displays the health status of all background workers in a compact panel.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from workers.base_worker import WorkerStatus


class SystemHealthPanel(QWidget):
    """
    Real-time health monitoring panel for background workers.
    
    Shows status indicators for:
    - Camera Capture threads
    - Fire Detection threads
    - People Detection threads
    - Other background services
    """
    
    def __init__(self, error_manager, parent=None):
        super().__init__(parent)
        self.error_manager = error_manager
        self.worker_labels = {}  # worker_name -> (status_indicator, status_label)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Header
        header = QLabel("System Health")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(10)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Scroll area for worker status items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(300)
        
        # Container for worker items
        self.workers_container = QWidget()
        self.workers_layout = QVBoxLayout(self.workers_container)
        self.workers_layout.setContentsMargins(0, 0, 0, 0)
        self.workers_layout.setSpacing(3)
        
        scroll.setWidget(self.workers_container)
        layout.addWidget(scroll)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Style
        self.setStyleSheet("""
            SystemHealthPanel {
                background-color: #2b2b2b;
                border-radius: 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
    
    def add_worker(self, worker_name, display_name=None):
        """
        Add a worker to the health panel.
        
        Args:
            worker_name: Internal worker name
            display_name: Human-readable display name (optional)
        """
        if worker_name in self.worker_labels:
            return  # Already added
        
        if display_name is None:
            display_name = worker_name
        
        # Create row widget
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(5, 3, 5, 3)
        row_layout.setSpacing(8)
        
        # Status indicator (colored circle)
        status_indicator = QLabel("●")
        status_indicator.setFixedWidth(15)
        status_indicator.setStyleSheet("color: #888888; font-size: 14px;")  # Gray by default
        row_layout.addWidget(status_indicator)
        
        # Worker name
        name_label = QLabel(display_name)
        name_label.setStyleSheet("color: #ffffff; font-size: 11px;")
        row_layout.addWidget(name_label, 1)
        
        # Status text
        status_label = QLabel("IDLE")
        status_label.setStyleSheet("color: #888888; font-size: 10px;")
        status_label.setAlignment(Qt.AlignRight)
        row_layout.addWidget(status_label)
        
        # Add to layout
        self.workers_layout.addWidget(row)
        
        # Store references
        self.worker_labels[worker_name] = (status_indicator, status_label, row)
    
    @pyqtSlot(str, str)
    def update_worker_status(self, worker_name, status):
        """
        Update the status of a worker.
        
        Args:
            worker_name: Name of the worker
            status: New status (from WorkerStatus)
        """
        if worker_name not in self.worker_labels:
            # Auto-add worker if not already added
            self.add_worker(worker_name)
        
        status_indicator, status_label, row = self.worker_labels[worker_name]
        
        # Update status text
        status_label.setText(status)
        
        # Update indicator color based on status
        if status == WorkerStatus.RUNNING:
            color = "#00ff00"  # Green
            status_label.setStyleSheet("color: #00ff00; font-size: 10px;")
        elif status in [WorkerStatus.STARTING, WorkerStatus.RESTARTING]:
            color = "#ffaa00"  # Yellow/Orange
            status_label.setStyleSheet("color: #ffaa00; font-size: 10px;")
        elif status == WorkerStatus.CRASHED:
            color = "#ff0000"  # Red
            status_label.setStyleSheet("color: #ff0000; font-size: 10px;")
        elif status == WorkerStatus.DISABLED:
            color = "#ff0000"  # Red
            status_label.setStyleSheet("color: #ff0000; font-size: 10px;")
        elif status == WorkerStatus.STOPPED:
            color = "#888888"  # Gray
            status_label.setStyleSheet("color: #888888; font-size: 10px;")
        else:  # IDLE
            color = "#888888"  # Gray
            status_label.setStyleSheet("color: #888888; font-size: 10px;")
        
        status_indicator.setStyleSheet(f"color: {color}; font-size: 14px;")
        
        # Make row clickable if crashed/disabled
        if status in [WorkerStatus.CRASHED, WorkerStatus.DISABLED]:
            row.setCursor(Qt.PointingHandCursor)
            row.mousePressEvent = lambda event: self.show_worker_details(worker_name)
        else:
            row.setCursor(Qt.ArrowCursor)
            row.mousePressEvent = None
    
    def show_worker_details(self, worker_name):
        """Show detailed error information for a worker"""
        worker_status = self.error_manager.get_worker_status(worker_name)
        
        if not worker_status:
            return
        
        # Build message
        message = f"Worker: {worker_name}\n"
        message += f"Status: {worker_status['status']}\n"
        message += f"Restart Count: {worker_status['restart_count']}\n"
        message += f"Error Count: {worker_status['error_count']}\n"
        
        if worker_status['last_error']:
            message += f"\nLast Error: {worker_status['last_error']}"
        
        # Create message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"Worker Status: {worker_name}")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Warning if worker_status['is_disabled'] else QMessageBox.Information)
        
        # Add buttons
        if worker_status['is_disabled']:
            msg_box.addButton("View Logs", QMessageBox.ActionRole)
            msg_box.addButton("Retry Manually", QMessageBox.ActionRole)
            msg_box.addButton("Close", QMessageBox.RejectRole)
        else:
            msg_box.addButton("OK", QMessageBox.AcceptRole)
        
        result = msg_box.exec_()
        
        # Handle button clicks
        if result == 0 and worker_status['is_disabled']:
            # View Logs
            self.open_error_log()
        elif result == 1 and worker_status['is_disabled']:
            # Retry Manually
            self.retry_worker(worker_name)
    
    def retry_worker(self, worker_name):
        """Manually retry a failed worker"""
        self.error_manager.reset_worker(worker_name)
        
        # Get worker reference and restart
        workers = self.error_manager.workers
        if worker_name in workers:
            worker = workers[worker_name]
            worker.start()
            
            QMessageBox.information(
                self,
                "Worker Restarted",
                f"Worker '{worker_name}' has been manually restarted."
            )
    
    def open_error_log(self):
        """Open the error log file"""
        import os
        import subprocess
        
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        log_file = os.path.join(log_dir, 'errors.log')
        
        if os.path.exists(log_file):
            # Open with default text editor
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(log_file)
                elif os.name == 'posix':  # macOS, Linux
                    subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', log_file))
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error Opening Log",
                    f"Could not open log file: {str(e)}"
                )
        else:
            QMessageBox.information(
                self,
                "No Log File",
                "Error log file does not exist yet."
            )
    
    def get_status_summary(self):
        """Get a summary of all worker statuses"""
        summary = {
            'total': len(self.worker_labels),
            'running': 0,
            'crashed': 0,
            'disabled': 0,
            'stopped': 0
        }
        
        for worker_name in self.worker_labels:
            worker_status = self.error_manager.get_worker_status(worker_name)
            if worker_status:
                status = worker_status['status']
                if status == WorkerStatus.RUNNING:
                    summary['running'] += 1
                elif status == WorkerStatus.CRASHED:
                    summary['crashed'] += 1
                elif status == WorkerStatus.DISABLED:
                    summary['disabled'] += 1
                elif status == WorkerStatus.STOPPED:
                    summary['stopped'] += 1
        
        return summary
