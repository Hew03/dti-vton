const webcamVideo = document.getElementById('webcam');
const processedVideo = document.getElementById('processed');
const statusDiv = document.getElementById('status');
const imageUploadInput = document.getElementById('image-upload');
const originalPreview = document.getElementById('original-preview');
const processedPreview = document.getElementById('processed-preview');
const processImageBtn = document.getElementById('process-image');
const applyToVideoBtn = document.getElementById('apply-to-video');

let pc;
let webcamStream;
let originalImage = null;
let processedImage = null;
let videoEnabled = false;

// Handle image upload
imageUploadInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Display original image preview
    const reader = new FileReader();
    reader.onload = function(event) {
        originalImage = event.target.result;
        originalPreview.innerHTML = `<img src="${originalImage}" alt="Original Image">`;
        processImageBtn.disabled = false;
    };
    reader.readAsDataURL(file);
});

// Process the uploaded image
processImageBtn.addEventListener('click', async function() {
    if (!originalImage) return;
    
    // Show loading state
    processedPreview.innerHTML = '<span>Processing...</span>';
    
    try {
        // Send image to server for processing
        const response = await fetch('/process-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: originalImage })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        processedImage = result.processedImage;
        
        // Display processed image
        processedPreview.innerHTML = `<img src="${processedImage}" alt="Processed Image">`;
        applyToVideoBtn.disabled = false;
        
        statusDiv.textContent = "Image processed successfully";
        statusDiv.className = "connected";
    } catch (err) {
        processedPreview.innerHTML = '<span>Processing failed</span>';
        statusDiv.textContent = `Error: ${err.message}`;
        statusDiv.className = "disconnected";
        console.error(err);
    }
});

// Apply to video feed
applyToVideoBtn.addEventListener('click', async function() {
    if (!processedImage) return;
    
    // Enable video processing
    videoEnabled = true;
    
    // Tell the server to use this image for video processing
    try {
        const response = await fetch('/set-reference-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: originalImage })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        // Start webcam if not already started
        if (!webcamStream) {
            await start();
        }
        
        statusDiv.textContent = "Applied to video feed";
        statusDiv.className = "connected";
    } catch (err) {
        statusDiv.textContent = `Error: ${err.message}`;
        statusDiv.className = "disconnected";
        console.error(err);
    }
});

async function start() {
    try {
        // Get webcam access
        webcamStream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 },
            audio: false 
        });
        webcamVideo.srcObject = webcamStream;
        
        // Setup WebRTC
        await setupWebRTC();
        
        statusDiv.textContent = "Connecting...";
        statusDiv.className = "pending";
    } catch (err) {
        statusDiv.textContent = `Error: ${err.message}`;
        statusDiv.className = "disconnected";
        console.error(err);
    }
}

async function setupWebRTC() {
    pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    // Monitor connection state
    pc.oniceconnectionstatechange = () => {
        console.log("ICE connection state:", pc.iceConnectionState);
        if (pc.iceConnectionState === "connected" || pc.iceConnectionState === "completed") {
            statusDiv.textContent = "Connected (WebRTC)";
            statusDiv.className = "connected";
        } else if (pc.iceConnectionState === "failed" || pc.iceConnectionState === "disconnected") {
            statusDiv.textContent = "Connection failed";
            statusDiv.className = "disconnected";
        }
    };
    
    // Add webcam tracks
    webcamStream.getTracks().forEach(track => {
        pc.addTrack(track, webcamStream);
    });

    // Handle incoming processed video stream
    pc.ontrack = (event) => {
        console.log("Received remote track:", event.track.kind);
        if (event.track.kind === 'video') {
            // Create a MediaStream to hold the received track
            const remoteStream = new MediaStream([event.track]);
            processedVideo.srcObject = remoteStream;
            
            // Ensure video starts playing
            processedVideo.play().catch(err => {
                console.error("Error playing processed video:", err);
            });
        }
    };

    // Create and send offer
    try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        console.log("Created and set local description");

        const response = await fetch('/offer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sdp: pc.localDescription.sdp,
                type: pc.localDescription.type,
                videoEnabled: videoEnabled
            })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const answer = await response.json();
        console.log("Received answer from server");
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
        console.log("Set remote description");
    } catch (err) {
        console.error("WebRTC setup error:", err);
        statusDiv.textContent = `Setup error: ${err.message}`;
        statusDiv.className = "disconnected";
    }
}

// Cleanup on exit
window.addEventListener('beforeunload', () => {
    if (pc) pc.close();
    if (webcamStream) webcamStream.getTracks().forEach(track => track.stop());
});