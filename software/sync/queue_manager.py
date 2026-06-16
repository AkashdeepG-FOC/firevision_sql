import time
import json
import uuid
from database.local_db import LocalDB
from auth.key_manager import KeyManager

class QueueManager:
    """Manages the local SQLite queue for offline events."""
    
    PRIORITIES = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}
    
    def __init__(self):
        self.db = LocalDB()
        
    def enqueue(self, event_type: str, payload: dict, priority: str = "MEDIUM"):
        """Add an event to the sync queue."""
        event_uuid = str(uuid.uuid4())
        # Encrypt the payload before storing
        encrypted_payload = KeyManager.encrypt_data(json.dumps(payload))
        
        query = """
        INSERT INTO sync_queue (event_uuid, type, payload, timestamp, priority, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
        """
        self.db.execute_query(query, (event_uuid, event_type, encrypted_payload, time.time(), priority))
        return event_uuid
        
    def get_pending_events(self, limit: int = 50):
        """Get pending events, ordered by priority and timestamp."""
        # SQLite doesn't natively sort our string priorities optimally, so we fetch and sort in Python
        # Or we map priority string to integer in DB, but fetching all pending and sorting is fine for local.
        query = "SELECT * FROM sync_queue WHERE status = 'pending' ORDER BY timestamp ASC LIMIT ?"
        rows = self.db.fetch_all(query, (limit * 2,)) # Fetch more to sort by priority
        
        events = []
        for row in rows:
            try:
                decrypted_payload = json.loads(KeyManager.decrypt_data(row['payload']))
                events.append({
                    "event_uuid": row['event_uuid'],
                    "type": row['type'],
                    "payload": decrypted_payload,
                    "timestamp": row['timestamp'],
                    "retry_count": row['retry_count'],
                    "priority": row['priority']
                })
            except Exception as e:
                print(f"Error decrypting queue item {row['event_uuid']}: {e}")
                # Mark as corrupted/failed
                self.update_status(row['event_uuid'], "corrupted")
                
        # Sort by Priority (1 is highest) then Timestamp
        events.sort(key=lambda x: (self.PRIORITIES.get(x['priority'], 99), x['timestamp']))
        return events[:limit]
        
    def update_status(self, event_uuid: str, status: str):
        """Update the status of a queue item (synced, failed, pending)."""
        self.db.execute_query("UPDATE sync_queue SET status = ? WHERE event_uuid = ?", (status, event_uuid))
        
    def increment_retry(self, event_uuid: str):
        """Increment the retry counter for an event."""
        self.db.execute_query("UPDATE sync_queue SET retry_count = retry_count + 1 WHERE event_uuid = ?", (event_uuid,))
        
    def delete_event(self, event_uuid: str):
        """Remove an event from the queue after successful sync."""
        self.db.execute_query("DELETE FROM sync_queue WHERE event_uuid = ?", (event_uuid,))
