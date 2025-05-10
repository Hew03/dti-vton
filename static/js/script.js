const video = document.getElementById('video');
const localCanvas = document.getElementById('local-canvas');
const localCtx = localCanvas.getContext('2d');
const processedCanvas = document.getElementById('processed-canvas');
const processedCtx = processedCanvas.getContext('2d');
const previewImg = document.getElementById('garment-preview');
const statusDiv = document.getElementById('status');
let garmentPath = null;
let peerConnection = null;
let dataChannel = null;

// FPS tracking variables
let localFps = 0;
let remoteFps = 0;
let localFrameCount = 0;
let remoteFrameCount = 0;
let lastFpsUpdate = 0;

// Frame processing variables
let processingFrame = false;
const targetFps = 30;
const frameInterval = 1000 / targetFps;
let lastFrameTime = 0;

// Connect to WebSocket server
const socket = io();

// WebRTC configuration
const configuration = {
  iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
};

// Status updates
socket.on('connect', () => {
  statusDiv.textContent = 'Connected to server';
  statusDiv.className = 'connected';
});

socket.on('disconnect', () => {
  statusDiv.textContent = 'Disconnected from server';
  statusDiv.className = 'disconnected';
});

// Start webcam feed
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
    video.addEventListener('loadedmetadata', () => {
      localCanvas.width = video.videoWidth;
      localCanvas.height = video.videoHeight;
      processedCanvas.width = video.videoWidth;
      processedCanvas.height = video.videoHeight;
      
      // Start local video rendering
      renderLocalVideo();
      
      // Start frame processing
      startFrameProcessing();
      
      // Setup WebRTC
      setupWebRTC(stream);
    });
  })
  .catch(err => {
    console.error('Error accessing webcam:', err);
    statusDiv.textContent = 'Webcam error: ' + err.message;
    statusDiv.className = 'disconnected';
  });

// Render local video feed
function renderLocalVideo() {
  function draw() {
    localCtx.drawImage(video, 0, 0, localCanvas.width, localCanvas.height);
    localFrameCount++;
    requestAnimationFrame(draw);
  }
  draw();
}

// Frame processing functions
function startFrameProcessing() {
  function process() {
    const now = Date.now();
    if (now - lastFrameTime >= frameInterval) {
      captureAndSendFrame();
      lastFrameTime = now;
    }
    requestAnimationFrame(process);
  }
  process();
}

function captureAndSendFrame() {
  if (processingFrame) return;
  
  processingFrame = true;
  
  // Capture frame from local canvas
  const frameData = localCanvas.toDataURL('image/jpeg', 0.7);
  socket.emit('process_frame', {
    frame: frameData,
    timestamp: Date.now()
  });
  
  processingFrame = false;
}

// Handle processed frames from server
socket.on('processed_frame', data => {
  const img = new Image();
  img.onload = () => {
    processedCtx.drawImage(img, 0, 0, processedCanvas.width, processedCanvas.height);
    remoteFrameCount++;
  };
  img.src = data.frame;
});

// FPS counter
function updateFpsDisplay() {
  const now = performance.now();
  if (now - lastFpsUpdate >= 1000) {
    document.getElementById('local-fps').textContent = `Local FPS: ${localFps}`;
    document.getElementById('remote-fps').textContent = `Processed FPS: ${remoteFps}`;
    
    localFps = localFrameCount;
    remoteFps = remoteFrameCount;
    localFrameCount = 0;
    remoteFrameCount = 0;
    lastFpsUpdate = now;
  }
  requestAnimationFrame(updateFpsDisplay);
}
updateFpsDisplay();

// WebRTC setup
function setupWebRTC(localStream) {
  peerConnection = new RTCPeerConnection(configuration);

  localStream.getTracks().forEach(track => {
    peerConnection.addTrack(track, localStream);
  });

  dataChannel = peerConnection.createDataChannel('garmentData');
  dataChannel.onopen = () => console.log('Data channel opened');
  dataChannel.onclose = () => console.log('Data channel closed');

  peerConnection.ontrack = event => {
    console.log('Received remote stream');
  };

  peerConnection.onicecandidate = event => {
    if (event.candidate) {
      socket.emit('ice_candidate', { candidate: event.candidate });
    }
  };

  // WebSocket signaling
  socket.on('offer', async data => {
    try {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);
      socket.emit('answer', { answer: answer });
    } catch (err) {
      console.error('Error handling offer:', err);
    }
  });

  socket.on('answer', async data => {
    try {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
    } catch (err) {
      console.error('Error handling answer:', err);
    }
  });

  socket.on('ice_candidate', async data => {
    try {
      await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
    } catch (e) {
      console.error('Error adding ICE candidate:', e);
    }
  });

  // Start connection
  peerConnection.createOffer()
    .then(offer => peerConnection.setLocalDescription(offer))
    .then(() => {
      socket.emit('offer', { offer: peerConnection.localDescription });
    })
    .catch(err => {
      console.error('Error creating offer:', err);
      statusDiv.textContent = 'WebRTC error: ' + err.message;
      statusDiv.className = 'disconnected';
    });
}

// Garment upload handling
document.getElementById('upload').addEventListener('change', e => {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(evt) {
    previewImg.src = evt.target.result;
    socket.emit('upload_garment', { image: evt.target.result });
  };
  reader.readAsDataURL(file);
});

socket.on('garment_uploaded', data => {
  garmentPath = data.path;
  console.log('Garment uploaded to:', garmentPath);
  
  if (dataChannel && dataChannel.readyState === 'open') {
    dataChannel.send(JSON.stringify({ type: 'garment_update', path: garmentPath }));
  }
});

socket.on('upload_error', data => {
  console.error('Upload error:', data.error);
  alert('Error uploading garment: ' + data.error);
});