import cv2
import time

class ClothesProcessor:  
    def __init__(self):
        self.clothes_image = None
        self.video_processing_enabled = False
        self.processing_time = 0.1  # Default processing time in seconds (100ms)
        self.last_frame_time = time.time()
        self.input_fps = 0
        self.output_fps = 0
        self.fps_update_time = time.time()
        self.input_frame_count = 0
        self.output_frame_count = 0
    
    def set_clothes_image(self, image):
        self.clothes_image = image
        self.video_processing_enabled = True
        return True
        
    def process_single_image(self, image):      
        cv2.putText(
            image, 
            "Processed", 
            (20, 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255, 0), 
            2
        )
            
        return image
    
    def update_fps_stats(self, is_input=True):
        current_time = time.time()
        
        # Update frame counts
        if is_input:
            self.input_frame_count += 1
        else:
            self.output_frame_count += 1
        
        # Calculate FPS every second
        if current_time - self.fps_update_time >= 1.0:
            time_diff = current_time - self.fps_update_time
            self.input_fps = self.input_frame_count / time_diff
            self.output_fps = self.output_frame_count / time_diff
            
            # Reset counters
            self.fps_update_time = current_time
            self.input_frame_count = 0
            self.output_frame_count = 0
    
    def process_video_frame(self, frame):
        # Update input FPS
        self.update_fps_stats(is_input=True)
        
        current_time = time.time()
        
        # Check if enough time has passed since the last processed frame
        # If processing is too slow, we'll skip frames to maintain responsiveness
        if current_time - self.last_frame_time < self.processing_time:
            # Not enough time has passed, skip processing this frame
            return None
        
        # Simulate model inference time
        time.sleep(self.processing_time)
        
        # Update last frame time
        self.last_frame_time = time.time()
        
        # Add FPS information to the frame
        cv2.putText(
            frame, 
            f"Input FPS: {self.input_fps:.1f}", 
            (20, 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 0), 
            2
        )
        
        cv2.putText(
            frame, 
            f"Output FPS: {self.output_fps:.1f}", 
            (20, 80), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 0), 
            2
        )
        
        cv2.putText(
            frame, 
            f"Process time: {self.processing_time*1000:.0f}ms", 
            (20, 120), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 0), 
            2
        )
        
        # Update output FPS
        self.update_fps_stats(is_input=False)
               
        return frame
    
    def is_processing_enabled(self):
        return self.video_processing_enabled