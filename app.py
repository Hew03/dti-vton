from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, MediaStreamTrack
import cv2
import asyncio
import json
from av import VideoFrame

app = web.Application()
pcs = set()  # Track active peer connections

# ML Processing
class MLProcessor:
    def process(self, frame):
        """Example: Flip frame + placeholder for ML"""
        processed = cv2.flip(frame, 1)
        return processed

ml_model = MLProcessor()

class MLVideoTrack(VideoStreamTrack):
    def __init__(self, track):
        super().__init__()
        self.track = track
        self.counter = 0
        self._last_frame = None

    async def recv(self):
        try:
            frame = await self.track.recv()
            self.counter += 1
            
            # Process the frame with ML
            img = frame.to_ndarray(format="bgr24")
            processed_img = ml_model.process(img)
            
            # Create a new frame from the processed image
            new_frame = VideoFrame.from_ndarray(processed_img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            
            self._last_frame = new_frame
            return new_frame
        except Exception as e:
            print(f"Error in video processing: {e}")
            # Return last frame if available, or original frame as fallback
            if self._last_frame:
                return self._last_frame
            return frame

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

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

    video_sender = None

    # Add ML track when client sends video
    @pc.on("track")
    def on_track(track):
        print(f"Track received: {track.kind}")
        if track.kind == "video":
            print("Adding ML video track")
            ml_track = MLVideoTrack(track)
            video_sender = pc.addTrack(ml_track)

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

async def index(request):
    return web.FileResponse('./templates/index.html')

async def on_shutdown(app):
    # Close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

app.router.add_get("/", index)
app.router.add_post("/offer", offer)
app.router.add_static("/static/", path="./static", name="static")
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=8080)