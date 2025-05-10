const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const previewImg = document.getElementById('garment-preview');
let garmentPath = null;

// Start webcam feed
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
    video.addEventListener('loadedmetadata', () => {
      // Match canvas size to video resolution
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      startProcessingLoop();
    });
  })
  .catch(err => console.error('Error accessing webcam:', err));

// Handle clothing upload
document.getElementById('upload').addEventListener('change', e => {
  const file = e.target.files[0];
  if (!file) return;

  // Preview locally
  const reader = new FileReader();
  reader.onload = function(evt) {
    previewImg.src = evt.target.result;
  };
  reader.readAsDataURL(file);

  // Upload to server
  const fd = new FormData();
  fd.append('garment', file);
  fetch('/upload', { method: 'POST', body: fd })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'ok') {
        garmentPath = data.path;
        console.log('Uploaded to', garmentPath);
      }
    });
});

// Processing loop: continuously send frames to backend for processing
function startProcessingLoop() {
  async function processFrame() {
    // Capture current frame
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    tempCanvas.getContext('2d').drawImage(video, 0, 0);

    // Convert to base64 JPEG
    const frameBase64 = tempCanvas.toDataURL('image/jpeg').split(',')[1];

    try {
      // Send to backend for processing
      const resp = await fetch('/process_frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame: frameBase64, garment_path: garmentPath })
      });
      const json = await resp.json();
      const processedFrame = json.frame;

      // Only draw if frame is returned
      if (processedFrame) {
        const img = new Image();
        img.src = 'data:image/jpeg;base64,' + processedFrame;
        img.onload = () => ctx.drawImage(img, 0, 0);
      }
    } catch (error) {
      console.error('Error processing frame:', error);
    }
  }

  // Loop indefinitely
  (async function loop() {
    await processFrame();
    requestAnimationFrame(loop);
  })();
}