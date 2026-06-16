from fastapi import FastAPI
import uvicorn
import threading

from local_api.routers import auth, system

app = FastAPI(title="FireVision Local API", description="Local API for FireVision Offline Storage and Auth")

app.include_router(auth.router, prefix="/api/local/auth", tags=["auth"])
app.include_router(system.router, prefix="/api/local/system", tags=["system"])
# app.include_router(sync.router, prefix="/api/local/sync", tags=["sync"])
# app.include_router(queue.router, prefix="/api/local/queue", tags=["queue"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "FireVision Local API"}

def start_local_api_server(port=8001):
    """Run the FastAPI server in a background thread."""
    def run():
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")
        
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
