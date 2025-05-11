class VirtualTryOn {
  constructor() {
    this.net = null;
    this.videoElement = document.getElementById("camera-feed");
    this.outputCanvas = document.getElementById("output-canvas");
    this.ctx = this.outputCanvas.getContext("2d");
    this.loadingOverlay = document.getElementById("loading-overlay");
    this.clothingImage = null;
    this.tryOnActive = false;
    this.animationFrameId = null;
    this.isProcessing = false;
    this.cameraReady = false;

    // UI Elements
    this.statusElement = document.getElementById("status");
    this.clothingPreview = document.getElementById("clothing-preview");
    this.tryOnButton = document.getElementById("try-on-btn");
    this.resetButton = document.getElementById("reset-btn");
    this.clothingUpload = document.getElementById("clothing-upload");

    // Event listeners
    this.tryOnButton.addEventListener("click", this.toggleTryOn.bind(this));
    this.resetButton.addEventListener("click", this.reset.bind(this));
    this.clothingUpload.addEventListener(
      "change",
      this.handleClothingUpload.bind(this)
    );

    this.init();
  }

  async init() {
    try {
      this.showLoading(true);
      this.updateStatus("Loading models...", "warning");

      // Load BodyPix model
      this.net = await bodyPix.load({
        architecture: "MobileNetV1",
        outputStride: 16,
        multiplier: 1,
        quantBytes: 2,
        internalResolution: "low",
      });

      // Start camera
      await this.startCamera();
      this.cameraReady = true;

      this.updateStatus("Ready", "ready");
      this.showLoading(false);
      this.processFrame();
    } catch (error) {
      console.error("Initialization error:", error);
      this.updateStatus("Failed to initialize: " + error, "error");
      this.showLoading(false);

      // Fallback to static image mode if camera fails
      this.videoElement.style.display = "none";
      this.outputCanvas.style.background = "#333";
      this.ctx.fillStyle = "white";
      this.ctx.textAlign = "center";
      this.ctx.fillText(
        "Camera initialization failed",
        this.outputCanvas.width / 2,
        this.outputCanvas.height / 2
      );
    }
  }

  isVideoReady() {
    return (
      this.cameraReady &&
      this.videoElement.videoWidth > 10 && // Minimum 10px to prevent zero dimensions
      this.videoElement.videoHeight > 10 &&
      this.outputCanvas.width === this.videoElement.videoWidth && // Exact match required
      this.outputCanvas.height === this.videoElement.videoHeight
    );
  }

  syncCanvasToVideo() {
    if (
      this.videoElement.videoWidth !== this.outputCanvas.width ||
      this.videoElement.videoHeight !== this.outputCanvas.height
    ) {
      this.outputCanvas.width = this.videoElement.videoWidth;
      this.outputCanvas.height = this.videoElement.videoHeight;
    }
  }

  async startCamera() {
    try {
      const isMobile = /Mobi|Android/i.test(navigator.userAgent);
      const constraints = {
        video: {
          facingMode: "user",
          width: isMobile ? { ideal: window.screen.width } : { ideal: 640 },
          height: isMobile ? { ideal: window.screen.height } : { ideal: 480 },
        },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.videoElement.srcObject = stream;

      // Set explicit video dimensions
      this.videoElement.width = isMobile ? window.screen.width : 640;
      this.videoElement.height = isMobile ? window.screen.height : 480;

      return new Promise((resolve) => {
        const checkReady = () => {
          if (
            this.videoElement.videoWidth > 10 && // Minimum 10px check
            this.videoElement.videoHeight > 10
          ) {
            this.outputCanvas.width = this.videoElement.videoWidth;
            this.outputCanvas.height = this.videoElement.videoHeight;
            resolve();
          } else {
            setTimeout(checkReady, 100);
          }
        };
        this.videoElement.onloadedmetadata = () => {
          checkReady();
        };
        checkReady();
      });
    } catch (error) {
      console.error("Camera error:", error);
      this.updateStatus("Camera access denied", "error");
      throw error;
    }
  }

  async processFrame() {
    if (this.isProcessing || !this.isVideoReady()) {
      this.animationFrameId = requestAnimationFrame(
        this.processFrame.bind(this)
      );
      return;
    }

    try {
      this.isProcessing = true;
      this.syncCanvasToVideo();

      // Don't draw immediately - prepare everything first
      if (this.tryOnActive && this.clothingImage?.complete) {
        try {
          // Use video element for segmentation
          const segmentation = await this.net.segmentPersonParts(
            this.videoElement,
            {
              segmentationThreshold: 0.7,
              flipHorizontal: true,
              internalResolution: "medium",
              maxDetections: 1,
            }
          );

          // Create an offscreen canvas for compositing
          const offscreenCanvas = document.createElement("canvas");
          offscreenCanvas.width = this.outputCanvas.width;
          offscreenCanvas.height = this.outputCanvas.height;
          const offscreenCtx = offscreenCanvas.getContext("2d");

          // First draw video feed to offscreen canvas
          offscreenCtx.drawImage(
            this.videoElement,
            0,
            0,
            offscreenCanvas.width,
            offscreenCanvas.height
          );

          // Then apply the mask if segmentation was successful
          if (
            segmentation?.data &&
            segmentation.width > 0 &&
            segmentation.height > 0
          ) {
            const coloredPartImage = bodyPix.toColoredPartMask(segmentation);
            const opacity = 0.7;
            const maskBlurAmount = 3;

            // Apply mask to the offscreen canvas
            bodyPix.drawMask(
              offscreenCanvas,
              offscreenCanvas,
              coloredPartImage,
              opacity,
              maskBlurAmount
            );

            // Clean up
            tf.dispose(coloredPartImage);
          }

          // Finally, draw the completed offscreen canvas to the visible canvas in one operation
          this.ctx.clearRect(
            0,
            0,
            this.outputCanvas.width,
            this.outputCanvas.height
          );
          this.ctx.drawImage(offscreenCanvas, 0, 0);
        } catch (segError) {
          console.warn("Segmentation error:", segError);
          // If segmentation fails, draw just the video
          this.ctx.clearRect(
            0,
            0,
            this.outputCanvas.width,
            this.outputCanvas.height
          );
          this.ctx.drawImage(
            this.videoElement,
            0,
            0,
            this.outputCanvas.width,
            this.outputCanvas.height
          );
        }
      } else {
        // Just draw the video if try-on is inactive
        this.ctx.clearRect(
          0,
          0,
          this.outputCanvas.width,
          this.outputCanvas.height
        );
        this.ctx.drawImage(
          this.videoElement,
          0,
          0,
          this.outputCanvas.width,
          this.outputCanvas.height
        );
      }
    } catch (error) {
      console.error("Frame processing failed:", error);
    } finally {
      this.isProcessing = false;
      // Throttle processing to ~25fps for better stability
      setTimeout(() => {
        this.animationFrameId = requestAnimationFrame(
          this.processFrame.bind(this)
        );
      }, 40);
    }
  }

  handleClothingUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        this.clothingImage = img;
        this.clothingPreview.innerHTML = "";
        this.clothingPreview.appendChild(img);
        this.tryOnButton.disabled = false;
        this.updateStatus("Clothing loaded", "ready");
      };
      img.onerror = () => {
        this.clothingPreview.innerHTML = "<span>Error loading image</span>";
        this.updateStatus("Invalid image file", "error");
      };
      img.src = e.target.result;
    };
    reader.onerror = () => {
      this.clothingPreview.innerHTML = "<span>Error reading file</span>";
      this.updateStatus("File read error", "error");
    };
    reader.readAsDataURL(file);
  }

  toggleTryOn() {
    this.tryOnActive = !this.tryOnActive;
    if (this.tryOnActive) {
      this.tryOnButton.textContent = "Show Original";
      this.updateStatus("Try-on active", "ready");
    } else {
      this.tryOnButton.textContent = "Apply Try-On";
      this.updateStatus("Ready", "ready");
    }
  }

  reset() {
    this.tryOnActive = false;
    this.clothingImage = null;
    this.clothingPreview.innerHTML = "<span>No clothing selected</span>";
    this.tryOnButton.textContent = "Apply Try-On";
    this.tryOnButton.disabled = true;
    this.clothingUpload.value = "";
    this.updateStatus("Ready", "ready");
  }

  updateStatus(message, type) {
    this.statusElement.textContent = message;
    this.statusElement.className = `status status-${type}`;
  }

  showLoading(show) {
    this.loadingOverlay.style.display = show ? "flex" : "none";
  }

  cleanup() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    if (this.videoElement.srcObject) {
      this.videoElement.srcObject.getTracks().forEach((track) => track.stop());
    }
    // Clean up TensorFlow.js memory
    if (this.net) {
      tf.disposeVariables();
    }
  }
}

// Initialize application when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  const app = new VirtualTryOn();

  // Cleanup on exit
  window.addEventListener("beforeunload", () => {
    app.cleanup();
  });
});
