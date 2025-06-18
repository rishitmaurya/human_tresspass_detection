# camera_widget.py
import cv2
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import QTimer, Qt, QPoint, QEvent, QThread, pyqtSignal, pyqtSlot, QObject
from detectors.yolo_detector import detect_humans
from utils.geometry import is_inside_roi
from utils.alert import trigger_alert
from utils.logger import log_event
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox
import os
from datetime import datetime
from utils.email.sender import UniversalEmailSender
from time import time
import json
import traceback
from detectors.face_recognizer import FaceRecognizer
from PyQt5.QtCore import QThread, pyqtSignal



import cv2
import numpy as np
from ultralytics import YOLO
from queue import Queue
from threading import Lock

class DetectionManager(QObject):
    detection_complete = pyqtSignal(object, object, object)  # frame, humans, faces
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.frame_queue = Queue(maxsize=1)  # Only keep latest frame
        self.lock = Lock()
        self.thread = None
        
        # Initialize models in the background
        self.init_thread = QThread()
        self.init_thread.run = self._initialize_models
        self.init_thread.start()
        
    def _initialize_models(self):
        try:
            from detectors.face_recognizer import FaceRecognizer
            self.model = YOLO(os.path.join("models", "yolov8n.pt"))
            self.face_recognizer = FaceRecognizer()
            self.model.predict(source=np.zeros((640, 640, 3), dtype=np.uint8))  # Warmup
        except Exception as e:
            print(f"Error initializing models: {e}")
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = QThread()
            self.thread.run = self._detection_loop
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.quit()
            self.thread.wait()
    
    def process_frame(self, frame):
        """Add new frame to queue, dropping old frame if necessary"""
        if self.frame_queue.full():
            try:
                self.frame_queue.get_nowait()
            except:
                pass
        try:
            self.frame_queue.put_nowait(frame)
        except:
            pass
            
    def _detection_loop(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                if frame is None:
                    continue
                    
                # Process at 640x360 resolution
                process_frame = cv2.resize(frame, (640, 360))
                
                # Run YOLO detection
                results = self.model.predict(source=process_frame, conf=0.4, classes=[0], verbose=False)
                humans = []
                if len(results) > 0:
                    result = results[0]
                    boxes = result.boxes
                    if len(boxes) > 0:
                        for box in boxes:
                            # Get box coordinates
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            conf = float(box.conf[0].item())
                            humans.append({
                                "box": (x1, y1, x2, y2),
                                "confidence": conf
                            })
                
                # Run face recognition
                face_results = self.face_recognizer.recognize_faces(process_frame)
                
                self.detection_complete.emit(frame, humans, face_results)
                
            except Exception as e:
                continue

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
            subject = "[IMPORTANT] Security Alert - Danger Zone Intrusion Detected"
            body = f"""
SECURITY ALERT - IMMEDIATE ATTENTION REQUIRED

An unauthorized intrusion has been detected in the designated danger zone.

Details:
- Date: {self.date_str}
- Time: {self.time_str}
- Day: {self.day_str}
- Location: Robotic Test Cell, SEL
- Event Type: Human Intrusion in Danger Zone
An image of the intrusion is attached to this email for verification.

This is an automated security alert. Please take appropriate action immediately.

Best regards,
Security Monitoring System
                """
            headers = {
                "Importance": "High",
                "X-Priority": "1",
                "X-MSMail-Priority": "High",
                "List-Unsubscribe": f"<mailto:{self.sender}?subject=unsubscribe>"
            }
            
            sender.send_email(
                self.receivers,
                subject,
                body,
                attachments=[self.img_path],
                headers=headers
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
        self.detection_manager = DetectionManager()
        self.detection_manager.detection_complete.connect(self.handle_detection_result)
        self.last_processed_frame = None
        self.last_detection_results = None
        self.last_face_results = None
        self.frame_count = 0
        self.log_worker = None
        
        self.danger_mail_sender = "sender@gmail.com"
        self.danger_mail_password = "password"
        self.danger_mail_receivers = {
            "receiver1": {"email": "receiver@gmail.com", "enabled": True},
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
        self.face_recognizer = FaceRecognizer()
        

    def start(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Add CAP_DSHOW for Windows
            if not self.cap.isOpened():
                print("Error: Could not open video capture.")
                return
                
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)  # Set FPS
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer size
            
            # self.frame_count = 0  # Add frame counter for processing
            self.detection_enabled = True
            self.detection_manager.start()
            self.timer.start(33)  # ~30 FPS
            
        except Exception as e:
            print(f"Error starting camera: {str(e)}")


    def stop(self):
        if self.cap:
            self.detection_manager.stop()
            self.timer.stop()
            self.detection_enabled = False
            self.roi = None
            self.drawing = False
            self.allow_drawing = False
            try:
                self.cap.release()
                self.cap = None
            except:
                pass
        self.video_label.clear()
        self.video_label.setText("Video Feed")
            
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
    
    def _draw_rois_on_frame(self, frame):
        # Draw warning ROIs in green
        for roi in self.rois:
            (x1, y1), (x2, y2) = roi
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Draw danger ROIs in red
        for roi in self.danger_rois:
            (x1, y1), (x2, y2) = roi
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        # Draw current ROI being drawn
        if self.current_roi:
            x1, y1, x2, y2 = self.current_roi
            color = (0, 0, 255) if self.drawing_danger else (0, 255, 0)
            cv2.rectangle(frame, (min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2)), color, 2)
        return frame
    

    def update_frame(self):
        if not self.cap or not self.cap.isOpened():
            return
        try:
            ret, frame = self.cap.read()
            if not ret:
                return

            # Process detection every 3rd frame (but always draw latest results)
            self.frame_count += 1
            if self.detection_enabled and self.frame_count % 1 == 0:
                self.detection_manager.process_frame(frame.copy())

            # Always draw faces and person detections (even if results are from previous frame)
            frame = self._draw_detections(frame)

            # Draw ROIs on the frame
            frame = self._draw_rois_on_frame(frame)

            # Display frame
            self._display_frame(frame)

        except Exception as e:
            print(f"Error in update_frame: {e}")

    def _draw_detections(self, frame):
        frame_height, frame_width = frame.shape[:2]
        scale_x = frame_width / 640
        scale_y = frame_height / 360

        # Draw faces (yellow)
        for face in self.last_face_results or []:
            if not isinstance(face, dict) or "location" not in face or "name" not in face:
                continue
            top, right, bottom, left = face["location"]
            top_disp = int(top * scale_y)
            bottom_disp = int(bottom * scale_y)
            left_disp = int(left * scale_x)
            right_disp = int(right * scale_x)
            cv2.rectangle(frame, (left_disp, top_disp), (right_disp, bottom_disp), (0, 255, 255), 2)
            cv2.putText(frame, face["name"], (left_disp, top_disp - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Draw person detections (blue/green/red)
        current_time = time()
        for person in self.last_detection_results or []:
            if not isinstance(person, dict) or "box" not in person:
                continue
            box = person["box"]
            if not isinstance(box, (tuple, list)) or len(box) != 4:
                continue

            x1, y1, x2, y2 = box
            x1_disp = int(float(x1) * scale_x)
            x2_disp = int(float(x2) * scale_x)
            y1_disp = int(float(y1) * scale_y)
            y2_disp = int(float(y2) * scale_y)

            # Pass original (unscaled) box for matching
            self._handle_person_detection(frame, (x1_disp, y1_disp, x2_disp, y2_disp), current_time, (x1, y1, x2, y2))

        return frame

    def _handle_person_detection(self, frame, box, current_time, original_box=None):
        """Handle person detection and ROI intersection"""
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        # Use original_box for matching (in 640x360 space)
        if original_box is None:
            original_box = box
        ox1, oy1, ox2, oy2 = original_box
        ocenter_x = (ox1 + ox2) // 2
        ocenter_y = (oy1 + oy2) // 2

        # Get face name if any face is detected near this person (in 640x360 space)
        person_name = "Unknown"
        if self.last_face_results:
            for face in self.last_face_results:
                if not isinstance(face, dict) or "location" not in face or "name" not in face:
                    continue
                top, right, bottom, left = face["location"]
                # Face box in (left, top, right, bottom) order for IoU
                fx1, fy1, fx2, fy2 = left, top, right, bottom
                px1, py1, px2, py2 = ox1, oy1, ox2, oy2

                # Compute intersection
                ix1 = max(px1, fx1)
                iy1 = max(py1, fy1)
                ix2 = min(px2, fx2)
                iy2 = min(py2, fy2)
                iw = max(0, ix2 - ix1)
                ih = max(0, iy2 - iy1)
                intersection = iw * ih
                # Compute areas
                person_area = (px2 - px1) * (py2 - py1)
                face_area = (fx2 - fx1) * (fy2 - fy1)
                union = person_area + face_area - intersection
                iou = intersection / union if union > 0 else 0

                if iou > 0.15:  # If overlap is significant, consider it a match
                    person_name = face["name"]
                    break

        # Check warning zones
        for roi in self.rois:
            (rx1, ry1), (rx2, ry2) = roi
            if (rx1 <= center_x <= rx2 and ry1 <= center_y <= ry2):
                # Person is in warning zone
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Add name label to the frame (only for green)
                cv2.putText(frame, f"Name: {person_name}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                if current_time - self.last_alert_time > 5:  # 5 second cooldown
                    self.last_alert_time = current_time
                    trigger_alert()
                    log_event("Warning Zone Intrusion", frame, person_name)
                return True

        # Check danger zones
        for roi in self.danger_rois:
            (rx1, ry1), (rx2, ry2) = roi
            if (rx1 <= center_x <= rx2 and ry1 <= center_y <= ry2):
                # Person is in danger zone
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                # Add name label to the frame (only for red)
                cv2.putText(frame, f"Name: {person_name}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                if current_time - self.last_danger_alert_time > 10:  # 10 second cooldown
                    self.last_danger_alert_time = current_time
                    self.handle_danger_alert(frame)
                    log_event("Danger Zone Intrusion", frame, person_name)
                return True

        # Not in any zone: draw blue box, NO name label
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        return False

    def _display_frame(self, frame):
        """Efficiently display frame on video label"""
        label_size = self.video_label.size()
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate optimal display size
        scale = min(label_size.width() / frame_width, 
                    label_size.height() / frame_height)
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        
        # Resize efficiently
        display_frame = cv2.resize(frame, (new_width, new_height))
        rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        
        # Create QImage without copying data
        qt_image = QImage(rgb.data, new_width, new_height, 
                        new_width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setPixmap(pixmap)
            
    def mousePressEvent(self, event):
        if not self.allow_drawing:
            return
        if event.button() == Qt.LeftButton:
            pos = self.video_label.mapFromParent(event.pos())
            if self.video_label.rect().contains(pos):
                x, y = self.map_to_video(pos)
                self.drawing = True
                self.current_roi = [x, y, x, y]
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (self.allow_drawing and self.drawing and self.current_roi):
            return
        pos = self.video_label.mapFromParent(event.pos())
        if self.video_label.rect().contains(pos):
            x, y = self.map_to_video(pos)
            self.current_roi[2] = x
            self.current_roi[3] = y
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not (self.allow_drawing and self.drawing and self.current_roi):
            return
        if event.button() == Qt.LeftButton:
            pos = self.video_label.mapFromParent(event.pos())
            if self.video_label.rect().contains(pos):
                x, y = self.map_to_video(pos)
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
                event.accept()
                return
        super().mouseReleaseEvent(event)
            
    def map_to_video(self, pos):
        label_size = self.video_label.size()
        if not self.cap:
            return 0, 0
        ret, frame = self.cap.read()
        if not ret:
            return 0, 0
            
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate scale and offsets based on aspect ratio
        target_ratio = frame_width / frame_height
        label_ratio = label_size.width() / label_size.height()
        
        if label_ratio > target_ratio:
            # Label is wider than video
            scale = label_size.height() / frame_height
            new_width = int(frame_width * scale)
            new_height = label_size.height()
            x_offset = (label_size.width() - new_width) // 2
            y_offset = 0
        else:
            # Label is taller than video
            scale = label_size.width() / frame_width
            new_width = label_size.width()
            new_height = int(frame_height * scale)
            x_offset = 0
            y_offset = (label_size.height() - new_height) // 2
        
        # Adjust click coordinates
        x = pos.x() - x_offset
        y = pos.y() - y_offset
        
        # Convert back to original frame coordinates
        x = int((x / scale) if scale > 0 else 0)
        y = int((y / scale) if scale > 0 else 0)
        
        # Ensure coordinates are within frame bounds
        x = max(0, min(frame_width - 1, x))
        y = max(0, min(frame_height - 1, y))
        
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
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Danger!")
        msg.setText("Robot stopped")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setModal(False)  # <-- This makes it non-blocking
        msg.show()
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
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning")
            msg.setText("No active email receivers configured!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setModal(False)
            msg.show()
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
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Email Sent")
        msg.setText("Danger alert email sent successfully!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setModal(False)  # Non-blocking
        msg.show()
                
    def show_email_error(self, error_msg):
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Danger Mail Error")
        msg.setText(f"Failed to send danger email:\n{error_msg}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setModal(False)  # Non-blocking
        msg.show()
        
    def handle_detection_result(self, frame, humans, face_results):
        """Handle detection results from detection manager"""
        self.last_detection_results = humans
        self.last_face_results = face_results
        self.last_processed_frame = frame
