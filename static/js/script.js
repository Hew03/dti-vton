const webcamVideo = document.getElementById('webcam');
const processedVideo = document.getElementById('processed');
const statusDiv = document.getElementById('status');

let pc;
let webcamStream;

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

// Start application
start();

// Cleanup on exit
window.addEventListener('beforeunload', () => {
    if (pc) pc.close();
    if (webcamStream) webcamStream.getTracks().forEach(track => track.stop());
});