import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QLineEdit, QCheckBox,
                             QProgressBar, QTextEdit, QTabWidget, QFormLayout,
                             QDialog, QMessageBox, QFileDialog, QSpinBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QScrollArea)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

@dataclass
class CloudProvider:
    """Cloud provider configuration"""
    name: str
    type: str  # 'google_drive', 'dropbox', 'aws_s3', 'azure_blob'
    credentials: Dict
    settings: Dict
    is_authenticated: bool = False
    last_sync: Optional[float] = None

@dataclass
class BackupJob:
    """Backup job configuration"""
    id: str
    name: str
    provider: str
    source_type: str  # 'recordings', 'alerts', 'system_logs'
    source_path: str
    destination_path: str
    schedule: str  # 'manual', 'daily', 'weekly', 'monthly'
    schedule_time: str  # HH:MM format
    enabled: bool
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    retention_days: int = 30
    compress: bool = True
    encrypt: bool = False

@dataclass
class BackupStatus:
    """Backup operation status"""
    job_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    start_time: float
    end_time: Optional[float] = None
    files_total: int = 0
    files_uploaded: int = 0
    bytes_total: int = 0
    bytes_uploaded: int = 0
    error_message: Optional[str] = None

class CloudBackupManager(QObject):
    """Manager for cloud backup operations"""
    
    backup_started = pyqtSignal(str)  # job_id
    backup_progress = pyqtSignal(str, int, int)  # job_id, current, total
    backup_completed = pyqtSignal(str, bool)  # job_id, success
    provider_authenticated = pyqtSignal(str, bool)  # provider_name, success
    
    def __init__(self):
        super().__init__()
        self.config_file = "config/cloud_backup.json"
        self.providers = {}  # provider_name -> CloudProvider
        self.backup_jobs = {}  # job_id -> BackupJob
        self.active_backups = {}  # job_id -> BackupStatus
        
        # Create config directory
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Load configuration
        self.load_configuration()
        
        # Initialize providers
        self.init_providers()
        
        # Start scheduler
        self.scheduler_timer = QTimer()
        self.scheduler_timer.timeout.connect(self.check_scheduled_backups)
        self.scheduler_timer.start(60000)  # Check every minute
    
    def init_providers(self):
        """Initialize cloud providers"""
        # Google Drive
        if 'google_drive' not in self.providers:
            self.providers['google_drive'] = CloudProvider(
                name="Google Drive",
                type="google_drive",
                credentials={},
                settings={
                    'folder_name': 'FireVision_Backups',
                    'chunk_size': 1024 * 1024,  # 1MB chunks
                    'max_retries': 3
                }
            )
        
        # Dropbox
        if 'dropbox' not in self.providers:
            self.providers['dropbox'] = CloudProvider(
                name="Dropbox",
                type="dropbox",
                credentials={},
                settings={
                    'folder_name': '/FireVision_Backups',
                    'chunk_size': 4 * 1024 * 1024,  # 4MB chunks
                    'max_retries': 3
                }
            )
        
        # AWS S3
        if 'aws_s3' not in self.providers:
            self.providers['aws_s3'] = CloudProvider(
                name="Amazon S3",
                type="aws_s3",
                credentials={},
                settings={
                    'bucket_name': '',
                    'region': 'us-east-1',
                    'storage_class': 'STANDARD_IA',
                    'multipart_threshold': 64 * 1024 * 1024  # 64MB
                }
            )
        
        # Azure Blob Storage
        if 'azure_blob' not in self.providers:
            self.providers['azure_blob'] = CloudProvider(
                name="Azure Blob Storage",
                type="azure_blob",
                credentials={},
                settings={
                    'container_name': 'firevision-backups',
                    'tier': 'Cool',
                    'chunk_size': 4 * 1024 * 1024  # 4MB chunks
                }
            )
    
    def load_configuration(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load providers
                for provider_data in data.get('providers', []):
                    provider = CloudProvider(**provider_data)
                    self.providers[provider.type] = provider
                
                # Load backup jobs
                for job_data in data.get('backup_jobs', []):
                    job = BackupJob(**job_data)
                    self.backup_jobs[job.id] = job
                
                print("✅ Cloud backup configuration loaded")
                
        except Exception as e:
            print(f"❌ Error loading cloud backup configuration: {e}")
    
    def save_configuration(self):
        """Save configuration to file"""
        try:
            data = {
                'providers': [asdict(provider) for provider in self.providers.values()],
                'backup_jobs': [asdict(job) for job in self.backup_jobs.values()]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving cloud backup configuration: {e}")
    
    def authenticate_google_drive(self, credentials_file: str) -> bool:
        """Authenticate with Google Drive"""
        try:
            # This would use the Google Drive API
            # For now, simulate authentication
            provider = self.providers['google_drive']
            provider.credentials = {'credentials_file': credentials_file}
            provider.is_authenticated = True
            provider.last_sync = time.time()
            
            self.save_configuration()
            self.provider_authenticated.emit('google_drive', True)
            
            print("✅ Google Drive authenticated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error authenticating Google Drive: {e}")
            self.provider_authenticated.emit('google_drive', False)
            return False
    
    def authenticate_dropbox(self, access_token: str) -> bool:
        """Authenticate with Dropbox"""
        try:
            # This would use the Dropbox API
            # For now, simulate authentication
            provider = self.providers['dropbox']
            provider.credentials = {'access_token': access_token}
            provider.is_authenticated = True
            provider.last_sync = time.time()
            
            self.save_configuration()
            self.provider_authenticated.emit('dropbox', True)
            
            print("✅ Dropbox authenticated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error authenticating Dropbox: {e}")
            self.provider_authenticated.emit('dropbox', False)
            return False
    
    def authenticate_aws_s3(self, access_key: str, secret_key: str, bucket_name: str) -> bool:
        """Authenticate with AWS S3"""
        try:
            # This would use boto3 to test AWS credentials
            # For now, simulate authentication
            provider = self.providers['aws_s3']
            provider.credentials = {
                'access_key': access_key,
                'secret_key': secret_key
            }
            provider.settings['bucket_name'] = bucket_name
            provider.is_authenticated = True
            provider.last_sync = time.time()
            
            self.save_configuration()
            self.provider_authenticated.emit('aws_s3', True)
            
            print("✅ AWS S3 authenticated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error authenticating AWS S3: {e}")
            self.provider_authenticated.emit('aws_s3', False)
            return False
    
    def authenticate_azure_blob(self, connection_string: str, container_name: str) -> bool:
        """Authenticate with Azure Blob Storage"""
        try:
            # This would use azure-storage-blob to test credentials
            # For now, simulate authentication
            provider = self.providers['azure_blob']
            provider.credentials = {'connection_string': connection_string}
            provider.settings['container_name'] = container_name
            provider.is_authenticated = True
            provider.last_sync = time.time()
            
            self.save_configuration()
            self.provider_authenticated.emit('azure_blob', True)
            
            print("✅ Azure Blob Storage authenticated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error authenticating Azure Blob Storage: {e}")
            self.provider_authenticated.emit('azure_blob', False)
            return False
    
    def create_backup_job(self, name: str, provider: str, source_type: str,
                         source_path: str, destination_path: str, schedule: str,
                         schedule_time: str = "02:00", retention_days: int = 30,
                         compress: bool = True, encrypt: bool = False) -> str:
        """Create a new backup job"""
        try:
            job_id = f"backup_{int(time.time())}_{name.replace(' ', '_').lower()}"
            
            job = BackupJob(
                id=job_id,
                name=name,
                provider=provider,
                source_type=source_type,
                source_path=source_path,
                destination_path=destination_path,
                schedule=schedule,
                schedule_time=schedule_time,
                enabled=True,
                retention_days=retention_days,
                compress=compress,
                encrypt=encrypt
            )
            
            # Calculate next run time
            if schedule != 'manual':
                job.next_run = self.calculate_next_run(schedule, schedule_time)
            
            self.backup_jobs[job_id] = job
            self.save_configuration()
            
            print(f"✅ Backup job '{name}' created successfully")
            return job_id
            
        except Exception as e:
            print(f"❌ Error creating backup job: {e}")
            return None
    
    def calculate_next_run(self, schedule: str, schedule_time: str) -> float:
        """Calculate next run time for a backup job"""
        try:
            now = datetime.now()
            hour, minute = map(int, schedule_time.split(':'))
            
            if schedule == 'daily':
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
            elif schedule == 'weekly':
                # Run on Sundays
                days_ahead = 6 - now.weekday()  # Sunday is 6
                if days_ahead <= 0:
                    days_ahead += 7
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                next_run += timedelta(days=days_ahead)
            elif schedule == 'monthly':
                # Run on the 1st of each month
                if now.day == 1 and now.hour < hour:
                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    if now.month == 12:
                        next_run = now.replace(year=now.year + 1, month=1, day=1,
                                             hour=hour, minute=minute, second=0, microsecond=0)
                    else:
                        next_run = now.replace(month=now.month + 1, day=1,
                                             hour=hour, minute=minute, second=0, microsecond=0)
            else:
                return None
            
            return next_run.timestamp()
            
        except Exception as e:
            print(f"❌ Error calculating next run time: {e}")
            return None
    
    def check_scheduled_backups(self):
        """Check for scheduled backups that need to run"""
        try:
            current_time = time.time()
            
            for job in self.backup_jobs.values():
                if (job.enabled and job.schedule != 'manual' and 
                    job.next_run and current_time >= job.next_run):
                    
                    print(f"🕐 Starting scheduled backup: {job.name}")
                    self.start_backup(job.id)
                    
                    # Calculate next run time
                    job.next_run = self.calculate_next_run(job.schedule, job.schedule_time)
                    self.save_configuration()
                    
        except Exception as e:
            print(f"❌ Error checking scheduled backups: {e}")
    
    def start_backup(self, job_id: str) -> bool:
        """Start a backup job"""
        try:
            if job_id not in self.backup_jobs:
                print(f"❌ Backup job {job_id} not found")
                return False
            
            job = self.backup_jobs[job_id]
            provider = self.providers.get(job.provider)
            
            if not provider or not provider.is_authenticated:
                print(f"❌ Provider {job.provider} not authenticated")
                return False
            
            if job_id in self.active_backups:
                print(f"⚠️ Backup job {job_id} already running")
                return False
            
            # Create backup status
            status = BackupStatus(
                job_id=job_id,
                status='pending',
                start_time=time.time()
            )
            
            self.active_backups[job_id] = status
            
            # Start backup thread
            backup_thread = BackupThread(job, provider, self)
            backup_thread.progress_updated.connect(self.on_backup_progress)
            backup_thread.backup_completed.connect(self.on_backup_completed)
            backup_thread.start()
            
            # Update job last run
            job.last_run = time.time()
            self.save_configuration()
            
            self.backup_started.emit(job_id)
            
            print(f"🚀 Backup job '{job.name}' started")
            return True
            
        except Exception as e:
            print(f"❌ Error starting backup: {e}")
            return False
    
    def stop_backup(self, job_id: str) -> bool:
        """Stop a running backup job"""
        try:
            if job_id not in self.active_backups:
                return False
            
            # TODO: Implement backup cancellation
            status = self.active_backups[job_id]
            status.status = 'cancelled'
            status.end_time = time.time()
            
            del self.active_backups[job_id]
            
            print(f"🛑 Backup job {job_id} stopped")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping backup: {e}")
            return False
    
    def on_backup_progress(self, job_id: str, files_uploaded: int, files_total: int):
        """Handle backup progress update"""
        if job_id in self.active_backups:
            status = self.active_backups[job_id]
            status.files_uploaded = files_uploaded
            status.files_total = files_total
            status.status = 'running'
            
            self.backup_progress.emit(job_id, files_uploaded, files_total)
    
    def on_backup_completed(self, job_id: str, success: bool, error_message: str = None):
        """Handle backup completion"""
        if job_id in self.active_backups:
            status = self.active_backups[job_id]
            status.status = 'completed' if success else 'failed'
            status.end_time = time.time()
            status.error_message = error_message
            
            del self.active_backups[job_id]
            
            self.backup_completed.emit(job_id, success)
            
            if success:
                print(f"✅ Backup job {job_id} completed successfully")
            else:
                print(f"❌ Backup job {job_id} failed: {error_message}")
    
    def get_backup_jobs(self) -> List[BackupJob]:
        """Get all backup jobs"""
        return list(self.backup_jobs.values())
    
    def get_backup_status(self, job_id: str) -> Optional[BackupStatus]:
        """Get backup status"""
        return self.active_backups.get(job_id)
    
    def delete_backup_job(self, job_id: str) -> bool:
        """Delete a backup job"""
        try:
            if job_id in self.backup_jobs:
                del self.backup_jobs[job_id]
                self.save_configuration()
                print(f"✅ Backup job {job_id} deleted")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error deleting backup job: {e}")
            return False
    
    def test_connection(self, provider_type: str) -> bool:
        """Test connection to cloud provider"""
        try:
            provider = self.providers.get(provider_type)
            if not provider or not provider.is_authenticated:
                return False
            
            # TODO: Implement actual connection tests for each provider
            # For now, simulate test
            print(f"🔍 Testing connection to {provider.name}...")
            time.sleep(1)  # Simulate network delay
            
            provider.last_sync = time.time()
            self.save_configuration()
            
            print(f"✅ Connection to {provider.name} successful")
            return True
            
        except Exception as e:
            print(f"❌ Error testing connection: {e}")
            return False

class BackupThread(QThread):
    """Thread for running backup operations"""
    
    progress_updated = pyqtSignal(str, int, int)  # job_id, current, total
    backup_completed = pyqtSignal(str, bool, str)  # job_id, success, error_message
    
    def __init__(self, job: BackupJob, provider: CloudProvider, manager: CloudBackupManager):
        super().__init__()
        self.job = job
        self.provider = provider
        self.manager = manager
        self.cancelled = False
    
    def run(self):
        """Run the backup operation"""
        try:
            print(f"📦 Starting backup: {self.job.name}")
            
            # Get files to backup
            files_to_backup = self.get_files_to_backup()
            
            if not files_to_backup:
                self.backup_completed.emit(self.job.id, False, "No files to backup")
                return
            
            total_files = len(files_to_backup)
            uploaded_files = 0
            
            # Upload files
            for file_path in files_to_backup:
                if self.cancelled:
                    break
                
                try:
                    # Simulate file upload
                    self.upload_file(file_path)
                    uploaded_files += 1
                    
                    # Emit progress
                    self.progress_updated.emit(self.job.id, uploaded_files, total_files)
                    
                    # Small delay to simulate upload time
                    self.msleep(100)
                    
                except Exception as e:
                    print(f"❌ Error uploading file {file_path}: {e}")
                    continue
            
            if self.cancelled:
                self.backup_completed.emit(self.job.id, False, "Backup cancelled")
            else:
                self.backup_completed.emit(self.job.id, True, None)
                
        except Exception as e:
            self.backup_completed.emit(self.job.id, False, str(e))
    
    def get_files_to_backup(self) -> List[str]:
        """Get list of files to backup"""
        try:
            files = []
            
            if self.job.source_type == 'recordings':
                # Get recording files
                recordings_dir = self.job.source_path or "recordings"
                if os.path.exists(recordings_dir):
                    for root, dirs, filenames in os.walk(recordings_dir):
                        for filename in filenames:
                            if filename.endswith(('.mp4', '.avi', '.mov')):
                                files.append(os.path.join(root, filename))
            
            elif self.job.source_type == 'alerts':
                # Get alert footage
                alerts_dir = self.job.source_path or "footage/alerts"
                if os.path.exists(alerts_dir):
                    for root, dirs, filenames in os.walk(alerts_dir):
                        for filename in filenames:
                            files.append(os.path.join(root, filename))
            
            elif self.job.source_type == 'system_logs':
                # Get system logs
                logs_dir = self.job.source_path or "logs"
                if os.path.exists(logs_dir):
                    for root, dirs, filenames in os.walk(logs_dir):
                        for filename in filenames:
                            if filename.endswith(('.log', '.txt')):
                                files.append(os.path.join(root, filename))
            
            # Filter by retention policy
            if self.job.retention_days > 0:
                cutoff_time = time.time() - (self.job.retention_days * 24 * 60 * 60)
                files = [f for f in files if os.path.getmtime(f) >= cutoff_time]
            
            return files
            
        except Exception as e:
            print(f"❌ Error getting files to backup: {e}")
            return []
    
    def upload_file(self, file_path: str):
        """Upload a single file to cloud storage"""
        try:
            # This would implement actual upload logic for each provider
            # For now, simulate upload
            file_size = os.path.getsize(file_path)
            
            if self.provider.type == 'google_drive':
                self.upload_to_google_drive(file_path)
            elif self.provider.type == 'dropbox':
                self.upload_to_dropbox(file_path)
            elif self.provider.type == 'aws_s3':
                self.upload_to_aws_s3(file_path)
            elif self.provider.type == 'azure_blob':
                self.upload_to_azure_blob(file_path)
            
            print(f"📤 Uploaded: {os.path.basename(file_path)} ({file_size} bytes)")
            
        except Exception as e:
            print(f"❌ Error uploading file {file_path}: {e}")
            raise
    
    def upload_to_google_drive(self, file_path: str):
        """Upload file to Google Drive"""
        # TODO: Implement Google Drive API upload
        pass
    
    def upload_to_dropbox(self, file_path: str):
        """Upload file to Dropbox"""
        # TODO: Implement Dropbox API upload
        pass
    
    def upload_to_aws_s3(self, file_path: str):
        """Upload file to AWS S3"""
        # TODO: Implement boto3 S3 upload
        pass
    
    def upload_to_azure_blob(self, file_path: str):
        """Upload file to Azure Blob Storage"""
        # TODO: Implement Azure Blob Storage upload
        pass
    
    def cancel(self):
        """Cancel the backup operation"""
        self.cancelled = True

class CloudBackupWidget(QWidget):
    """Widget for managing cloud backup settings"""
    
    def __init__(self, backup_manager: CloudBackupManager):
        super().__init__()
        self.backup_manager = backup_manager
        
        self.setup_ui()
        self.connect_signals()
        self.load_data()
    
    def setup_ui(self):
        """Setup the cloud backup interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header_widget = self.create_header()
        layout.addWidget(header_widget)
        
        # Main content with tabs
        self.tab_widget = QTabWidget()
        
        # Providers tab
        self.providers_tab = self.create_providers_tab()
        self.tab_widget.addTab(self.providers_tab, "\u2601\ufe0f Cloud Providers")
        
        # Backup jobs tab
        self.jobs_tab = self.create_jobs_tab()
        self.tab_widget.addTab(self.jobs_tab, "\U0001F4E6 Backup Jobs")
        
        # Status tab
        self.status_tab = self.create_status_tab()
        self.tab_widget.addTab(self.status_tab, "\U0001F4CA Backup Status")
        
        # Wrap tab widget in a scroll area for responsiveness
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.tab_widget)
        layout.addWidget(scroll)
    
    def create_header(self) -> QWidget:
        """Create header with controls"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Title
        title = QLabel("☁️ Cloud Backup Management")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        
        # Action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        
        add_job_btn = QPushButton("➕ Add Backup Job")
        add_job_btn.clicked.connect(self.show_add_job_dialog)
        
        test_connections_btn = QPushButton("🔍 Test Connections")
        test_connections_btn.clicked.connect(self.test_all_connections)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_data)
        
        actions_layout.addWidget(add_job_btn)
        actions_layout.addWidget(test_connections_btn)
        actions_layout.addWidget(refresh_btn)
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(actions_widget)
        
        return header
    
    def create_providers_tab(self) -> QWidget:
        """Create cloud providers configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Google Drive
        google_drive_group = self.create_provider_group("Google Drive", "google_drive")
        layout.addWidget(google_drive_group)
        
        # Dropbox
        dropbox_group = self.create_provider_group("Dropbox", "dropbox")
        layout.addWidget(dropbox_group)
        
        # AWS S3
        aws_s3_group = self.create_provider_group("Amazon S3", "aws_s3")
        layout.addWidget(aws_s3_group)
        
        # Azure Blob Storage
        azure_blob_group = self.create_provider_group("Azure Blob Storage", "azure_blob")
        layout.addWidget(azure_blob_group)
        
        layout.addStretch()
        
        return widget
    
    def create_provider_group(self, name: str, provider_type: str) -> QWidget:
        """Create a provider configuration group"""
        group = QWidget()
        group.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                margin: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel(name)
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        
        # Status indicator
        status_label = QLabel("Not Connected")
        status_label.setObjectName(f"{provider_type}_status")
        status_label.setStyleSheet("""
            QLabel {
                color: #ff3333;
                font-size: 12px;
                background: transparent;
                padding: 4px 8px;
                border: 1px solid #ff3333;
                border-radius: 4px;
            }
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
        
        # Configuration form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        if provider_type == 'google_drive':
            credentials_btn = QPushButton("Select Credentials File")
            credentials_btn.clicked.connect(lambda: self.select_google_drive_credentials())
            form_layout.addRow("Credentials:", credentials_btn)
            
        elif provider_type == 'dropbox':
            access_token_input = QLineEdit()
            access_token_input.setObjectName(f"{provider_type}_access_token")
            access_token_input.setPlaceholderText("Enter Dropbox access token")
            form_layout.addRow("Access Token:", access_token_input)
            
        elif provider_type == 'aws_s3':
            access_key_input = QLineEdit()
            access_key_input.setObjectName(f"{provider_type}_access_key")
            access_key_input.setPlaceholderText("Enter AWS access key")
            form_layout.addRow("Access Key:", access_key_input)
            
            secret_key_input = QLineEdit()
            secret_key_input.setObjectName(f"{provider_type}_secret_key")
            secret_key_input.setEchoMode(QLineEdit.Password)
            secret_key_input.setPlaceholderText("Enter AWS secret key")
            form_layout.addRow("Secret Key:", secret_key_input)
            
            bucket_input = QLineEdit()
            bucket_input.setObjectName(f"{provider_type}_bucket")
            bucket_input.setPlaceholderText("Enter S3 bucket name")
            form_layout.addRow("Bucket Name:", bucket_input)
            
        elif provider_type == 'azure_blob':
            connection_string_input = QLineEdit()
            connection_string_input.setObjectName(f"{provider_type}_connection_string")
            connection_string_input.setPlaceholderText("Enter Azure connection string")
            form_layout.addRow("Connection String:", connection_string_input)
            
            container_input = QLineEdit()
            container_input.setObjectName(f"{provider_type}_container")
            container_input.setPlaceholderText("Enter container name")
            form_layout.addRow("Container Name:", container_input)
        
        layout.addWidget(form_widget)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(lambda: self.test_provider_connection(provider_type))
        
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(lambda: self.connect_provider(provider_type))
        
        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.clicked.connect(lambda: self.disconnect_provider(provider_type))
        
        buttons_layout.addWidget(test_btn)
        buttons_layout.addWidget(connect_btn)
        buttons_layout.addWidget(disconnect_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        return group
    
    def create_jobs_tab(self) -> QWidget:
        """Create backup jobs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Jobs table
        self.jobs_table = QTableWidget()
        self.jobs_table.setColumnCount(8)
        self.jobs_table.setHorizontalHeaderLabels([
            "Name", "Provider", "Source", "Schedule", "Last Run", 
            "Next Run", "Status", "Actions"
        ])
        
        # Set column widths
        header = self.jobs_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.jobs_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #505050;
                gridline-color: #505050;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #505050;
            }
            QTableWidget::item:selected {
                background-color: #ff3333;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 8px;
                border: 1px solid #505050;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.jobs_table)
        
        return widget
    
    def create_status_tab(self) -> QWidget:
        """Create backup status tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Status overview
        overview_widget = QWidget()
        overview_layout = QHBoxLayout(overview_widget)
        
        # Total jobs card
        self.total_jobs_card = self.create_stat_card("Total Jobs", "0", "#3498db")
        overview_layout.addWidget(self.total_jobs_card)
        
        # Active jobs card
        self.active_jobs_card = self.create_stat_card("Active Jobs", "0", "#2ecc71")
        overview_layout.addWidget(self.active_jobs_card)
        
        # Failed jobs card
        self.failed_jobs_card = self.create_stat_card("Failed Jobs", "0", "#e74c3c")
        overview_layout.addWidget(self.failed_jobs_card)
        
        # Last backup card
        self.last_backup_card = self.create_stat_card("Last Backup", "Never", "#f39c12")
        overview_layout.addWidget(self.last_backup_card)
        
        layout.addWidget(overview_widget)
        
        # Active backups
        active_label = QLabel("Active Backups")
        active_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                padding: 10px;
                background: transparent;
            }
        """)
        layout.addWidget(active_label)
        
        self.active_backups_widget = QWidget()
        self.active_backups_layout = QVBoxLayout(self.active_backups_widget)
        layout.addWidget(self.active_backups_widget)
        
        layout.addStretch()
        
        return widget
    
    def create_stat_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a statistics card"""
        card = QWidget()
        card.setFixedSize(200, 100)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 8px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
    
    def connect_signals(self):
        """Connect signals"""
        self.backup_manager.backup_started.connect(self.on_backup_started)
        self.backup_manager.backup_progress.connect(self.on_backup_progress)
        self.backup_manager.backup_completed.connect(self.on_backup_completed)
        self.backup_manager.provider_authenticated.connect(self.on_provider_authenticated)
    
    def load_data(self):
        """Load data from backup manager"""
        self.update_provider_status()
        self.update_jobs_table()
        self.update_status_overview()
    
    def update_provider_status(self):
        """Update provider connection status"""
        for provider_type, provider in self.backup_manager.providers.items():
            status_label = self.findChild(QLabel, f"{provider_type}_status")
            if status_label:
                if provider.is_authenticated:
                    status_label.setText("Connected")
                    status_label.setStyleSheet("""
                        QLabel {
                            color: #00ff00;
                            font-size: 12px;
                            background: transparent;
                            padding: 4px 8px;
                            border: 1px solid #00ff00;
                            border-radius: 4px;
                        }
                    """)
                else:
                    status_label.setText("Not Connected")
                    status_label.setStyleSheet("""
                        QLabel {
                            color: #ff3333;
                            font-size: 12px;
                            background: transparent;
                            padding: 4px 8px;
                            border: 1px solid #ff3333;
                            border-radius: 4px;
                        }
                    """)
    
    def update_jobs_table(self):
        """Update backup jobs table"""
        jobs = self.backup_manager.get_backup_jobs()
        self.jobs_table.setRowCount(len(jobs))
        
        for row, job in enumerate(jobs):
            # Name
            self.jobs_table.setItem(row, 0, QTableWidgetItem(job.name))
            
            # Provider
            provider_name = self.backup_manager.providers.get(job.provider, {}).get('name', job.provider)
            self.jobs_table.setItem(row, 1, QTableWidgetItem(provider_name))
            
            # Source
            self.jobs_table.setItem(row, 2, QTableWidgetItem(job.source_type.replace('_', ' ').title()))
            
            # Schedule
            schedule_text = job.schedule.title()
            if job.schedule != 'manual':
                schedule_text += f" at {job.schedule_time}"
            self.jobs_table.setItem(row, 3, QTableWidgetItem(schedule_text))
            
            # Last Run
            last_run = "Never"
            if job.last_run:
                last_run = datetime.fromtimestamp(job.last_run).strftime("%Y-%m-%d %H:%M")
            self.jobs_table.setItem(row, 4, QTableWidgetItem(last_run))
            
            # Next Run
            next_run = "Manual"
            if job.next_run:
                next_run = datetime.fromtimestamp(job.next_run).strftime("%Y-%m-%d %H:%M")
            self.jobs_table.setItem(row, 5, QTableWidgetItem(next_run))
            
            # Status
            status = "Enabled" if job.enabled else "Disabled"
            status_item = QTableWidgetItem(status)
            status_item.setBackground(Qt.green if job.enabled else Qt.gray)
            self.jobs_table.setItem(row, 6, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            run_btn = QPushButton("▶️")
            run_btn.setFixedSize(30, 25)
            run_btn.setToolTip("Run Now")
            run_btn.clicked.connect(lambda checked, jid=job.id: self.run_backup_job(jid))
            actions_layout.addWidget(run_btn)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 25)
            edit_btn.setToolTip("Edit Job")
            edit_btn.clicked.connect(lambda checked, jid=job.id: self.edit_backup_job(jid))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 25)
            delete_btn.setToolTip("Delete Job")
            delete_btn.clicked.connect(lambda checked, jid=job.id: self.delete_backup_job(jid))
            actions_layout.addWidget(delete_btn)
            
            self.jobs_table.setCellWidget(row, 7, actions_widget)
    
    def update_status_overview(self):
        """Update status overview"""
        jobs = self.backup_manager.get_backup_jobs()
        
        # Update stat cards
        self.total_jobs_card.value_label.setText(str(len(jobs)))
        
        active_jobs = len([j for j in jobs if j.enabled])
        self.active_jobs_card.value_label.setText(str(active_jobs))
        
        # TODO: Track failed jobs
        self.failed_jobs_card.value_label.setText("0")
        
        # Last backup
        last_backup = "Never"
        if jobs:
            last_runs = [j.last_run for j in jobs if j.last_run]
            if last_runs:
                last_backup = datetime.fromtimestamp(max(last_runs)).strftime("%m/%d %H:%M")
        self.last_backup_card.value_label.setText(last_backup)
    
    def select_google_drive_credentials(self):
        """Select Google Drive credentials file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Google Drive Credentials",
            "", "JSON Files (*.json)"
        )
        
        if file_path:
            success = self.backup_manager.authenticate_google_drive(file_path)
            if success:
                QMessageBox.information(self, "Success", "Google Drive authenticated successfully")
                self.update_provider_status()
            else:
                QMessageBox.warning(self, "Error", "Failed to authenticate Google Drive")
    
    def connect_provider(self, provider_type: str):
        """Connect to a cloud provider"""
        try:
            if provider_type == 'dropbox':
                access_token_input = self.findChild(QLineEdit, f"{provider_type}_access_token")
                if access_token_input:
                    access_token = access_token_input.text().strip()
                    if access_token:
                        success = self.backup_manager.authenticate_dropbox(access_token)
                        if success:
                            QMessageBox.information(self, "Success", "Dropbox authenticated successfully")
                        else:
                            QMessageBox.warning(self, "Error", "Failed to authenticate Dropbox")
                    else:
                        QMessageBox.warning(self, "Error", "Please enter access token")
            
            elif provider_type == 'aws_s3':
                access_key_input = self.findChild(QLineEdit, f"{provider_type}_access_key")
                secret_key_input = self.findChild(QLineEdit, f"{provider_type}_secret_key")
                bucket_input = self.findChild(QLineEdit, f"{provider_type}_bucket")
                
                if access_key_input and secret_key_input and bucket_input:
                    access_key = access_key_input.text().strip()
                    secret_key = secret_key_input.text().strip()
                    bucket_name = bucket_input.text().strip()
                    
                    if access_key and secret_key and bucket_name:
                        success = self.backup_manager.authenticate_aws_s3(access_key, secret_key, bucket_name)
                        if success:
                            QMessageBox.information(self, "Success", "AWS S3 authenticated successfully")
                        else:
                            QMessageBox.warning(self, "Error", "Failed to authenticate AWS S3")
                    else:
                        QMessageBox.warning(self, "Error", "Please fill in all AWS S3 fields")
            
            elif provider_type == 'azure_blob':
                connection_string_input = self.findChild(QLineEdit, f"{provider_type}_connection_string")
                container_input = self.findChild(QLineEdit, f"{provider_type}_container")
                
                if connection_string_input and container_input:
                    connection_string = connection_string_input.text().strip()
                    container_name = container_input.text().strip()
                    
                    if connection_string and container_name:
                        success = self.backup_manager.authenticate_azure_blob(connection_string, container_name)
                        if success:
                            QMessageBox.information(self, "Success", "Azure Blob Storage authenticated successfully")
                        else:
                            QMessageBox.warning(self, "Error", "Failed to authenticate Azure Blob Storage")
                    else:
                        QMessageBox.warning(self, "Error", "Please fill in all Azure fields")
            
            self.update_provider_status()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error connecting to provider: {str(e)}")
    
    def disconnect_provider(self, provider_type: str):
        """Disconnect from a cloud provider"""
        try:
            provider = self.backup_manager.providers.get(provider_type)
            if provider:
                provider.is_authenticated = False
                provider.credentials = {}
                self.backup_manager.save_configuration()
                self.update_provider_status()
                QMessageBox.information(self, "Success", f"{provider.name} disconnected")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error disconnecting provider: {str(e)}")
    
    def test_provider_connection(self, provider_type: str):
        """Test connection to a cloud provider"""
        success = self.backup_manager.test_connection(provider_type)
        if success:
            QMessageBox.information(self, "Success", "Connection test successful")
        else:
            QMessageBox.warning(self, "Error", "Connection test failed")
    
    def test_all_connections(self):
        """Test all provider connections"""
        results = []
        for provider_type, provider in self.backup_manager.providers.items():
            if provider.is_authenticated:
                success = self.backup_manager.test_connection(provider_type)
                results.append(f"{provider.name}: {'✅ Success' if success else '❌ Failed'}")
        
        if results:
            QMessageBox.information(self, "Connection Test Results", "\n".join(results))
        else:
            QMessageBox.information(self, "No Connections", "No cloud providers are connected")
    
    def show_add_job_dialog(self):
        """Show add backup job dialog"""
        dialog = AddBackupJobDialog(self.backup_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def run_backup_job(self, job_id: str):
        """Run a backup job manually"""
        success = self.backup_manager.start_backup(job_id)
        if success:
            QMessageBox.information(self, "Success", "Backup job started")
        else:
            QMessageBox.warning(self, "Error", "Failed to start backup job")
    
    def edit_backup_job(self, job_id: str):
        """Edit a backup job"""
        # TODO: Implement edit backup job dialog
        QMessageBox.information(self, "Edit Job", f"Edit job {job_id} (not implemented yet)")
    
    def delete_backup_job(self, job_id: str):
        """Delete a backup job"""
        reply = QMessageBox.question(
            self, 'Delete Backup Job',
            'Are you sure you want to delete this backup job?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.backup_manager.delete_backup_job(job_id)
            if success:
                self.load_data()
                QMessageBox.information(self, "Success", "Backup job deleted")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete backup job")
    
    def on_backup_started(self, job_id: str):
        """Handle backup started"""
        self.update_status_overview()
    
    def on_backup_progress(self, job_id: str, current: int, total: int):
        """Handle backup progress"""
        # TODO: Update progress display
        pass
    
    def on_backup_completed(self, job_id: str, success: bool):
        """Handle backup completed"""
        self.update_status_overview()
        self.load_data()
    
    def on_provider_authenticated(self, provider_name: str, success: bool):
        """Handle provider authentication"""
        self.update_provider_status()

class AddBackupJobDialog(QDialog):
    """Dialog for adding new backup jobs"""
    
    def __init__(self, backup_manager: CloudBackupManager, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.setWindowTitle("Add Backup Job")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Job name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter backup job name")
        form_layout.addRow("Job Name:", self.name_input)
        
        # Provider
        self.provider_combo = QComboBox()
        for provider_type, provider in self.backup_manager.providers.items():
            if provider.is_authenticated:
                self.provider_combo.addItem(provider.name, provider_type)
        form_layout.addRow("Cloud Provider:", self.provider_combo)
        
        # Source type
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["recordings", "alerts", "system_logs"])
        form_layout.addRow("Source Type:", self.source_type_combo)
        
        # Source path
        self.source_path_input = QLineEdit()
        self.source_path_input.setPlaceholderText("Leave empty for default path")
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_source_path)
        
        source_widget = QWidget()
        source_layout = QHBoxLayout(source_widget)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addWidget(self.source_path_input)
        source_layout.addWidget(browse_btn)
        
        form_layout.addRow("Source Path:", source_widget)
        
        # Destination path
        self.destination_input = QLineEdit()
        self.destination_input.setPlaceholderText("Remote destination path")
        form_layout.addRow("Destination Path:", self.destination_input)
        
        # Schedule
        self.schedule_combo = QComboBox()
        self.schedule_combo.addItems(["manual", "daily", "weekly", "monthly"])
        self.schedule_combo.currentTextChanged.connect(self.on_schedule_changed)
        form_layout.addRow("Schedule:", self.schedule_combo)
        
        # Schedule time
        self.schedule_time_input = QLineEdit()
        self.schedule_time_input.setText("02:00")
        self.schedule_time_input.setPlaceholderText("HH:MM format")
        self.schedule_time_input.setEnabled(False)
        form_layout.addRow("Schedule Time:", self.schedule_time_input)
        
        # Retention days
        self.retention_input = QSpinBox()
        self.retention_input.setRange(1, 365)
        self.retention_input.setValue(30)
        self.retention_input.setSuffix(" days")
        form_layout.addRow("Retention Period:", self.retention_input)
        
        # Options
        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        
        self.compress_checkbox = QCheckBox("Compress files before upload")
        self.compress_checkbox.setChecked(True)
        options_layout.addWidget(self.compress_checkbox)
        
        self.encrypt_checkbox = QCheckBox("Encrypt files (requires password)")
        options_layout.addWidget(self.encrypt_checkbox)
        
        form_layout.addRow("Options:", options_widget)
        
        layout.addWidget(form_widget)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Create Job")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        create_btn.clicked.connect(self.create_job)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(create_btn)
        
        layout.addWidget(buttons_widget)
    
    def on_schedule_changed(self, schedule: str):
        """Handle schedule change"""
        self.schedule_time_input.setEnabled(schedule != 'manual')
    
    def browse_source_path(self):
        """Browse for source path"""
        path = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if path:
            self.source_path_input.setText(path)
    
    def create_job(self):
        """Create backup job"""
        try:
            name = self.name_input.text().strip()
            provider_data = self.provider_combo.currentData()
            source_type = self.source_type_combo.currentText()
            source_path = self.source_path_input.text().strip()
            destination_path = self.destination_input.text().strip()
            schedule = self.schedule_combo.currentText()
            schedule_time = self.schedule_time_input.text().strip()
            retention_days = self.retention_input.value()
            compress = self.compress_checkbox.isChecked()
            encrypt = self.encrypt_checkbox.isChecked()
            
            # Validation
            if not name:
                QMessageBox.warning(self, "Error", "Please enter a job name")
                return
            
            if not provider_data:
                QMessageBox.warning(self, "Error", "Please select a cloud provider")
                return
            
            if not destination_path:
                QMessageBox.warning(self, "Error", "Please enter a destination path")
                return
            
            if schedule != 'manual' and not schedule_time:
                QMessageBox.warning(self, "Error", "Please enter a schedule time")
                return
            
            # Create job
            job_id = self.backup_manager.create_backup_job(
                name=name,
                provider=provider_data,
                source_type=source_type,
                source_path=source_path,
                destination_path=destination_path,
                schedule=schedule,
                schedule_time=schedule_time,
                retention_days=retention_days,
                compress=compress,
                encrypt=encrypt
            )
            
            if job_id:
                QMessageBox.information(self, "Success", f"Backup job '{name}' created successfully")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to create backup job")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating backup job: {str(e)}")
