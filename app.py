from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import cv2
import numpy as np
import uuid
import json
import os
from av import VideoFrame

app = web.Application()
pcs = set()  # Track active peer connections

# ML Processing (Replace with your model)
class MLProcessor:
    def process(self, frame):
        """Example: Flip frame + placeholder for ML"""
        processed = cv2.flip(frame, 1)
        # Add your ML processing here
        return processed

ml_model = MLProcessor()

class MLVideoTrack(VideoStreamTrack):
    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")
        
        # Process frame with ML
        processed_img = ml_model.process(img)
        
        new_frame = VideoFrame.from_ndarray(processed_img, format="bgr24")
        new_frame.pts = frame.pts
        return new_frame

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # Add ML track when client sends video
    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            ml_track = MLVideoTrack(track)
            pc.addTrack(ml_track)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

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
    for pc in pcs:
        await pc.close()

app.router.add_get("/", index)
app.router.add_post("/offer", offer)
app.router.add_static("/static/", path="./static", name="static")
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=8080)