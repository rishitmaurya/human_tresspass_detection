from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QMessageBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFont
import os
import shutil
from detectors.face_recognizer import FaceRecognizer

class FaceCard(QFrame):
    def __init__(self, name, image_path, parent_dialog):
        super().__init__()
        self.name = name
        self.image_path = image_path
        self.parent_dialog = parent_dialog
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.setFixedSize(200, 280)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #1a237e;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setFixedSize(160, 160)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
        
        # Load and display image
        self.load_image()
        
        # Name label
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setWordWrap(True)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        delete_btn.clicked.connect(self.delete_face)
        
        layout.addWidget(self.image_label)
        layout.addWidget(name_label)
        layout.addWidget(delete_btn)
        layout.addStretch()
    
    def load_image(self):
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    160, 160, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("Image\nNot Available")
        else:
            self.image_label.setText("Image\nNot Found")
    
    def delete_face(self):
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to delete '{self.name}' from known faces?\n\n"
            "This will remove all images and data for this person.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Remove the entire person's directory
                person_dir = os.path.dirname(self.image_path)
                if os.path.exists(person_dir):
                    shutil.rmtree(person_dir)
                
                # Update face recognizer (reload encodings)
                face_recognizer = FaceRecognizer()
                face_recognizer.load_known_faces()
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"'{self.name}' has been deleted successfully!"
                )
                
                # Refresh the parent dialog
                self.parent_dialog.refresh_faces()
                
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Failed to delete '{self.name}':\n{str(e)}"
                )

class ShowFacesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Known Faces")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        
        self.setup_ui()
        self.load_faces()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Known Faces")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #1a237e;")
        
        self.count_label = QLabel()
        self.count_label.setFont(QFont("Arial", 12))
        self.count_label.setStyleSheet("color: #666;")
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a237e;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #283593;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_faces)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll area for faces
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(scroll_area)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def load_faces(self):
        # Clear existing cards
        self.clear_layout()
        
        known_faces_dir = "known_faces"
        if not os.path.exists(known_faces_dir):
            self.show_no_faces_message()
            return
        
        face_cards = []
        
        # Get all person directories
        for person_name in os.listdir(known_faces_dir):
            person_dir = os.path.join(known_faces_dir, person_name)
            if os.path.isdir(person_dir):
                # Find the first image file in the person's directory
                image_files = [f for f in os.listdir(person_dir) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
                
                if image_files:
                    image_path = os.path.join(person_dir, image_files[0])
                    face_card = FaceCard(person_name, image_path, self)
                    face_cards.append(face_card)
        
        if not face_cards:
            self.show_no_faces_message()
            return
        
        # Arrange cards in grid
        cols = 4  # Number of columns
        for i, card in enumerate(face_cards):
            row = i // cols
            col = i % cols
            self.scroll_layout.addWidget(card, row, col)
        
        # Add stretch to fill remaining space
        self.scroll_layout.setRowStretch(len(face_cards) // cols + 1, 1)
        self.scroll_layout.setColumnStretch(cols, 1)
        
        # Update count
        self.count_label.setText(f"({len(face_cards)} faces)")
    
    def clear_layout(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def show_no_faces_message(self):
        no_faces_label = QLabel("No known faces found.\n\nUse 'Add Faces' to add people to the recognition database.")
        no_faces_label.setAlignment(Qt.AlignCenter)
        no_faces_label.setFont(QFont("Arial", 14))
        no_faces_label.setStyleSheet("""
            QLabel {
                color: #666;
                background-color: white;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 40px;
                margin: 20px;
            }
        """)
        
        self.scroll_layout.addWidget(no_faces_label, 0, 0, 1, 4)
        self.count_label.setText("(0 faces)")
    
    def refresh_faces(self):
        self.load_faces()