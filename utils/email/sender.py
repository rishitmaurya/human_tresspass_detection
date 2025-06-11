from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib
import ssl
import os
from typing import List, Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmailServerConfig:
    """Email server configuration"""
    smtp_server: str
    smtp_port: int
    use_tls: bool = True
    use_ssl: bool = False
    domain: Optional[str] = None
    auth_required: bool = True

class UniversalEmailSender:
    """A flexible email sender that works with any SMTP server"""
    
    # Common email provider configurations
    PROVIDER_CONFIGS: Dict[str, EmailServerConfig] = {
        'gmail': EmailServerConfig('smtp.gmail.com', 587, True),
        'yahoo': EmailServerConfig('smtp.mail.yahoo.com', 587, True),
        'outlook': EmailServerConfig('smtp-mail.outlook.com', 587, True),
        'office365': EmailServerConfig('smtp.office365.com', 587, True),
        'hotmail': EmailServerConfig('smtp.live.com', 587, True),
        'aol': EmailServerConfig('smtp.aol.com', 587, True),
        'zoho': EmailServerConfig('smtp.zoho.com', 587, True),
    }

    def __init__(self, 
                 email: str, 
                 password: str, 
                 provider: str = 'custom',
                 custom_config: Optional[EmailServerConfig] = None):
        """
        Initialize email sender
        Args:
            email: Email address
            password: Email password or app-specific password
            provider: Provider name from PROVIDER_CONFIGS or 'custom'
            custom_config: Required if provider is 'custom'
        """
        self.email = email
        self.password = password
        
        if provider == 'custom' and custom_config is None:
            raise ValueError("custom_config required when provider is 'custom'")
            
        self.config = (custom_config if provider == 'custom' 
                      else self.PROVIDER_CONFIGS.get(provider.lower()))
        
        if not self.config:
            raise ValueError(f"Unknown provider: {provider}")

    def _create_message(self, 
                       to_emails: List[str], 
                       subject: str, 
                       body: str, 
                       attachments: Optional[List[str]] = None,
                       headers: Optional[Dict[str, str]] = None ) -> MIMEMultipart:
        """Create email message with attachments"""
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        
        if headers:
            for key, value in headers.items():
                msg[key] = value
        
        msg.attach(MIMEText(body, 'plain'))

        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read())
                        part.add_header('Content-Disposition', 'attachment',
                                      filename=os.path.basename(file_path))
                        msg.attach(part)
                except Exception as e:
                    logger.error(f"Failed to attach file {file_path}: {e}")
        
        return msg

    def send_email(self, 
                  to_emails: List[str], 
                  subject: str, 
                  body: str, 
                  attachments: Optional[List[str]] = None,
                  headers: Optional[Dict[str, str]] = None
                  ) -> bool:
        """
        Send email with optional attachments
        Returns:
            bool: True if email was sent successfully
        """
        if not isinstance(to_emails, list):
            to_emails = [to_emails]

        msg = self._create_message(to_emails, subject, body, attachments, headers)
        
        try:
            # Choose SMTP class based on SSL setting
            smtp_class = smtplib.SMTP_SSL if self.config.use_ssl else smtplib.SMTP
            
            # Create connection
            with smtp_class(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls and not self.config.use_ssl:
                    server.starttls(context=ssl.create_default_context())
                
                # Handle authentication
                if self.config.auth_required:
                    username = self.email
                    if self.config.domain:
                        username = f"{self.config.domain}\\{username}"
                    server.login(username, self.password)
                
                # Send email
                server.send_message(msg)
                logger.info(f"Email sent successfully to {', '.join(to_emails)}")
                return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise

    @classmethod
    def create_company_sender(cls, 
                            email: str,
                            password: str,
                            smtp_server: str,
                            smtp_port: int,
                            domain: Optional[str] = None,
                            use_tls: bool = True,
                            use_ssl: bool = False) -> 'UniversalEmailSender':
        """Create sender for company email"""
        config = EmailServerConfig(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            use_tls=use_tls,
            use_ssl=use_ssl,
            domain=domain
        )
        return cls(email, password, 'custom', config)

    @classmethod
    def create_temp_mail_sender(cls,
                              email: str,
                              password: str,
                              smtp_server: str,
                              smtp_port: int) -> 'UniversalEmailSender':
        """Create sender for temporary email services"""
        config = EmailServerConfig(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            use_tls=False,
            use_ssl=False,
            auth_required=True
        )
        return cls(email, password, 'custom', config)