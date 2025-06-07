# app.py
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                            QWidget, QLabel, QSizePolicy, QAction, QMenuBar, QMessageBox, QFileDialog)
from gui.camera_widget import CameraWidget
from PyQt5.QtCore import Qt, QUrl
import os
from utils.logger import IMAGES_DIR
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from utils.email.dialog import EmailDialog
import tempfile
from datetime import datetime

class CustomWebPage(QWebEnginePage):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() == 'download':
            self.main_window.download_data(IMAGES_DIR)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)
    
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Human Trespass Detection System")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)

        self.setStyleSheet("""
        QMainWindow {
            background-color: #f0f2f5;
        }
        QPushButton {
            background-color: #1a237e;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            min-width: 120px;
            margin: 5px;
        }
        QPushButton:hover {
            background-color: #283593;
        }
        QPushButton:pressed {
            background-color: #0d1c73;
        }
        QPushButton#stopButton {
            background-color: #c62828;
        }
        QPushButton#stopButton:hover {
            background-color: #d32f2f;
        }
        """)

        self.camera_widget = CameraWidget()
        self.camera_widget.setSizePolicy(
            QSizePolicy.Expanding, 
            QSizePolicy.Expanding
        )
        self.camera_widget.setMinimumSize(640, 480)
        
        self.draw_menu = None
        self.menubar = self.menuBar()
        self.menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1a237e;
                color: white;
                padding: 2px;
            }
            QMenuBar::item {
                padding: 8px 12px;
                margin: 0px;
            }
            QMenuBar::item:selected {
                background-color: #283593;
            }
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #e8eaf6;
                color: #1a237e;
            }
        """)

        # Create buttons with improved layout
        button_container = QWidget()
        button_container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 10, 20, 20)
        button_layout.setSpacing(10)

        start_button = QPushButton("▶ Start Detection")
        stop_button = QPushButton("⏹ Stop Detection")
        stop_button.setObjectName("stopButton")
        
        for button in (start_button, stop_button):
            button.setSizePolicy(
                QSizePolicy.Minimum,
                QSizePolicy.Fixed
            )

        button_layout.addStretch()
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addStretch()
        button_container.setLayout(button_layout)

        start_button.clicked.connect(self.on_start_detection)
        stop_button.clicked.connect(self.camera_widget.stop)

        # Main layout with margins
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(self.camera_widget, stretch=1)
        layout.addWidget(button_container)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.create_menu()

    def create_menu(self):

        # File menu
        file_menu = self.menubar.addMenu("File")
        
        # Email action
        email_action = QAction("Send Email Report", self)
        email_action.setStatusTip("Send intrusion report via email")
        email_action.triggered.connect(self.show_email_dialog)
        file_menu.addAction(email_action)

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
                self.log_window.setGeometry(200, 200, 1000, 700)
                self.log_window.setStyleSheet("""
                    QWidget {
                        background-color: #f0f2f5;
                    }
                """)

                # Create web view with custom page
                web_view = QWebEngineView()
                custom_page = CustomWebPage(web_view, self)
                web_view.setPage(custom_page)
                web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(log_path)))

                # Add padding around the web view
                layout = QVBoxLayout()
                layout.setContentsMargins(20, 20, 20, 20)
                layout.addWidget(web_view)
                self.log_window.setLayout(layout)
                self.log_window.show()
            else:
                QMessageBox.information(self, "Intruders Log", "No intrusions detected yet.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open log: {str(e)}")
            
    def handle_url_change(self, url):
        if url.toString().startswith('download://'):
            self.download_data(IMAGES_DIR)
            
    def handle_download(self, download):
        """Handle downloads from the WebEngine"""
        download.accept()

    def download_data(self, images_dir):
        """Downloads all intrusion data including CSV and images"""
        try:
            import shutil
            import tempfile
            import csv
            from datetime import datetime
            from bs4 import BeautifulSoup
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"intrusion_data_{timestamp}.zip"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                export_dir = os.path.join(temp_dir, "intrusion_data")
                os.makedirs(export_dir)
                
                # Create CSV from HTML table
                log_path = os.path.join("logs", "alert_log.html")
                csv_path = os.path.join(export_dir, "intrusion_log.csv")
                
                with open(log_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    table = soup.find('table')
                    
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        
                        # Write header
                        header_row = table.find('tr')
                        headers = [th.text.strip() for th in header_row.find_all('th')]
                        headers[-1] = 'Image File'  # Change last header from 'Evidence' to 'Image File'
                        writer.writerow(headers)
                        
                        # Write data rows
                        for row in table.find_all('tr')[1:]:  # Skip header row
                            cols = row.find_all('td')
                            if cols:  # If row has data
                                # Get text from first 4 columns
                                row_data = [col.text.strip() for col in cols[:-1]]
                                
                                # Get image filename from the img tag if it exists
                                img_tag = cols[-1].find('img')
                                if img_tag and 'src' in img_tag.attrs:
                                    img_filename = os.path.basename(img_tag['src'])
                                    row_data.append(img_filename)
                                else:
                                    row_data.append('No image')
                                    
                                writer.writerow(row_data)
                    
                # Copy images
                images_export_dir = os.path.join(export_dir, "images")
                if os.path.exists(images_dir):
                    shutil.copytree(images_dir, images_export_dir)
                
                # Create zip file
                zip_path = os.path.join(temp_dir, zip_name)
                shutil.make_archive(zip_path[:-4], 'zip', export_dir)
                
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
                        "- CSV file with intrusion data including image references\n"
                        "- Folder with captured images"
                    )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not download data: {str(e)}")

    def show_email_dialog(self):
        """Show email dialog"""
        try:
            dialog = EmailDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Could not open email dialog: {str(e)}"
            )

    def show_about_dialog(self):
        QMessageBox.information(
            self,
            "About",
            "Human Trespass Detection System\nDeveloped by \n \t - Rishit Maurya"
        )