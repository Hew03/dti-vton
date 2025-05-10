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
        Clothing image is passed but not used in actual processing
        """
        # Create a horizontally flipped version of the frame
        result = cv2.flip(frame, 1)  # 1 for horizontal flip
        
        # Add text to show this is try-on result
        cv2.putText(result, "Try-On Result", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add clothing name if available (simulated)
        cv2.putText(result, "Clothing applied!", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
        
        return result