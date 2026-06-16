import threading
import time
from backend_client import backend_client
from sync.queue_manager import QueueManager
from sync.retry_handler import RetryHandler

class SyncManager:
    """
    Background service that monitors internet connectivity and synchronizes 
    offline events with the Cloud API when online.
    """
    def __init__(self):
        self.queue_manager = QueueManager()
        self.is_running = False
        self.thread = None
        self._lock = threading.Lock()
        
    def start(self):
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self.thread = threading.Thread(target=self._sync_loop, daemon=True)
                self.thread.start()
                
    def stop(self):
        with self._lock:
            self.is_running = False
            
    def _sync_loop(self):
        """Main loop for the background sync thread."""
        while self.is_running:
            try:
                # 1. Check Internet Connectivity (Ping own API)
                if backend_client.test_connection():
                    self._process_queue()
                    # Sleep shorter if online but queue empty, 
                    # though if queue has items we process them in bulk.
                    time.sleep(5)
                else:
                    # Offline: wait before checking again
                    time.sleep(10)
            except Exception as e:
                print(f"Error in sync loop: {e}")
                time.sleep(10) # Fallback sleep on unexpected error
                
    def _process_queue(self):
        """Fetch pending events and push to Cloud API."""
        events = self.queue_manager.get_pending_events(limit=20)
        
        for event in events:
            # Check retry backoff
            # For simplicity in this structure, we use the timestamp as a proxy for last attempt,
            # or we'd need a separate last_attempt column. We'll simulate backoff sleep here or skip.
            # In a robust implementation, we'd check if we should skip this event based on last_attempt.
            
            # Attempt to sync
            success = self._push_event_to_cloud(event)
            
            if success:
                self.queue_manager.delete_event(event['event_uuid'])
            else:
                self.queue_manager.increment_retry(event['event_uuid'])
                self.queue_manager.update_status(event['event_uuid'], 'pending')
                
    def _push_event_to_cloud(self, event: dict) -> bool:
        """Route the event to the correct backend_client endpoint."""
        try:
            event_type = event['type']
            payload = event['payload']
            
            if event_type == "fire_alert":
                # Assuming payload matches create_alert signature
                res = backend_client.create_alert(**payload)
                return res is not None
            elif event_type == "camera_config":
                res = backend_client.create_camera(**payload)
                return res is not None
            # Handle other event types (logs, users, etc.)
            else:
                print(f"Unknown event type: {event_type}")
                return True # Delete unknown events so they don't block queue
                
        except Exception as e:
            print(f"Failed to push event {event['event_uuid']} to cloud: {e}")
            return False
