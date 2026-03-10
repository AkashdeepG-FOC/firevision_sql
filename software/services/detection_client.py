import asyncio
import json
import cv2
import websockets
import threading

from utils.logger import logger

class DetectionClient:
    """
    WebSocket client to send video frames to the detection microservice
    and receive detection bounding boxes asynchronously.
    """
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.callbacks = {}
        self.websockets = {}
        self.loop = None
        self.thread = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("DetectionClient background thread started.")

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop(self):
        self._running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread and self.thread.is_alive():
            self.thread.join()
        logger.info("DetectionClient background thread stopped.")

    def register_camera(self, camera_id, callback):
        """
        Register a callback for when detections are received for a specific camera.
        """
        self.callbacks[camera_id] = callback
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._connect_ws(camera_id), self.loop)
        logger.info(f"Registered detection camera callback for {camera_id}")

    def unregister_camera(self, camera_id):
        """
        Unregister a camera from AI detection.
        """
        if camera_id in self.callbacks:
            del self.callbacks[camera_id]
        if camera_id in self.websockets:
            ws = self.websockets[camera_id]
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(ws.close(), self.loop)
            del self.websockets[camera_id]
        logger.info(f"Unregistered detection camera {camera_id}")

    async def _connect_ws(self, camera_id):
        uri = f"ws://{self.host}:{self.port}/ws/detect/{camera_id}"
        retry_count = 0
        while self._running and camera_id in self.callbacks:
            try:
                async with websockets.connect(uri) as websocket:
                    self.websockets[camera_id] = websocket
                    retry_count = 0
                    logger.info(f"Connected to Detection Service WS for {camera_id}")
                    while self._running:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if camera_id in self.callbacks:
                            self.callbacks[camera_id](data.get("detections", []))
            except Exception as e:
                logger.error(f"WebSocket error for {camera_id}: {e}")
                
            self.websockets.pop(camera_id, None)
            retry_count += 1
            await asyncio.sleep(min(2 ** retry_count, 30))

    def send_frame(self, camera_id, frame):
        """
        Sends frame to detection service over WebSocket. 
        `frame` is a numpy array (BGR).
        """
        if camera_id in self.websockets and self.loop:
            ws = self.websockets[camera_id]
            # JPEG encode at 80% to save bandwidth while retaining enough quality for YOLO
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if success:
                asyncio.run_coroutine_threadsafe(ws.send(buffer.tobytes()), self.loop)
