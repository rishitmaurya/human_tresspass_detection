# app.py
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QAction, QMenuBar, QMessageBox
from gui.camera_widget import CameraWidget
from PyQt5.QtCore import Qt, QUrl
import os
from PyQt5.QtWebEngineWidgets import QWebEngineView

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
            log_path = os.path.join("logs", "alert_log.html")
            if os.path.exists(log_path):
                self.log_window = QWidget()
                self.log_window.setWindowTitle("Intruders Log")
                self.log_window.setGeometry(200, 200, 800, 600)

                # Create web view to display HTML
                web_view = QWebEngineView()
                web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(log_path)))

                # Add download button
                download_button = QPushButton("Download Images")
                download_button.clicked.connect(lambda: self.download_images(IMAGES_DIR))

                # Add to layout
                layout = QVBoxLayout()
                layout.addWidget(web_view)
                layout.addWidget(download_button)
                self.log_window.setLayout(layout)
                self.log_window.show()
            else:
                QMessageBox.information(self, "Intruders Log", "No intrusions detected yet.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open log: {str(e)}")

    def download_images(self, images_dir):
            """Downloads all images from the logs/images directory"""
            try:
                import shutil
                import tempfile
                from datetime import datetime

                # Create a zip file with all images
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_name = f"intrusion_images_{timestamp}.zip"
                
                # Create temp directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = os.path.join(temp_dir, zip_name)
                    
                    # Create zip file
                    shutil.make_archive(zip_path[:-4], 'zip', images_dir)
                    
                    # Show save file dialog
                    from PyQt5.QtWidgets import QFileDialog
                    save_path, _ = QFileDialog.getSaveFileName(
                        self,
                        "Save Images",
                        zip_name,
                        "ZIP Files (*.zip)"
                    )
                    
                    if save_path:
                        shutil.copy2(zip_path, save_path)
                        QMessageBox.information(self, "Success", "Images downloaded successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not download images: {str(e)}")

    def show_about_dialog(self):
        QMessageBox.information(
            self,
            "About",
            "Human Trespass Detection System\nDeveloped using PyQt5, OpenCV, and YOLOv8."
        )
