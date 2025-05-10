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
        
        statusDiv.textContent = "Connected (WebRTC)";
        statusDiv.className = "connected";
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

    // Add webcam tracks
    webcamStream.getTracks().forEach(track => {
        pc.addTrack(track, webcamStream);
    });

    // Receive processed video
    pc.ontrack = (event) => {
        if (event.track.kind === 'video') {
            processedVideo.srcObject = event.streams[0];
        }
    };

    // Create and send offer
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const response = await fetch('/offer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pc.localDescription)
    });

    const answer = await response.json();
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
}

// Start application
start();

// Cleanup on exit
window.addEventListener('beforeunload', () => {
    if (pc) pc.close();
    if (webcamStream) webcamStream.getTracks().forEach(track => track.stop());
});