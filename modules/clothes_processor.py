import cv2

class ClothesProcessor:  
    def __init__(self):
        self.clothes_image = None
        self.video_processing_enabled = False
    
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
    
    def process_video_frame(self, frame):
        cv2.putText(
            frame, 
            "Processed", 
            (20, 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255, 0), 
            2
        )
               
        return frame
    
    def is_processing_enabled(self):
        return self.video_processing_enabled