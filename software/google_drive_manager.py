import os
import io
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from PyQt5.QtCore import QObject, pyqtSignal, QThread

# Constants for file paths and scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_secret_502421975806-rohri82oac9k7htqlabd2ekjp284c6ig.apps.googleusercontent.com.json'  # make sure this matches your downloaded file name
TOKEN_FILE = 'token.json'


class GoogleDriveUploadThread(QThread):
    upload_progress = pyqtSignal(int)  # Progress percentage
    upload_completed = pyqtSignal(str, str)  # file_id, file_name
    upload_error = pyqtSignal(str)  # error_message

    def __init__(self, service, file_path, file_name, folder_id=None):
        super().__init__()
        self.service = service
        self.file_path = file_path
        self.file_name = file_name
        self.folder_id = folder_id

    def run(self):
        try:
            file_metadata = {'name': self.file_name}
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]

            media = MediaFileUpload(self.file_path, resumable=True)
            request = self.service.files().create(body=file_metadata, media_body=media, fields='id')

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    self.upload_progress.emit(progress)

            file_id = response.get('id')
            self.upload_completed.emit(file_id, self.file_name)

        except Exception as e:
            self.upload_error.emit(str(e))


class GoogleDriveManager(QObject):
    authentication_required = pyqtSignal()
    authentication_completed = pyqtSignal(bool)  # success
    upload_started = pyqtSignal(str)  # file_name
    upload_progress = pyqtSignal(str, int)  # file_name, progress
    upload_completed = pyqtSignal(str, str, str)  # file_name, file_id, drive_url
    upload_error = pyqtSignal(str, str)  # file_name, error

    def __init__(self):
        super().__init__()
        self.service = None
        self.creds = None
        self.recordings_folder_id = None
        self.upload_threads = {}

    def authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            if os.path.exists(TOKEN_FILE):
                self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                    self.creds = flow.run_local_server(port=0)

                with open(TOKEN_FILE, 'w') as token:
                    token.write(self.creds.to_json())

            self.service = build('drive', 'v3', credentials=self.creds)

            self._setup_recordings_folder()

            self.authentication_completed.emit(True)
            return True

        except Exception as e:
            print(f"Authentication error: {e}")
            self.authentication_completed.emit(False)
            return False

    def _setup_recordings_folder(self):
        """Create or find the recordings folder in Google Drive"""
        try:
            query = "name='Fire Vision Pro Recordings' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()

            folders = results.get('files', [])
            if folders:
                self.recordings_folder_id = folders[0]['id']
                print(f"Found existing recordings folder: {self.recordings_folder_id}")
            else:
                folder_metadata = {
                    'name': 'Fire Vision Pro Recordings',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                self.recordings_folder_id = folder.get('id')
                print(f"Created new recordings folder: {self.recordings_folder_id}")

        except Exception as e:
            print(f"Error setting up recordings folder: {e}")

    def upload_recording(self, file_path, camera_name):
        """Upload a recording to Google Drive"""
        try:
            if not self.service:
                self.upload_error.emit(os.path.basename(file_path), "Not authenticated with Google Drive")
                return False

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{camera_name}_{timestamp}.mp4"

            upload_thread = GoogleDriveUploadThread(self.service, file_path, file_name, self.recordings_folder_id)

            # Use default argument trick to capture current file_name in lambda
            upload_thread.upload_progress.connect(
                lambda progress, fn=file_name: self.upload_progress.emit(fn, progress)
            )
            upload_thread.upload_completed.connect(
                lambda file_id, name=file_name, path=file_path: self._on_upload_completed(file_id, name, path)
            )
            upload_thread.upload_error.connect(
                lambda error, fn=file_name: self.upload_error.emit(fn, error)
            )

            self.upload_threads[file_name] = upload_thread

            self.upload_started.emit(file_name)
            upload_thread.start()

            return True

        except Exception as e:
            self.upload_error.emit(os.path.basename(file_path), str(e))
            return False

    def _on_upload_completed(self, file_id, file_name, local_path):
        drive_url = f"https://drive.google.com/file/d/{file_id}/view"
        self.upload_completed.emit(file_name, file_id, drive_url)

        if file_name in self.upload_threads:
            del self.upload_threads[file_name]

        try:
            os.remove(local_path)
            print(f"Local file deleted: {local_path}")
        except Exception as e:
            print(f"Error deleting local file: {e}")

    def get_recordings_list(self):
        """Get list of recordings from Google Drive"""
        try:
            if not self.service:
                return []

            query = f"'{self.recordings_folder_id}' in parents and (mimeType contains 'video/' or name contains '.mp4' or name contains '.avi') and trashed=false"

            results = self.service.files().list(
                q=query,
                fields="files(id, name, size, createdTime, webViewLink)",
                orderBy="createdTime desc"
            ).execute()

            files = results.get('files', [])
            recordings = []
            for file in files:
                recordings.append({
                    'id': file['id'],
                    'name': file['name'],
                    'size': int(file.get('size', 0)),
                    'created_time': file['createdTime'],
                    'web_view_link': file['webViewLink'],
                    'download_link': f"https://drive.google.com/uc?id={file['id']}&export=download"
                })

            return recordings

        except Exception as e:
            print(f"Error getting recordings list: {e}")
            return []

    def download_recording(self, file_id, save_path):
        """Download a recording from Google Drive"""
        try:
            if not self.service:
                return False

            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            with open(save_path, 'wb') as f:
                f.write(file_io.getvalue())

            return True

        except Exception as e:
            print(f"Error downloading recording: {e}")
            return False

    def delete_recording(self, file_id):
        """Delete a recording from Google Drive"""
        try:
            if not self.service:
                return False

            self.service.files().delete(fileId=file_id).execute()
            return True

        except Exception as e:
            print(f"Error deleting recording: {e}")
            return False

    def is_authenticated(self):
        """Check if authenticated with Google Drive"""
        return self.service is not None
