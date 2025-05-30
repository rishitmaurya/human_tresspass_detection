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
        self.draw_menu = None
        self.menubar = self.menuBar()

        start_button = QPushButton("Start Detection")
        stop_button = QPushButton("Stop Detection")

        start_button.clicked.connect(self.on_start_detection)
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

        # File menu
        file_menu = self.menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = self.menubar.addMenu("View")
        log_action = QAction("Intruders Log", self)
        log_action.triggered.connect(self.show_intruders_log)
        view_menu.addAction(log_action)

        # Help menu
        help_menu = self.menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def add_draw_menu(self):
        if not self.draw_menu:
            self.draw_menu = self.menubar.addMenu("Draw")
            draw_action = QAction("Draw ROI", self)
            draw_action.triggered.connect(self.camera_widget.enable_drawing)
            self.draw_menu.addAction(draw_action)

    def on_start_detection(self):
        self.camera_widget.start()
        self.add_draw_menu()
        
    def show_intruders_log(self):
        try:
            with open("logs/alert_log.txt", "r") as f:
                log_content = f.read()
            QMessageBox.information(
                self,
                "Intruders Log",
                log_content if log_content else "No intrusions detected yet."
            )
        except FileNotFoundError:
            QMessageBox.information(
                self,
                "Intruders Log",
                "No log file found."
            )

    def show_about_dialog(self):
        QMessageBox.information(
            self,
            "About",
            "Human Trespass Detection System\nDeveloped using PyQt5, OpenCV, and YOLOv8."
        )
