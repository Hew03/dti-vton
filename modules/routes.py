from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
import json
import cv2
import numpy as np
import base64
import os
import uuid

from .video_track import ClothesVideoTrack

def setup_routes(app, pcs, ml_model, upload_dir):
    app.router.add_get("/", index)
    
    app.router.add_post("/offer", lambda request: offer(request, pcs, ml_model))
    app.router.add_post("/process-clothes-image", lambda request: process_clothes_image(request, ml_model, upload_dir))

async def index(request):
    return web.FileResponse('./templates/index.html')

async def offer(request, pcs, ml_model):
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

    @pc.on("track")
    def on_track(track):
        print(f"Track received: {track.kind}")
        if track.kind == "video":
            print("Adding processed video track")
            ml_track = ClothesVideoTrack(track, ml_model)
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

async def process_clothes_image(request, ml_model, upload_dir):
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
        
        image_path = os.path.join(upload_dir, f"{uuid.uuid4()}.jpg")
        cv2.imwrite(image_path, image)
        
        processed_image = ml_model.process_single_image(image)
        
        ml_model.set_clothes_image(image)
        
        _, buffer = cv2.imencode('.jpg', processed_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        processed_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "processedImage": f"data:image/jpeg;base64,{processed_b64}",
                "success": True
            })
        )
    except Exception as e:
        print(f"Error processing image: {e}")
        return web.Response(
            status=500,
            text=json.dumps({"error": str(e)}),
            content_type="application/json"
        )