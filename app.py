from flask import Flask, request, jsonify, render_template
import os
import cv2
import numpy as np
import time
import base64

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# TODO: Load or configure your model here (local or Vertex AI)
# e.g. model = load_local_model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('garment')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return jsonify({'status': 'ok', 'path': filepath})

@app.route('/process_frame', methods=['POST'])
def process_frame():
    # Simulate backend processing delay
    time.sleep(0.15)  # ~150ms per frame

    # Receive base64 frame and garment path
    data = request.get_json()
    frame_b64 = data.get('frame', '')
    garment_path = data.get('garment_path')

    # Decode frame
    img_data = base64.b64decode(frame_b64)
    img_array = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # TODO: Call your model here; for now, simulate a simple processing (e.g., flip horizontally)
    processed = cv2.flip(frame, 1)

    # Encode back to JPEG
    _, jpeg = cv2.imencode('.jpg', processed)
    return jsonify({'frame': base64.b64encode(jpeg.tobytes()).decode('utf-8')})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)