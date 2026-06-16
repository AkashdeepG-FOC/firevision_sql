from fastapi import APIRouter
from datetime import datetime
from backend_client import backend_client
from sync.queue_manager import QueueManager
# from database.local_db import LocalDB

router = APIRouter()
queue_manager = QueueManager()

@router.get("/status")
def get_system_status():
    """
    Returns the real-time connectivity status of the system.
    """
    # 1. Check cloud API connection
    cloud_connected = backend_client.test_connection()
    internet = cloud_connected  # We assume internet is true if cloud is reachable for now
    
    # 2. Get pending sync queue size
    # We fetch with a high limit just to count, or we could add a get_queue_size() to QueueManager
    pending_events = queue_manager.get_pending_events(limit=1000)
    sync_pending = len(pending_events)
    
    # 3. Determine Mode
    if not cloud_connected:
        mode = "offline"
    elif cloud_connected and sync_pending > 0:
        mode = "syncing"
    else:
        # We could add more nuanced checks for 'limited' here if latency is high, 
        # but for simplicity, if connected and queue is 0 -> online
        mode = "online"
        
    return {
        "mode": mode,
        "internet": internet,
        "cloud_connected": cloud_connected,
        "sync_pending": sync_pending,
        "last_sync": datetime.now().isoformat(),  # Placeholder, should fetch from DB
        "api_latency": 0, # Placeholder
        "token_valid": True, # Placeholder, depends on auth manager state
        "queue_size": sync_pending,
        "cameras_online": 0,
        "cameras_total": 0
    }
