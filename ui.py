from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QGridLayout,
                            QGroupBox, QSplitter, QFrame)
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
        self.setWindowTitle("Video Processing App")
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
        title_label = QLabel("Video Processing App")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        status_label = QLabel("Camera Active")
        status_label.setStyleSheet("color: green;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        
        # Create video display section
        video_group = QGroupBox("Real-Time Processing")
        video_layout = QGridLayout(video_group)
        
        # Camera input
        webcam_label = QLabel("Original Webcam Input:")
        self.webcam_display = ImageDisplayLabel()
        video_layout.addWidget(webcam_label, 0, 0)
        video_layout.addWidget(self.webcam_display, 1, 0)
        
        # Processed output
        processed_label = QLabel("Processed Output (Flipped):")
        self.processed_display = ImageDisplayLabel()
        video_layout.addWidget(processed_label, 0, 1)
        video_layout.addWidget(self.processed_display, 1, 1)
        
        # Add all sections to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(video_group)
        
        # Add control buttons at the bottom
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        
        restart_btn = QPushButton("Restart Camera")
        restart_btn.clicked.connect(self.restart_camera)
        
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.close)
        
        controls_layout.addStretch()
        controls_layout.addWidget(restart_btn)
        controls_layout.addWidget(exit_btn)
        
        main_layout.addWidget(controls)
        
        # Set the central widget
        self.setCentralWidget(central_widget)
    
    def update_frames(self):
        """Update the UI with the latest frames"""
        # Update original webcam frame
        if self.processor.original_frame is not None:
            frame = cv2.cvtColor(self.processor.original_frame, cv2.COLOR_BGR2RGB)
            h, w, c = frame.shape
            q_img = QImage(frame.data, w, h, w * c, QImage.Format_RGB888)
            self.webcam_display.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.webcam_display.width(),
                self.webcam_display.height(),
                Qt.KeepAspectRatio
            ))
        
        # Update processed frame
        if self.processor.processed_frame is not None:
            processed = cv2.cvtColor(self.processor.processed_frame, cv2.COLOR_BGR2RGB)
            h, w, c = processed.shape
            q_img = QImage(processed.data, w, h, w * c, QImage.Format_RGB888)
            self.processed_display.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.processed_display.width(),
                self.processed_display.height(),
                Qt.KeepAspectRatio
            ))
    
    def restart_camera(self):
        """Restart the camera capture"""
        self.processor.stop_camera()
        self.processor.start_camera()
    
    def closeEvent(self, event):
        """Clean up resources when closing the application"""
        self.timer.stop()
        self.processor.stop_camera()
        event.accept()