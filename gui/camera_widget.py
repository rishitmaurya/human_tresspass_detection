# camera_widget.py
import cv2
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, QPoint
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
        self.video_label.setFixedSize(950, 600)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setMouseTracking(True)
        self.video_label.installEventFilter(self)

        layout = QVBoxLayout()
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
        if source is self.video_label:
            if not self.allow_drawing:
                return super().eventFilter(source, event)
                
            if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                self.drawing = True
                self.start_point = event.pos()
                self.end_point = event.pos()
            elif event.type() == event.MouseMove and self.drawing:
                self.end_point = event.pos()
            elif event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
                self.drawing = False
                x1, y1 = self.start_point.x(), self.start_point.y()
                x2, y2 = self.end_point.x(), self.end_point.y()
                self.roi = [(min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2))]
                self.allow_drawing = False  
        return super().eventFilter(source, event)

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if not ret:
                return
            
            # Resize frame to match video_label size
            frame = cv2.resize(frame, (950, 600))

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
                pt1 = (self.start_point.x(), self.start_point.y())
                pt2 = (self.end_point.x(), self.end_point.y())
                cv2.rectangle(frame, pt1, pt2, (0, 255, 255), 2)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)

            self.video_label.setPixmap(pixmap)