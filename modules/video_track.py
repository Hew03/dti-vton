from aiortc import VideoStreamTrack
from av import VideoFrame

class ClothesVideoTrack(VideoStreamTrack):
    def __init__(self, track, processor):
        super().__init__()
        self.track = track
        self.processor = processor
        self._last_frame = None
        
    async def recv(self):
        try:
            frame = await self.track.recv()
            
            if not self.processor.is_processing_enabled():
                return frame
            
            img = frame.to_ndarray(format="bgr24")
            
            processed_img = self.processor.process_video_frame(img)
            
            if processed_img is None:
                if self._last_frame:
                    return self._last_frame
                return frame
    
            new_frame = VideoFrame.from_ndarray(processed_img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            
            self._last_frame = new_frame
            return new_frame
            
        except Exception as e:
            print(f"Error in video processing: {e}")
            
            if self._last_frame:
                return self._last_frame
            return frame