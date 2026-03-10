import asyncio
import numpy as np
import cv2
from typing import Dict, List, Tuple
from inference import YoloEngine

class BatchScheduler:
    def __init__(self, batch_size=4, max_wait_ms=50):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.queue = asyncio.Queue()
        self.engine = YoloEngine()
        self.callbacks: Dict[str, asyncio.Queue] = {}
        self._running = False
        self.task = None

    def register_client(self, camera_id: str):
        if camera_id not in self.callbacks:
            self.callbacks[camera_id] = asyncio.Queue()
        return self.callbacks[camera_id]

    def unregister_client(self, camera_id: str):
        if camera_id in self.callbacks:
            del self.callbacks[camera_id]

    async def add_frame(self, camera_id: str, frame_bytes: bytes):
        await self.queue.put((camera_id, frame_bytes))

    async def _process_batch(self):
        while self._running:
            batch = []
            try:
                # Wait for the first frame
                item = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                batch.append(item)
                
                # Try to fill the rest of the batch quickly
                while len(batch) < self.batch_size:
                    try:
                        item = await asyncio.wait_for(self.queue.get(), timeout=self.max_wait_ms / 1000.0)
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break
                
                if batch:
                    camera_ids = [b[0] for b in batch]
                    frames_bytes = [b[1] for b in batch]
                    
                    decoded_frames = []
                    valid_indices = []
                    
                    for i, b in enumerate(frames_bytes):
                        np_arr = np.frombuffer(b, np.uint8)
                        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                        if img is not None:
                            decoded_frames.append(img)
                            valid_indices.append(i)
                    
                    if decoded_frames:
                        # Run inference in thread pool to prevent blocking asyncio event loop
                        results = await asyncio.to_thread(self.engine.predict_batch, decoded_frames)
                        
                        # Dispatch results
                        for i, res in enumerate(results):
                            orig_idx = valid_indices[i]
                            cam_id = camera_ids[orig_idx]
                            
                            if cam_id in self.callbacks:
                                # Send result
                                await self.callbacks[cam_id].put({
                                    "camera_id": cam_id,
                                    "detections": res
                                })
                                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error in batch processing: {e}")

    async def start(self):
        self._running = True
        self.task = asyncio.create_task(self._process_batch())

    async def stop(self):
        self._running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

scheduler = BatchScheduler()
