from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QGroupBox, 
                            QSizePolicy)
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QSize
import cv2
from clothing_tryon import ClothingProcessor

class CenteredImageLabel(QLabel):
    """Custom QLabel that properly centers and scales images"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            background-color: #1e1e2d;
            border-radius: 8px;
            border: 1px solid #3a3a4a;
            color: #aaaaaa;
            padding: 10px;
        """)
        self.setMinimumSize(300, 300)
        self.setText("No image available")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.current_pixmap = None

    def resizeEvent(self, event):
        """Handle resizing while maintaining aspect ratio"""
        super().resizeEvent(event)
        if self.current_pixmap:
            self.setPixmap(self.current_pixmap)

    def setPixmap(self, pixmap):
        """Override to ensure proper scaling and centering"""
        if pixmap and not pixmap.isNull():
            self.current_pixmap = pixmap
            scaled = pixmap.scaled(
                self.width() - 20,  # Account for padding
                self.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            super().setPixmap(scaled)
        else:
            self.current_pixmap = None
            super().setPixmap(QPixmap())

class VideoDisplayLabel(QLabel):
    """Specialized label for video feed with better performance"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            background-color: #1e1e2d;
            border-radius: 8px;
            border: 1px solid #3a3a4a;
        """)
        self.setMinimumSize(640, 480)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

class ClothingTryOnApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_main_window()
        self.processor = ClothingProcessor()
        self.init_ui()
        self.setup_camera()
        
    def setup_main_window(self):
        """Configure main window properties"""
        self.setWindowTitle("Virtual Clothing Try-On")
        self.setMinimumSize(1024, 768)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121218;
            }
            QGroupBox {
                border: 1px solid #3a3a4a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                color: #cccccc;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

    def init_ui(self):
        """Initialize all UI components"""
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #121218;")
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.setup_header(main_layout)
        self.setup_content_area(main_layout)
        self.setCentralWidget(central_widget)
        self.try_on_active = False

    def setup_header(self, main_layout):
        """Create the header section"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Virtual Clothing Try-On")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 14px;
                padding: 5px 10px;
                border-radius: 4px;
                background-color: rgba(76, 175, 80, 0.1);
            }
        """)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        main_layout.addWidget(header)

    def setup_content_area(self, main_layout):
        """Create the main content area"""
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        self.setup_control_panel(content_layout)
        self.setup_video_panel(content_layout)
        main_layout.addWidget(content_widget)

    def setup_control_panel(self, content_layout):
        """Create the left control panel"""
        control_panel = QWidget()
        control_panel.setMaximumWidth(350)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(15)

        self.setup_clothing_upload(control_layout)
        self.setup_controls(control_layout)
        content_layout.addWidget(control_panel)

    def setup_clothing_upload(self, control_layout):
        """Create the clothing upload section"""
        upload_group = QGroupBox("Clothing Selection")
        upload_layout = QVBoxLayout(upload_group)
        upload_layout.setAlignment(Qt.AlignHCenter)
        upload_layout.setSpacing(15)
        upload_layout.setContentsMargins(15, 15, 15, 15)

        upload_btn = ModernButton("Browse Clothing Image", QIcon.fromTheme("document-open"))
        upload_btn.clicked.connect(self.select_clothing_image)

        # Special container for the image preview
        preview_container = QWidget()
        preview_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setAlignment(Qt.AlignCenter)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.clothing_preview = CenteredImageLabel()
        preview_layout.addWidget(self.clothing_preview)

        upload_layout.addWidget(upload_btn, 0, Qt.AlignHCenter)
        upload_layout.addWidget(preview_container)
        control_layout.addWidget(upload_group)

    def setup_controls(self, control_layout):
        """Create the control buttons section"""
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(10)

        self.try_on_btn = ModernButton("Apply Try-On", QIcon.fromTheme("camera-web"))
        self.try_on_btn.clicked.connect(self.toggle_try_on)
        self.try_on_btn.setEnabled(False)

        reset_btn = ModernButton("Reset", QIcon.fromTheme("edit-clear"))
        reset_btn.clicked.connect(self.reset_application)

        exit_btn = ModernButton("Exit", QIcon.fromTheme("application-exit"))
        exit_btn.clicked.connect(self.close)
        exit_btn.setStyleSheet("background-color: #6a1b1b;")

        controls_layout.addWidget(self.try_on_btn)
        controls_layout.addWidget(reset_btn)
        controls_layout.addWidget(exit_btn)
        controls_layout.addStretch()
        control_layout.addWidget(controls_group)

    def setup_video_panel(self, content_layout):
        """Create the right video panel - fixed layout hierarchy"""
        video_group = QGroupBox("Live Preview")
        video_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create the video display label
        self.video_display = VideoDisplayLabel()
        
        # Set up the layout for the group box
        video_group_layout = QVBoxLayout(video_group)
        video_group_layout.addWidget(self.video_display)
        
        # Add the group box directly to content layout
        content_layout.addWidget(video_group)

    def setup_camera(self):
        """Set up camera and timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)
        self.processor.start_camera()

    def select_clothing_image(self):
        """Handle clothing image selection"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Clothing Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            if self.processor.set_clothing(file_path):
                clothing_img = cv2.imread(file_path)
                if clothing_img is not None:
                    clothing_img_rgb = cv2.cvtColor(clothing_img, cv2.COLOR_BGR2RGB)
                    h, w, c = clothing_img_rgb.shape
                    q_img = QImage(clothing_img_rgb.data, w, h, w * c, QImage.Format_RGB888)
                    self.clothing_preview.setPixmap(QPixmap.fromImage(q_img))
                    
                    self.status_label.setText("Clothing loaded")
                    self.status_label.setStyleSheet("color: #FF9800; background-color: rgba(255, 152, 0, 0.1);")
                    self.try_on_btn.setEnabled(True)
                    return
            
            self.clothing_preview.setText("Failed to load image")
            self.clothing_preview.setPixmap(QPixmap())
            self.status_label.setText("Failed to load clothing")
            self.status_label.setStyleSheet("color: #F44336; background-color: rgba(244, 67, 54, 0.1);")

    def update_frames(self):
        """Update the video frames"""
        # Get the latest frame from the processor
        if not self.processor.capture or not self.processor.capture.isOpened():
            return

        ret, frame = self.processor.capture.read()
        if not ret:
            return

        # Store the original frame
        self.processor.original_frame = frame.copy()
        
        # Process the frame if clothing is loaded and try-on is active
        if self.try_on_active and self.processor.clothing_loaded:
            self.processor.processed_frame = self.processor.model.process_frame(frame, self.processor.clothing_image)
            display_frame = self.processor.processed_frame
        else:
            display_frame = self.processor.original_frame

        # Convert and display the frame
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, c = display_frame_rgb.shape
        bytes_per_line = w * c
        q_img = QImage(display_frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale to fit while maintaining aspect ratio
        self.video_display.setPixmap(
            QPixmap.fromImage(q_img).scaled(
                self.video_display.width(),
                self.video_display.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def toggle_try_on(self):
        """Toggle between original and try-on views"""
        self.try_on_active = not self.try_on_active
        if self.try_on_active:
            self.try_on_btn.setText("Show Original")
            self.status_label.setText("Try-on active")
            self.status_label.setStyleSheet("color: #4CAF50; background-color: rgba(76, 175, 80, 0.1);")
        else:
            self.try_on_btn.setText("Apply Try-On")
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: #4CAF50; background-color: rgba(76, 175, 80, 0.1);")

    def reset_application(self):
        """Reset the application state"""
        self.processor.clothing_loaded = False
        self.clothing_preview.setText("No clothing selected")
        self.clothing_preview.setPixmap(QPixmap())
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: #4CAF50; background-color: rgba(76, 175, 80, 0.1);")
        self.try_on_btn.setEnabled(False)
        self.try_on_active = False
        self.try_on_btn.setText("Apply Try-On")

    def closeEvent(self, event):
        """Clean up on window close"""
        self.timer.stop()
        self.processor.stop_camera()
        event.accept()

class ModernButton(QPushButton):
    """Styled button for consistent UI"""
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4a4a6a;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a5a7a;
            }
            QPushButton:pressed {
                background-color: #3a3a5a;
            }
            QPushButton:disabled {
                background-color: #2a2a3a;
                color: #666666;
            }
        """)
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(16, 16))