import psutil
from database.local_db import LocalDB

class HealthMonitor:
    """Monitors system health and sync queue size for the local dashboard."""
    
    @staticmethod
    def get_health_metrics() -> dict:
        try:
            db = LocalDB()
            # Count pending queue items
            queue_row = db.fetch_one("SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'")
            queue_size = queue_row['count'] if queue_row else 0
            
            # System stats
            cpu_usage = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "queue_size": queue_size,
                "cpu_percent": cpu_usage,
                "memory_percent": mem.percent,
                "disk_percent": disk.percent
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
