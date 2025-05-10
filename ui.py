from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QGridLayout,
                            QGroupBox, QSplitter, QFrame, QStackedWidget)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
import cv2
from clothing_tryon import ClothingProcessor

class ImageDisplayLabel(QLabel):
    """Custom QLabel for displaying the camera frames"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #2d2d2d; border-radius: 5px;")
        self.setMinimumSize(320, 240)
        self.setText("No image")
        
class ClothingTryOnApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Virtual Clothing Try-On")
        self.setMinimumSize(1024, 768)
        
        # Initialize the processor
        self.processor = ClothingProcessor()
        
        # Set up the UI
        self.init_ui()
        
        # Set up timer for updating the UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # Update every 30ms (approx 33 fps)
        
        # Start camera
        self.processor.start_camera()
        
    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        title_label = QLabel("Virtual Clothing Try-On")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.status_label = QLabel("Camera Active - Ready for Clothing Upload")
        self.status_label.setStyleSheet("color: green;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        
        # Create clothing upload section
        upload_group = QGroupBox("Upload Clothing Item")
        upload_layout = QVBoxLayout(upload_group)
        
        # Upload button
        upload_btn = QPushButton("Browse for Clothing Image")
        upload_btn.clicked.connect(self.select_clothing_image)
        upload_layout.addWidget(upload_btn)
        
        # Image preview
        clothing_preview_label = QLabel("Selected Clothing:")
        self.clothing_preview = ImageDisplayLabel()
        upload_layout.addWidget(clothing_preview_label)
        upload_layout.addWidget(self.clothing_preview)
        
        # Create video display section
        video_group = QGroupBox("Real-Time View")
        video_layout = QVBoxLayout(video_group)
        
        # Use stacked widget to switch between views
        self.stacked_widget = QStackedWidget()
        
        # Page 1: Camera input only
        camera_page = QWidget()
        camera_layout = QVBoxLayout(camera_page)
        camera_label = QLabel("Camera Preview:")
        self.webcam_display = ImageDisplayLabel()
        camera_layout.addWidget(camera_label)
        camera_layout.addWidget(self.webcam_display)
        
        # Page 2: Processed output only
        processed_page = QWidget()
        processed_layout = QVBoxLayout(processed_page)
        processed_label = QLabel("Try-On Result:")
        self.processed_display = ImageDisplayLabel()
        processed_layout.addWidget(processed_label)
        processed_layout.addWidget(self.processed_display)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(camera_page)
        self.stacked_widget.addWidget(processed_page)
        
        # Add stacked widget to video layout
        video_layout.addWidget(self.stacked_widget)
        
        # Add all sections to main layout
        main_layout.addWidget(header)
        
        # Create a splitter for the main content
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(upload_group)
        splitter.addWidget(video_group)
        splitter.setSizes([200, 600])  # Initial sizes
        main_layout.addWidget(splitter)
        
        # Add control buttons at the bottom
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        
        try_on_btn = QPushButton("Try On Clothing")
        try_on_btn.clicked.connect(self.apply_clothing)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_application)
        
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.close)
        
        controls_layout.addStretch()
        controls_layout.addWidget(try_on_btn)
        controls_layout.addWidget(reset_btn)
        controls_layout.addWidget(exit_btn)
        
        main_layout.addWidget(controls)
        
        # Set the central widget
        self.setCentralWidget(central_widget)
    
    def select_clothing_image(self):
        """Allow user to select a clothing image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Clothing Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            # Set the clothing image in the processor
            if self.processor.set_clothing(file_path):
                # Display the selected image
                clothing_img = cv2.imread(file_path)
                clothing_img_rgb = cv2.cvtColor(clothing_img, cv2.COLOR_BGR2RGB)
                h, w, c = clothing_img_rgb.shape
                q_img = QImage(clothing_img_rgb.data, w, h, w * c, QImage.Format_RGB888)
                self.clothing_preview.setPixmap(QPixmap.fromImage(q_img).scaled(
                    self.clothing_preview.width(), 
                    self.clothing_preview.height(),
                    Qt.KeepAspectRatio
                ))
                
                self.status_label.setText("Clothing loaded - Click 'Try On Clothing' when ready")
                self.status_label.setStyleSheet("color: orange;")
            else:
                self.clothing_preview.setText("Failed to load image")
    
    def apply_clothing(self):
        """Apply the clothing to the video feed"""
        if self.processor.clothing_image is not None:
            # Switch to processed view
            self.stacked_widget.setCurrentIndex(1)
            
            # Update status
            self.status_label.setText("Try-on active - showing processed view")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Please select a clothing item first")
            self.status_label.setStyleSheet("color: red;")
    
    def update_frames(self):
        """Update the UI with the latest frames"""
        # Update original webcam frame (always updated)
        if self.processor.original_frame is not None:
            frame = cv2.cvtColor(self.processor.original_frame, cv2.COLOR_BGR2RGB)
            h, w, c = frame.shape
            q_img = QImage(frame.data, w, h, w * c, QImage.Format_RGB888)
            self.webcam_display.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.webcam_display.width(),
                self.webcam_display.height(),
                Qt.KeepAspectRatio
            ))
        
        # Update processed frame (always updated but only shown after processing)
        if self.processor.processed_frame is not None:
            processed = cv2.cvtColor(self.processor.processed_frame, cv2.COLOR_BGR2RGB)
            h, w, c = processed.shape
            q_img = QImage(processed.data, w, h, w * c, QImage.Format_RGB888)
            self.processed_display.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.processed_display.width(),
                self.processed_display.height(),
                Qt.KeepAspectRatio
            ))
    
    def reset_application(self):
        """Reset the application state"""
        # Reset processor
        self.processor.clothing_loaded = False
        
        # Reset UI
        self.clothing_preview.setText("No image")
        self.stacked_widget.setCurrentIndex(0)  # Switch back to camera view
        self.status_label.setText("Camera Active - Ready for Clothing Upload")
        self.status_label.setStyleSheet("color: green;")
    
    def restart_camera(self):
        """Restart the camera capture"""
        self.processor.stop_camera()
        self.processor.start_camera()
    
    def closeEvent(self, event):
        """Clean up resources when closing the application"""
        self.timer.stop()
        self.processor.stop_camera()
        event.accept()