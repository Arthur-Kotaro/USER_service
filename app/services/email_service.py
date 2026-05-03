# app/services/email_service.py
import smtplib
import ssl
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.yandex.ru")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.enabled = bool(self.smtp_user and self.smtp_password)
        self.use_ssl = self.smtp_port == 465  # Яндекс использует SSL
    
    async def send_temp_password(self, to_email: str, temp_password: str, username: str) -> bool:
        """Отправка временного пароля на почту"""
        if not self.enabled:
            logger.warning(f"Email service disabled. Would send temp password to {to_email}: {temp_password}")
            return True
        
        subject = "Восстановление доступа к системе"
        body = f"""
Здравствуйте, {username}!

Вы запросили восстановление доступа к системе.

Ваш временный пароль: {temp_password}

Пожалуйста, войдите в систему с этим паролем и сразу измените его.
Временный пароль действителен в течение 24 часов.

Если вы не запрашивали восстановление доступа, проигнорируйте это письмо.

С уважением,
Команда поддержки
"""
        
        return await self._send_email(to_email, subject, body)
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # Для SSL (порт 465)
            if self.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # Для TLS (порт 587)
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
