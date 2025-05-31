# camera_widget.py
import cv2
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, QPoint, QEvent
from detectors.yolo_detector import detect_humans
from utils.geometry import is_inside_roi
from utils.alert import trigger_alert
from utils.logger import log_event

class CameraWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.cap = None
        self.timer = QTimer()
        
        self.roi = None  # ROI will be set by user
        self.drawing = False
        self.allow_drawing = False
        self.start_point = None
        self.end_point = None
        
        self.video_label = QLabel("Video Feed")
        self.video_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: black;
                border-radius: 8px;
            }
        """)
        self.video_label.setMouseTracking(True)
        self.video_label.installEventFilter(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_label)
        self.setLayout(layout)
        
        self.timer.timeout.connect(self.update_frame)
        
        

    def start(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open video capture.")
            return
        self.timer.start(30)

    def stop(self):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.clear()
            
    def enable_drawing(self):
        self.allow_drawing = True

    def eventFilter(self, source, event):
        if source is self.video_label and self.allow_drawing:
            if event.type() in [QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonRelease]:
                label_size = self.video_label.size()
                if self.cap:
                    ret, frame = self.cap.read()
                    if not ret:
                        return super().eventFilter(source, event)
                    frame_height, frame_width = frame.shape[:2]
                    scale = min(label_size.width() / frame_width, label_size.height() / frame_height)
                    new_width = int(frame_width * scale)
                    new_height = int(frame_height * scale)
                    x_offset = (label_size.width() - new_width) // 2
                    y_offset = (label_size.height() - new_height) // 2

                    pos = event.pos()
                    # Clamp to displayed video area
                    x = int(max(0, min(new_width - 1, pos.x() - x_offset)))
                    y = int(max(0, min(new_height - 1, pos.y() - y_offset)))

                    if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                        self.drawing = True
                        self.start_point = (x, y)
                        self.end_point = self.start_point
                        return True
                    elif event.type() == QEvent.MouseMove and self.drawing:
                        self.end_point = (x, y)
                        return True
                    elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                        self.drawing = False
                        x1, y1 = self.start_point
                        x2, y2 = self.end_point
                        self.roi = [(min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2))]
                        self.allow_drawing = False
                        return True
        return super().eventFilter(source, event)

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if not ret:
                return
            
            # Get current label size for proper scaling
            label_size = self.video_label.size()
            frame_height, frame_width = frame.shape[:2]
            
            # Calculate scaling to maintain aspect ratio
            scale = min(label_size.width() / frame_width, 
                    label_size.height() / frame_height)
            new_width = int(frame_width * scale)
            new_height = int(frame_height * scale)
            
            # Resize frame while maintaining aspect ratio
            frame = cv2.resize(frame, (new_width, new_height))

            # Detection
            humans = detect_humans(frame)
            for person in humans:
                x1, y1, x2, y2 = person["box"]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                if self.roi and is_inside_roi((cx, cy), self.roi):
                    trigger_alert()
                    log_event("Intrusion Detected", frame)
                    cv2.putText(frame, "INTRUDER!", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

            # Draw ROI (either user-drawn or currently drawing)
            if self.roi:
                cv2.rectangle(frame, self.roi[0], self.roi[1], (0, 255, 0), 2)
            elif self.drawing and self.start_point and self.end_point:
                cv2.rectangle(frame, self.start_point, self.end_point, (0, 255, 255), 2)

            # Convert to RGB and create QPixmap
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale pixmap to fit label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                label_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Center the pixmap in the label
            self.video_label.setAlignment(Qt.AlignCenter)
            self.video_label.setPixmap(scaled_pixmap)