import cv2
import numpy as np
import time

class ClothingTryOnModel:
    """
    Simplified model that just flips the video frame
    """
    def __init__(self):
        # No need for face cascade or other ML models
        pass
        
    def process_frame(self, frame, clothing_image):
        """
        Process a frame by simply flipping it horizontally
        No face detection or clothing overlay
        """
        # Create a horizontally flipped version of the frame
        result = cv2.flip(frame, 1)  # 1 for horizontal flip
        
        # Add text to show this is the processed frame
        cv2.putText(result, "Processed: Flipped Frame", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return result