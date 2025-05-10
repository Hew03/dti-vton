import cv2
import time
import random

class ClothesProcessor:  
    def __init__(self):
        self.clothes_image = None
        self.video_processing_enabled = False
        self.last_frame_time = time.time()
        self.actual_processing_time = 0
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
        if is_input:
            self.input_frame_count += 1
        else:
            self.output_frame_count += 1
        if current_time - self.fps_update_time >= 1.0:
            time_diff = current_time - self.fps_update_time
            self.input_fps = self.input_frame_count / time_diff
            self.output_fps = self.output_frame_count / time_diff
            self.fps_update_time = current_time
            self.input_frame_count = 0
            self.output_frame_count = 0
    
    def process_video_frame(self, frame):
        self.update_fps_stats(is_input=True)
        current_time = time.time()
        if current_time - self.last_frame_time < self.actual_processing_time:
            return None
        
        process_start_time = time.time()
        time.sleep(random.uniform(0.01, 0.05))
        self.actual_processing_time = time.time() - process_start_time

        self.last_frame_time = time.time()
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
            f"Process time: {self.actual_processing_time*1000:.0f}ms", 
            (20, 120), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 0), 
            2
        )
        self.update_fps_stats(is_input=False)
        return frame
    
    def is_processing_enabled(self):
        return self.video_processing_enabled
