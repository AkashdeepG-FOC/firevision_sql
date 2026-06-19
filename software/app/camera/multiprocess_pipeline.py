import multiprocessing as mp
import cv2
import time
import queue

def camera_capture_process(camera_id, rtsp_url, frame_queue, stop_event):
    """
    Subprocess for camera ingestion to fully bypass the GIL.
    Captures frames and feeds them into a shared queue.
    """
    print(f"🎥 Started capture process for camera {camera_id}")
    cap = cv2.VideoCapture(rtsp_url)
    
    # Set buffer size to minimize latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print(f"⚠️ Reconnecting camera {camera_id}...")
            time.sleep(2)
            cap.open(rtsp_url)
            continue
            
        # Push latest frame to queue, drop old frames if queue is full
        try:
            if frame_queue.full():
                try:
                    frame_queue.get_nowait()  # Discard old frame
                except queue.Empty:
                    pass
            frame_queue.put_nowait((camera_id, frame, time.time()))
        except Exception as e:
            print(f"Error putting frame in queue: {e}")
            
    cap.release()
    print(f"🛑 Capture process for camera {camera_id} stopped.")

class MultiProcessCameraManager:
    """
    GIL-bypassing Multi-process Camera Ingestion Manager.
    Spawns isolated processes per camera stream and processes alerts asynchronously.
    """
    def __init__(self):
        self.processes = {}
        self.queues = {}
        self.stop_events = {}

    def start_camera(self, camera_id: str, rtsp_url: str):
        if camera_id in self.processes:
            print(f"Camera {camera_id} is already running.")
            return
            
        # Force queue limit of 2 to guarantee real-time feed processing
        self.queues[camera_id] = mp.Queue(maxsize=2)
        self.stop_events[camera_id] = mp.Event()
        
        proc = mp.Process(
            target=camera_capture_process, 
            args=(camera_id, rtsp_url, self.queues[camera_id], self.stop_events[camera_id])
        )
        proc.daemon = True
        self.processes[camera_id] = proc
        proc.start()

    def get_latest_frame(self, camera_id: str):
        if camera_id not in self.queues:
            return None
            
        try:
            # Non-blocking retrieval of frame
            return self.queues[camera_id].get_nowait()
        except queue.Empty:
            return None

    def stop_camera(self, camera_id: str):
        if camera_id in self.stop_events:
            self.stop_events[camera_id].set()
        if camera_id in self.processes:
            self.processes[camera_id].join(timeout=2)
            if self.processes[camera_id].is_alive():
                self.processes[camera_id].terminate()
            del self.processes[camera_id]
        if camera_id in self.queues:
            del self.queues[camera_id]
        if camera_id in self.stop_events:
            del self.stop_events[camera_id]

    def stop_all(self):
        for cid in list(self.processes.keys()):
            self.stop_camera(cid)
