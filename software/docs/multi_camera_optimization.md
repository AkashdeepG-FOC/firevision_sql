# Multi-Camera AI Inference Optimization Guide

This document outlines a production-ready architecture designed to optimize CPU usage when running the unchanged FireVision YOLO models on Intel i3 hardware with multiple cameras.

## Core Architectural Concepts

To efficiently support 1-2 concurrent cameras on lower-end hardware (Intel i3 with 8GB RAM), the architecture uses a strict separation of concerns, heavily relying on multithreading and queues:

### 1. Separation of Capture and Inference (Producer/Consumer Pattern)
A common issue in AI vision pipelines is that video frame capturing (`cv2.VideoCapture.read()`) blocks the CPU. By separating them:
- **Frame Grabber Threads (Producers):** One thread per camera purely dedicated to pulling frames from the stream as quickly as possible and dropping them into a queue of size 1 (always keeping only the freshest frame).
- **Inference Workers (Consumers):** Independent workers that pull the latest frame from the queue, preventing inference latency from "backing up" the video stream (latency leads to RTSP stream corruption or lag).

### 2. Frame Skipping and Detection Intervals
Running inference on 30 FPS video is unnecessary for fire detection since fire/smoke spreads relatively slowly in the context of milliseconds.
- **Interval Control:** Instead of processing every frame, the inference worker pulls a frame exactly every `X` seconds (e.g., 1.0 seconds).
- **Result Caching:** During the frames where inference is skipped, the system uses the cached bounding boxes from the last successful detection. This gives the illusion of real-time 30 FPS tracking while heavily reducing CPU cycles.

### 3. Pre-Inference Resizing
High-resolution frames (e.g., 1080p or 4K) drastically slow down convolutional neural network operations. 
- Downscale the frame dimensions (e.g., to 640x640 or proportional dimensions like 640x360 depending on the model's preferred aspect ratio) *before* passing it into the model execution layer. 
- You then map the coordinates of the returned bounding boxes back to the original resolution for drawing.

## See the Example Code
An optimized implementation utilizing these patterns has been added to this project repository:
`d:\giit\firevision_sql\software\examples\optimized_pipeline.py`
