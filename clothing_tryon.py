import cv2
import numpy as np
from PIL import Image
import threading
import time
from models import ClothingTryOnModel

class ClothingProcessor:
    def __init__(self):
        self.model = ClothingTryOnModel()
        self.clothing_image = None
        self.processing = False
        self.capture = None
        self.processed_frame = None
        self.original_frame = None
        self.processing_thread = None
        self.running = False
        self.clothing_loaded = False  # Flag to track if clothing has been loaded
    
    def start_camera(self, camera_index=0):
        """Start the webcam capture"""
        self.capture = cv2.VideoCapture(camera_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_frames)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def stop_camera(self):
        """Stop the webcam capture and processing"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        if self.capture:
            self.capture.release()
            
    def set_clothing(self, clothing_path):
        """Set the clothing image and mark as loaded"""
        try:
            clothing_img = cv2.imread(clothing_path)
            if clothing_img is not None:
                self.clothing_image = clothing_img
                self.clothing_loaded = True  # Mark that clothing is loaded
                return True
            return False
        except Exception as e:
            print(f"Error loading clothing image: {e}")
            return False
    
    def _process_frames(self):
        """Process frames from webcam in a separate thread"""
        while self.running:
            if self.capture is None or not self.capture.isOpened():
                time.sleep(0.1)
                continue
                
            ret, frame = self.capture.read()
            if not ret:
                continue
                
            # Store the original frame
            self.original_frame = frame.copy()
            
            # Process the frame only if clothing is loaded
            if self.clothing_loaded:
                self.processed_frame = self.model.process_frame(frame, self.clothing_image)
            else:
                # If no clothing loaded yet, processed frame is same as original
                self.processed_frame = frame.copy()
                
            time.sleep(0.01)  # Small sleep to prevent CPU overuse