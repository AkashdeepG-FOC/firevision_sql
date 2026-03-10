import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from scheduler import scheduler
import uvicorn
import json

app = FastAPI(title="FireVision Detection Service")

@app.on_event("startup")
async def startup_event():
    await scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    await scheduler.stop()

@app.websocket("/ws/detect/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    result_queue = scheduler.register_client(camera_id)
    
    async def send_results():
        try:
            while True:
                result = await result_queue.get()
                await websocket.send_text(json.dumps(result))
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"Error sending results to {camera_id}: {e}")
            
    # Start sender task
    sender_task = asyncio.create_task(send_results())
    
    try:
        while True:
            # Receive frame as bytes (JPEG encoded)
            frame_bytes = await websocket.receive_bytes()
            await scheduler.add_frame(camera_id, frame_bytes)
    except WebSocketDisconnect:
        print(f"Client {camera_id} disconnected")
    finally:
        sender_task.cancel()
        scheduler.unregister_client(camera_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
