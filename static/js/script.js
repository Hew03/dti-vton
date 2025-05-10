document.addEventListener('DOMContentLoaded', function() {
    const webcamVideo = document.getElementById('webcam');
    const processedVideo = document.getElementById('processed');
    const statusDiv = document.getElementById('status');
    const imageUploadInput = document.getElementById('image-upload');
    const originalPreview = document.getElementById('original-preview');
    const processedPreview = document.getElementById('processed-preview');
    const processingIndicator = document.getElementById('processing-indicator');
    const fileUpload = document.querySelector('.file-upload');

    let pc;
    let webcamStream;
    let originalImage = null;
    let videoStarted = false;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileUpload.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        fileUpload.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileUpload.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        fileUpload.style.borderColor = 'var(--primary-color)';
        fileUpload.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
    }
    
    function unhighlight() {
        fileUpload.style.borderColor = '#e2e8f0';
        fileUpload.style.backgroundColor = '#f8fafc';
    }
    
    fileUpload.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            imageUploadInput.files = files;
            handleFileSelect(files[0]);
        }
    }

    imageUploadInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        handleFileSelect(file);
    });
    
    function handleFileSelect(file) {
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
    }

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
            
            updateStatus("Image processed successfully", "connected");
            
            if (!videoStarted) {
                await startVideoProcessing();
            }
            
            hideProcessingIndicator();
        } catch (err) {
            processedPreview.innerHTML = '<span>Processing failed</span>';
            updateStatus(`Error: ${err.message}`, "disconnected");
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
            updateStatus("Video processing started", "connected");
        } catch (err) {
            updateStatus(`Error starting video: ${err.message}`, "disconnected");
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
                updateStatus("Connected to video processing", "connected");
            } else if (pc.iceConnectionState === "failed" || pc.iceConnectionState === "disconnected") {
                updateStatus("Video connection failed", "disconnected");
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
            updateStatus(`Setup error: ${err.message}`, "disconnected");
        }
    }

    function showProcessingIndicator() {
        processingIndicator.style.display = 'flex';
    }

    function hideProcessingIndicator() {
        processingIndicator.style.display = 'none';
    }
    
    function updateStatus(message, className) {
        statusDiv.textContent = message;
        statusDiv.className = className;
        
        statusDiv.style.transform = 'scale(1.05)';
        setTimeout(() => {
            statusDiv.style.transform = 'scale(1)';
        }, 300);
    }

    window.addEventListener('beforeunload', () => {
        if (pc) pc.close();
        if (webcamStream) webcamStream.getTracks().forEach(track => track.stop());
    });
});