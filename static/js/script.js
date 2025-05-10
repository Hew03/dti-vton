document.addEventListener('DOMContentLoaded', function() {
    const webcamVideo = document.getElementById('webcam');
    const processedVideo = document.getElementById('processed');
    const statusDiv = document.getElementById('status');
    const imageUploadInput = document.getElementById('image-upload');
    const originalPreview = document.getElementById('original-preview');
    const processedPreview = document.getElementById('processed-preview');
    const processingIndicator = document.getElementById('processing-indicator');

    let pc;
    let webcamStream;
    let originalImage = null;
    let videoStarted = false;

    imageUploadInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        showProcessingIndicator();
        statusDiv.textContent = "Processing clothing image...";
        statusDiv.className = "pending";
        
        const reader = new FileReader();
        reader.onload = function(event) {
            originalImage = event.target.result;
            originalPreview.innerHTML = `<img src="${originalImage}" alt="Clothing Image">`;
            
            processClothingImage(originalImage);
        };
        reader.readAsDataURL(file);
    });

    async function processClothingImage(imageData) {
        try {
            const response = await fetch('/process-clothes-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: imageData })
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const result = await response.json();
            
            processedPreview.innerHTML = `<img src="${result.processedImage}" alt="Processed Clothing">`;
            
            statusDiv.textContent = "Image processed successfully";
            statusDiv.className = "connected";
            
            if (!videoStarted) {
                await startVideoProcessing();
            }
            
            hideProcessingIndicator();
        } catch (err) {
            processedPreview.innerHTML = '<span>Processing failed</span>';
            statusDiv.textContent = `Error: ${err.message}`;
            statusDiv.className = "disconnected";
            console.error(err);
            hideProcessingIndicator();
        }
    }

    async function startVideoProcessing() {
        try {
            if (!webcamStream) {
                webcamStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { width: 640, height: 480 },
                    audio: false 
                });
                webcamVideo.srcObject = webcamStream;
            }
            
            await setupWebRTC();
            
            videoStarted = true;
            statusDiv.textContent = "Video processing started";
            statusDiv.className = "connected";
        } catch (err) {
            statusDiv.textContent = `Error starting video: ${err.message}`;
            statusDiv.className = "disconnected";
            console.error(err);
        }
    }

    async function setupWebRTC() {
        pc = new RTCPeerConnection({
            iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
        });

        pc.oniceconnectionstatechange = () => {
            console.log("ICE connection state:", pc.iceConnectionState);
            if (pc.iceConnectionState === "connected" || pc.iceConnectionState === "completed") {
                statusDiv.textContent = "Connected to video processing";
                statusDiv.className = "connected";
            } else if (pc.iceConnectionState === "failed" || pc.iceConnectionState === "disconnected") {
                statusDiv.textContent = "Video connection failed";
                statusDiv.className = "disconnected";
            }
        };
        
        webcamStream.getTracks().forEach(track => {
            pc.addTrack(track, webcamStream);
        });

        pc.ontrack = (event) => {
            console.log("Received remote track:", event.track.kind);
            if (event.track.kind === 'video') {
                const remoteStream = new MediaStream([event.track]);
                processedVideo.srcObject = remoteStream;
                
                processedVideo.play().catch(err => {
                    console.error("Error playing processed video:", err);
                });
            }
        };

        try {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            console.log("Created and set local description");

            const response = await fetch('/offer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sdp: pc.localDescription.sdp,
                    type: pc.localDescription.type
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

    function showProcessingIndicator() {
        processingIndicator.style.display = 'block';
    }

    function hideProcessingIndicator() {
        processingIndicator.style.display = 'none';
    }

    window.addEventListener('beforeunload', () => {
        if (pc) pc.close();
        if (webcamStream) webcamStream.getTracks().forEach(track => track.stop());
    });
});