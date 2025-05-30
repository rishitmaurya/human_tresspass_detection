# app.py
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QAction, QMenuBar, QMessageBox, QFileDialog
from gui.camera_widget import CameraWidget
from PyQt5.QtCore import Qt, QUrl
import os
from utils.logger import IMAGES_DIR
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
        """Downloads all intrusion data including CSV and images"""
        try:
            import shutil
            import tempfile
            import csv
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"intrusion_data_{timestamp}.zip"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create CSV file with image references
                csv_path = os.path.join(temp_dir, "intrusion_log.csv")
                with open(csv_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["S.No", "Date", "Time", "Event", "Image File"])
                    
                    # Get data from HTML table
                    from bs4 import BeautifulSoup
                    with open(os.path.join("logs", "alert_log.html"), 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        rows = soup.find_all('tr')[1:]  # Skip header row
                        
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 5:
                                sno = cols[0].text.strip()
                                date = cols[1].text.strip()
                                time = cols[2].text.strip()
                                event = cols[3].text.strip()
                                img_tag = cols[4].find('img')
                                img_file = img_tag['src'].split('/')[-1] if img_tag else "No image"
                                writer.writerow([sno, date, time, event, img_file])
                
                # Create a folder for the export
                export_dir = os.path.join(temp_dir, "intrusion_data")
                os.makedirs(export_dir)
                
                # Copy CSV and create images folder
                shutil.copy2(csv_path, export_dir)
                images_export_dir = os.path.join(export_dir, "images")
                shutil.copytree(images_dir, images_export_dir)
                
                # Create zip file
                zip_path = os.path.join(temp_dir, zip_name)
                shutil.make_archive(zip_path[:-4], 'zip', temp_dir, "intrusion_data")
                
                # Show save file dialog
                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Intrusion Data",
                    zip_name,
                    "ZIP Files (*.zip)"
                )
                
                if save_path:
                    shutil.copy2(zip_path, save_path)
                    QMessageBox.information(
                        self, 
                        "Success", 
                        "Intrusion data downloaded successfully!\n\n"
                        "The ZIP file contains:\n"
                        "- CSV file with all intrusion data\n"
                        "- Folder with all captured images"
                    )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not download data: {str(e)}")

    def show_about_dialog(self):
        QMessageBox.information(
            self,
            "About",
            "Human Trespass Detection System\nDeveloped using PyQt5, OpenCV, and YOLOv8."
        )
