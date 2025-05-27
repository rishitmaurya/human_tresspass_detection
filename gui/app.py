# app.py
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from gui.camera_widget import CameraWidget

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Human Trespass Detection System")
        self.setGeometry(100, 100, 1000, 700)

        self.camera_widget = CameraWidget()

        start_button = QPushButton("Start Detection")
        stop_button = QPushButton("Stop Detection")

        start_button.clicked.connect(self.camera_widget.start)
        stop_button.clicked.connect(self.camera_widget.stop)

        layout = QVBoxLayout()
        layout.addWidget(self.camera_widget)
        layout.addWidget(start_button)
        layout.addWidget(stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
