from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLineEdit, QPushButton, QComboBox, QCheckBox, 
                            QSpinBox, QMessageBox, QTextEdit, QFileDialog)
from .sender import UniversalEmailSender, EmailServerConfig
import logging
import os

logger = logging.getLogger(__name__)

class EmailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.attachments = []
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Send Email Report")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        # Main layout
        layout = QVBoxLayout()
        form = QFormLayout()

        # Email provider selection
        self.provider = QComboBox()
        self.provider.addItems([
            'gmail', 'yahoo', 'outlook', 'office365', 
            'hotmail', 'company', 'custom'
        ])
        self.provider.currentTextChanged.connect(self.on_provider_changed)

        # Basic fields
        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.recipient = QLineEdit()
        self.subject = QLineEdit()

        # Email body
        self.body = QTextEdit()
        self.body.setMinimumHeight(150)
        self.body.setPlaceholderText("Enter email content here...")

        # Attachment section
        attachment_layout = QHBoxLayout()
        self.attachment_label = QLineEdit()
        self.attachment_label.setReadOnly(True)
        self.attachment_label.setPlaceholderText("No file selected")
        self.attach_btn = QPushButton("Add Attachment")
        self.attach_btn.clicked.connect(self.add_attachment)
        attachment_layout.addWidget(self.attachment_label)
        attachment_layout.addWidget(self.attach_btn)

        # Server settings (for custom/company)
        self.server_settings = {
            'server': QLineEdit(),
            'port': QSpinBox(),
            'tls': QCheckBox("Use TLS"),
            'ssl': QCheckBox("Use SSL"),
            'domain': QLineEdit()
        }
        self.server_settings['port'].setRange(1, 65535)
        self.server_settings['port'].setValue(587)

        # Add fields to form
        form.addRow("Email Provider:", self.provider)
        form.addRow("Your Email:", self.email)
        form.addRow("Password:", self.password)
        form.addRow("Recipient:", self.recipient)
        form.addRow("Subject:", self.subject)
        form.addRow("Message:", self.body)
        form.addRow("Attachment:", attachment_layout)
        form.addRow("SMTP Server:", self.server_settings['server'])
        form.addRow("SMTP Port:", self.server_settings['port'])
        form.addRow(self.server_settings['tls'])
        form.addRow(self.server_settings['ssl'])
        form.addRow("Domain:", self.server_settings['domain'])

        # Buttons
        buttons = QHBoxLayout()
        self.send_btn = QPushButton("Send")
        self.cancel_btn = QPushButton("Cancel")
        self.send_btn.clicked.connect(self.send_email)
        self.cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self.send_btn)
        buttons.addWidget(self.cancel_btn)

        # Assemble layout
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)
        
        # Initial state
        self.on_provider_changed(self.provider.currentText())
        
    def on_provider_changed(self, provider: str):
        """Show/hide server settings based on provider selection"""
        # Show server settings only for custom and company email
        show_server = provider in ['custom', 'company']
        
        # Toggle visibility of server settings
        for widget in self.server_settings.values():
            widget.setVisible(show_server)
            
        # Pre-fill server settings for company email
        if provider == 'company':
            self.server_settings['tls'].setChecked(True)
            self.server_settings['ssl'].setChecked(False)
        
        # Update dialog size to fit content
        self.adjustSize()

    def add_attachment(self):
        """Allow user to select file attachment"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Attachment",
            "",
            "All Files (*);;ZIP Files (*.zip);;PDF Files (*.pdf)"
        )
        if file_path:
            self.attachments.append(file_path)
            display_name = os.path.basename(file_path)
            current_text = self.attachment_label.text()
            if current_text and current_text != "No file selected":
                self.attachment_label.setText(f"{current_text}, {display_name}")
            else:
                self.attachment_label.setText(display_name)

    def send_email(self):
        """Send email with current settings"""
        try:
            if not self.email.text() or not self.password.text() or not self.recipient.text():
                QMessageBox.warning(self, "Error", "Please fill in all required fields.")
                return

            provider = self.provider.currentText()
            
            # Create appropriate sender
            if provider in ['custom', 'company']:
                config = EmailServerConfig(
                    smtp_server=self.server_settings['server'].text(),
                    smtp_port=self.server_settings['port'].value(),
                    use_tls=self.server_settings['tls'].isChecked(),
                    use_ssl=self.server_settings['ssl'].isChecked(),
                    domain=self.server_settings['domain'].text() or None
                )
                sender = UniversalEmailSender(
                    self.email.text(),
                    self.password.text(),
                    'custom',
                    config
                )
            else:
                sender = UniversalEmailSender(
                    self.email.text(),
                    self.password.text(),
                    provider
                )

            # Send email with attachment
            sender.send_email(
                [self.recipient.text()],
                self.subject.text() or "No Subject",
                self.body.toPlainText() or "No content",
                self.attachments if self.attachments else None
            )
            
            QMessageBox.information(self, "Success", "Email sent successfully!")
            self.accept()
        
        except Exception as e:
            if "5.7.9" in str(e) and "gmail" in self.provider.currentText().lower():
                QMessageBox.critical(
                    self, 
                    "Gmail Authentication Error",
                    "You need to use an App Password with Gmail:\n\n"
                    "1. Go to Google Account Settings\n"
                    "2. Enable 2-Step Verification if not enabled\n"
                    "3. Go to Security → App Passwords\n"
                    "4. Generate new App Password\n"
                    "5. Use that 16-character password here\n\n"
                    "For more info: https://support.google.com/mail/?p=InvalidSecondFactor"
                )
            else:
                QMessageBox.critical(self, "Error", f"Failed to send email: {str(e)}")