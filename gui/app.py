# app.py
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QAction, QMenuBar, QMessageBox
from gui.camera_widget import CameraWidget
from PyQt5.QtCore import Qt

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
        
        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_about_dialog(self):
        QMessageBox.information(
            self,
            "About",
            "Human Trespass Detection System\nDeveloped using PyQt5, OpenCV, and YOLOv8."
        )
