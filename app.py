from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import cv2
import numpy as np
import json
import asyncio
import os
import base64
import uuid
from av import VideoFrame

# Create uploads directory if it doesn't exist
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = web.Application()
pcs = set()  # Track active peer connections

# Global state
reference_image = None
video_processing_enabled = False

class MLProcessor:
    def __init__(self):
        self.reference_image = None
    
    def set_reference_image(self, image):
        self.reference_image = image
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

ml_model = MLProcessor()

class HighQualityVideoTrack(VideoStreamTrack):
    def __init__(self, track):
        super().__init__()
        self.track = track
        self._last_frame = None
        
    async def recv(self):
        try:
            frame = await self.track.recv()
            
            if not video_processing_enabled:
                return frame
            
            img = frame.to_ndarray(format="bgr24")
            
            processed_img = ml_model.process_video_frame(img)
            
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

async def offer(request):
    global video_processing_enabled
    
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    
    # Check if video processing should be enabled
    if "videoEnabled" in params:
        video_processing_enabled = params["videoEnabled"]
        print(f"Video processing set to: {video_processing_enabled}")

    pc = RTCPeerConnection()
    pcs.add(pc)
    print("New peer connection created")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print(f"ICE connection state is {pc.iceConnectionState}")
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # Add video track when client sends video
    @pc.on("track")
    def on_track(track):
        print(f"Track received: {track.kind}")
        if track.kind == "video":
            print("Adding processed video track")
            ml_track = HighQualityVideoTrack(track)
            pc.addTrack(ml_track)

    await pc.setRemoteDescription(offer)
    print("Remote description set")
    
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    print("Local description set")

    return web.Response(
        content_type="application/json",
        text=json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }),
    )

async def process_image(request):
    try:
        params = await request.json()
        image_data = params["image"]
        
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        image_binary = base64.b64decode(image_data)
        
        nparr = np.frombuffer(image_binary, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return web.Response(
                status=400,
                text=json.dumps({"error": "Invalid image data"}),
                content_type="application/json"
            )
        
        processed_image = ml_model.process_single_image(image)
        
        _, buffer = cv2.imencode('.jpg', processed_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        processed_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "processedImage": f"data:image/jpeg;base64,{processed_b64}"
            })
        )
    except Exception as e:
        print(f"Error processing image: {e}")
        return web.Response(
            status=500,
            text=json.dumps({"error": str(e)}),
            content_type="application/json"
        )

async def set_reference_image(request):
    global reference_image
    
    try:
        params = await request.json()
        image_data = params["image"]
        
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        image_binary = base64.b64decode(image_data)
        
        nparr = np.frombuffer(image_binary, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return web.Response(
                status=400,
                text=json.dumps({"error": "Invalid image data"}),
                content_type="application/json"
            )
        
        image_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.jpg")
        cv2.imwrite(image_path, image)
        
        reference_image = image
        ml_model.set_reference_image(image)
        
        global video_processing_enabled
        video_processing_enabled = True
        
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "success": True,
                "message": "Reference image set successfully"
            })
        )
    except Exception as e:
        print(f"Error setting reference image: {e}")
        return web.Response(
            status=500,
            text=json.dumps({"error": str(e)}),
            content_type="application/json"
        )

async def index(request):
    return web.FileResponse('./templates/index.html')

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

app.router.add_get("/", index)
app.router.add_post("/offer", offer)
app.router.add_post("/process-image", process_image)
app.router.add_post("/set-reference-image", set_reference_image)
app.router.add_static("/static/", path="./static", name="static")
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=8080)