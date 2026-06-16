import time
import requests
from PyQt5.QtCore import QThread, pyqtSignal

class SystemStatusWorker(QThread):
    """
    Background worker that polls the local FastAPI status endpoint
    every 3 seconds and emits the result to the UI.
    """
    status_updated = pyqtSignal(dict)
    
    def __init__(self, endpoint_url="http://127.0.0.1:8001/api/local/system/status", interval=3):
        super().__init__()
        self.endpoint_url = endpoint_url
        self.interval = interval
        self.is_running = True
        
    def run(self):
        while self.is_running:
            try:
                response = requests.get(self.endpoint_url, timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    self.status_updated.emit(data)
                else:
                    self._emit_offline()
            except Exception:
                self._emit_offline()
                
            time.sleep(self.interval)
            
    def _emit_offline(self):
        """Emit an offline status if the local API is unreachable."""
        self.status_updated.emit({
            "mode": "offline",
            "internet": False,
            "cloud_connected": False,
            "sync_pending": 0,
            "queue_size": 0
        })
        
    def stop(self):
        self.is_running = False
        self.wait()
