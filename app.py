from flask import Flask, request, render_template
import os
import base64
import uuid
import cv2
import numpy as np
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store WebRTC connections
connections = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)
    if request.sid in connections:
        del connections[request.sid]

@socketio.on('offer')
def handle_offer(data):
    connections[request.sid] = data['offer']
    socketio.emit('offer', {'offer': data['offer']}, room=request.sid)

@socketio.on('answer')
def handle_answer(data):
    connections[request.sid] = data['answer']
    socketio.emit('answer', {'answer': data['answer']}, room=request.sid)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    socketio.emit('ice_candidate', {'candidate': data['candidate']}, room=request.sid)

@socketio.on('process_frame')
def handle_process_frame(data):
    try:
        # Decode base64 image
        img_data = base64.b64decode(data['frame'].split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Flip the frame horizontally (mirror effect)
        flipped_frame = cv2.flip(frame, 1)
        
        # Encode back to base64
        _, buffer = cv2.imencode('.jpg', flipped_frame)
        flipped_frame_data = base64.b64encode(buffer).decode('utf-8')
        
        socketio.emit('processed_frame', {
            'frame': f'data:image/jpeg;base64,{flipped_frame_data}',
            'timestamp': data['timestamp']
        }, room=request.sid)
    except Exception as e:
        print('Error processing frame:', e)

@socketio.on('upload_garment')
def handle_garment_upload(data):
    try:
        # Decode base64 image
        img_data = base64.b64decode(data['image'].split(',')[1])
        filename = f"garment_{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_data)
        
        socketio.emit('garment_uploaded', {'path': filepath}, room=request.sid)
    except Exception as e:
        print('Error processing garment:', e)
        socketio.emit('upload_error', {'error': str(e)}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)