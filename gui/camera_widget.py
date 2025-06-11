# camera_widget.py
import cv2
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import QTimer, Qt, QPoint, QEvent, QThread, pyqtSignal
from detectors.yolo_detector import detect_humans
from utils.geometry import is_inside_roi
from utils.alert import trigger_alert
from utils.logger import log_event
from PyQt5 import QtCore
import os
from datetime import datetime
from utils.email.sender import UniversalEmailSender
from time import time
import json

from PyQt5.QtCore import QThread, pyqtSignal

class DangerEmailThread(QThread):
    error_signal = pyqtSignal(str)
    success_signal = pyqtSignal()

    def __init__(self, sender, password, receivers, img_path, date_str, time_str, day_str):
        super().__init__()
        self.sender = sender
        self.password = password
        self.receivers = receivers
        self.img_path = img_path
        self.date_str = date_str
        self.time_str = time_str
        self.day_str = day_str

    def run(self):
        try:
            sender = UniversalEmailSender(
                self.sender,
                self.password,
                "gmail"
            )
            subject = "Danger ROI Intrusion Alert"
            body = f"Intrusion detected in Danger ROI!\nDate: {self.date_str}\nTime: {self.time_str}\nDay: {self.day_str}"
            sender.send_email(
                self.receivers,
                subject,
                body,
                attachments=[self.img_path]
            )
            self.success_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

class CameraWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.cap = None
        self.timer = QTimer()
        
        self.rois = []
        self.danger_rois = []
        self.current_roi = None  
        self.drawing = False
        self.allow_drawing = False
        self.start_point = None
        self.end_point = None
        self.detection_enabled = False
        self.last_alert_time = 0
        self.drawing_danger = False
        self.last_danger_alert_time = 0
        
        self.danger_mail_sender = "shubhamrishit33@gmail.com"
        self.danger_mail_password = "bfcbtywflqclyxbm"
        self.danger_mail_receivers = {
            "receiver1": {"email": "rishitmaurya2002@gmail.com", "enabled": True},
            "receiver2": {"email": "", "enabled": False},
            "receiver3": {"email": "", "enabled": False}
        }
        
        self.load_danger_mail_config()
        
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
        self.detection_enabled = True
        self.timer.start(30)

    def stop(self):
        if self.cap:
            self.detection_enabled = False
            self.roi = None  
            self.drawing = False
            self.allow_drawing = False
            
    def enable_drawing(self):
        self.allow_drawing = True
        self.drawing = False
        self.current_roi = None
        self.start_point = None
        self.end_point = None
        self.drawing_danger = False
        
    def enable_danger_drawing(self):
        
        self.allow_drawing = True
        self.drawing = False
        self.drawing_danger = True

    def eventFilter(self, source, event):
        if source is self.video_label and self.allow_drawing:
            if event.type() == QEvent.MouseButtonPress:
                self.mousePressEvent(event)
                return True
            elif event.type() == QEvent.MouseMove:
                self.mouseMoveEvent(event)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)
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
            if self.detection_enabled:
                humans = detect_humans(frame)
                current_time = time()
                danger_triggered = False
                for person in humans:
                    x1, y1, x2, y2 = person["box"]
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    if any(is_inside_roi((cx, cy), roi) for roi in self.danger_rois):
                        # If first alert (after 1 sec) or 10 sec since last alert
                        if (self.last_danger_alert_time == 0 and current_time - self.last_alert_time >= 1) or \
                        (self.last_danger_alert_time != 0 and current_time - self.last_danger_alert_time >= 10):
                            QtCore.QTimer.singleShot(0, lambda: self.handle_danger_alert(frame.copy()))
                            self.last_danger_alert_time = current_time
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        danger_triggered = True
                    
                    if not danger_triggered:
                        self.last_danger_alert_time = 0
                    
                    if any(is_inside_roi((cx, cy), roi) for roi in self.rois):
                        # Check if 5 second has passed since last alert
                        if current_time - self.last_alert_time >= 5.0:
                            # Create a copy of the frame for logging
                            log_frame = frame.copy()
                            
                            # Handle alert in non-blocking way
                            QtCore.QTimer.singleShot(0, lambda: trigger_alert())
                            QtCore.QTimer.singleShot(0, lambda f=log_frame: log_event("Intrusion Detected", f))
                            
                            # Update last alert time
                            self.last_alert_time = current_time
                        
                        # Add visual indicator on display frame
                        cv2.putText(frame, "INTRUDER!", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                    # Always draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                # Draw ROI
                for roi in self.rois:
                    cv2.rectangle(frame, roi[0], roi[1], (0, 255, 0), 2)
                    
                # Draw danger ROIs in red
                for roi in self.danger_rois:
                    cv2.rectangle(frame, roi[0], roi[1], (0, 0, 255), 2)
                    
                if self.drawing and self.start_point and self.end_point:
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
            
            # Update the display
            self.video_label.setAlignment(Qt.AlignCenter)
            self.video_label.setPixmap(scaled_pixmap)
            
    def mousePressEvent(self, event):
        if self.allow_drawing and not self.drawing and event.button() == Qt.LeftButton:
            x, y = self.map_to_video(event.pos())
            self.drawing = True
            self.current_roi = [x, y, x, y]

    def mouseMoveEvent(self, event):
        if self.allow_drawing and self.drawing and self.current_roi:
            x, y = self.map_to_video(event.pos())
            self.current_roi[2] = x
            self.current_roi[3] = y
            self.update()

    def mouseReleaseEvent(self, event):
        if self.allow_drawing and self.drawing and self.current_roi and event.button() == Qt.LeftButton:
            x, y = self.map_to_video(event.pos())
            self.current_roi[2] = x
            self.current_roi[3] = y
            x1, y1, x2, y2 = self.current_roi
            roi_tuple = ((min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2)))
            if self.drawing_danger:
                self.danger_rois.append(roi_tuple)
            else:
                self.rois.append(roi_tuple)
            self.current_roi = None
            self.drawing = False
            self.allow_drawing = False
            self.drawing_danger = False
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        # Draw normal ROIs in green
        pen = QPen(Qt.green, 2, Qt.SolidLine)
        painter.setPen(pen)
        for roi in self.rois:
            (x1, y1), (x2, y2) = roi
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
        # Draw danger ROIs in red
        pen = QPen(Qt.red, 2, Qt.SolidLine)
        painter.setPen(pen)
        for roi in self.danger_rois:
            (x1, y1), (x2, y2) = roi
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
        # Draw the current ROI being drawn
        if self.current_roi:
            
            x1, y1, x2, y2 = self.current_roi
            pen = QPen(Qt.red if self.drawing_danger else Qt.green, 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            
    def map_to_video(self, pos):
        label_size = self.video_label.size()
        if not self.cap:
            return 0, 0
        ret, frame = self.cap.read()
        if not ret:
            return 0, 0
        frame_height, frame_width = frame.shape[:2]
        scale = min(label_size.width() / frame_width, label_size.height() / frame_height)
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        x_offset = (label_size.width() - new_width) // 2
        y_offset = (label_size.height() - new_height) // 2

        x = int(max(0, min(new_width - 1, pos.x() - x_offset)))
        y = int(max(0, min(new_height - 1, pos.y() - y_offset)))
        return x, y
    
    def clear_rois(self):
        self.rois.clear()
        self.danger_rois.clear()
        self.current_roi = None
        self.drawing = False
        self.allow_drawing = False
        self.update()
        
    def handle_danger_alert(self, frame):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Danger!", "Robot stopped")
        # Save current frame as image
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        day_str = now.strftime("%A")
        img_name = f"danger_{date_str}_{time_str}.jpg"
        img_path = os.path.join("danger_alerts", img_name)
        os.makedirs("danger_alerts", exist_ok=True)
        cv2.imwrite(img_path, frame)
        # Send email
        self.send_danger_email(img_path, date_str, time_str, day_str)
        
    def change_danger_mail_details(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Change Danger Mail Details")
        layout = QFormLayout(dialog)

        sender_edit = QLineEdit(self.danger_mail_sender)
        password_edit = QLineEdit(self.danger_mail_password)
        password_edit.setEchoMode(QLineEdit.Password)
        
        receiver_edits = {}
        receiver_checkboxes = {}
        
        layout.addRow("Sender Email:", sender_edit)
        layout.addRow("Sender Password:", password_edit)
        
        for i, (key, value) in enumerate(self.danger_mail_receivers.items(), 1):
            h_layout = QHBoxLayout()
            edit = QLineEdit(value["email"])
            checkbox = QCheckBox("Enable")
            checkbox.setChecked(value["enabled"])
            
            h_layout.addWidget(edit)
            h_layout.addWidget(checkbox)
            
            receiver_edits[key] = edit
            receiver_checkboxes[key] = checkbox
            layout.addRow(f"Receiver {i} Email:", h_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        def on_accept():
            self.danger_mail_sender = sender_edit.text()
            self.danger_mail_password = password_edit.text()
            
            for key in self.danger_mail_receivers:
                self.danger_mail_receivers[key]["email"] = receiver_edits[key].text()
                self.danger_mail_receivers[key]["enabled"] = receiver_checkboxes[key].isChecked()
            
            self.save_danger_mail_config()
            dialog.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dialog.reject)

        dialog.exec_()
        
    def load_danger_mail_config(self):
        config_path = "danger_mail_config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                self.danger_mail_sender = data.get("sender", self.danger_mail_sender)
                self.danger_mail_password = data.get("password", self.danger_mail_password)
                self.danger_mail_receivers = data.get("receivers", self.danger_mail_receivers)

    def save_danger_mail_config(self):
        config_path = "danger_mail_config.json"
        data = {
            "sender": self.danger_mail_sender,
            "password": self.danger_mail_password,
            "receivers": self.danger_mail_receivers
        }
        with open(config_path, "w") as f:
            json.dump(data, f)

    def send_danger_email(self, img_path, date_str, time_str, day_str):
        
        active_receivers = [
            receiver["email"] 
            for receiver in self.danger_mail_receivers.values() 
            if receiver["enabled"] and receiver["email"].strip()
        ]
        
        if not active_receivers:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "No active email receivers configured!")
            return
        
        self.email_thread = DangerEmailThread(
            self.danger_mail_sender,
            self.danger_mail_password,
            active_receivers,
            img_path,
            date_str,
            time_str,
            day_str
        )
        self.email_thread.error_signal.connect(self.show_email_error)
        self.email_thread.success_signal.connect(self.show_email_success)
        self.email_thread.start()
        
    def show_email_success(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Email Sent", "Danger alert email sent successfully!")
        
    def show_email_error(self, error_msg):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Danger Mail Error", f"Failed to send danger email:\n{error_msg}")
