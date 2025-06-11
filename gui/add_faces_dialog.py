from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel,
    QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import os
import cv2
import shutil

class CameraThread(QThread):
    frame_captured = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if ret:
                self.frame_captured.emit(frame)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()

class AddFacesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Face")
        self.setMinimumWidth(400)
        self.captured_image = None
        self.camera_thread = None

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        form_layout.addRow("Person Name:", self.name_edit)

        # Camera preview and buttons
        self.image_label = QLabel("No image captured.")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(320, 240)
        form_layout.addRow("Preview:", self.image_label)

        self.take_picture_btn = QPushButton("Take Picture")
        self.take_picture_btn.clicked.connect(self.start_camera)
        self.capture_btn = QPushButton("Capture")
        self.capture_btn.setEnabled(False)
        self.capture_btn.clicked.connect(self.capture_image)
        self.stop_camera_btn = QPushButton("Stop Camera")
        self.stop_camera_btn.setEnabled(False)
        self.stop_camera_btn.clicked.connect(self.stop_camera)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.take_picture_btn)
        btn_layout.addWidget(self.capture_btn)
        btn_layout.addWidget(self.stop_camera_btn)
        form_layout.addRow("", btn_layout)

        layout.addLayout(form_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_face)
        layout.addWidget(self.save_btn)

    def start_camera(self):
        self.camera_thread = CameraThread()
        self.camera_thread.frame_captured.connect(self.update_preview)
        self.camera_thread.start()
        self.take_picture_btn.setEnabled(False)
        self.capture_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(True)
        self.status_label.setText("Camera started. Click 'Capture' to take a photo.")

    def update_preview(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image).scaled(
            self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio
        )
        self.image_label.setPixmap(pixmap)
        self.current_frame = frame

    def capture_image(self):
        if hasattr(self, 'current_frame') and self.current_frame is not None:
            self.captured_image = self.current_frame.copy()
            self.status_label.setText("Image captured. Click 'Save' to store.")
            # Show captured image
            rgb_image = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image).scaled(
                self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio
            )
            self.image_label.setPixmap(pixmap)
            self.capture_btn.setEnabled(False)
            self.take_picture_btn.setEnabled(True)
            self.stop_camera()
        else:
            QMessageBox.warning(self, "Capture Error", "No frame to capture.")

    def stop_camera(self):
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        self.capture_btn.setEnabled(False)
        self.stop_camera_btn.setEnabled(False)
        self.take_picture_btn.setEnabled(True)
        self.status_label.setText("Camera stopped.")

    def save_face(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please provide a name.")
            return
        if self.captured_image is None:
            QMessageBox.warning(self, "Input Error", "Please capture an image first.")
            return

        faces_dir = os.path.join(os.getcwd(), "known_faces", name)
        os.makedirs(faces_dir, exist_ok=True)

        # Find a unique filename
        base_filename = f"{name}.jpg"
        dest_path = os.path.join(faces_dir, base_filename)
        i = 1
        while os.path.exists(dest_path):
            base_filename = f"{name}_{i}.jpg"
            dest_path = os.path.join(faces_dir, base_filename)
            i += 1

        try:
            # Save directly in BGR format (OpenCV's default)
            cv2.imwrite(dest_path, self.captured_image)
            self.status_label.setText(f"Face for '{name}' saved as {base_filename}!")
            self.name_edit.clear()
            self.captured_image = None
            self.image_label.setText("No image captured.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save face: {e}")
            
    def closeEvent(self, event):
        self.stop_camera()
        event.accept()