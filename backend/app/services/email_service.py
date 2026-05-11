"""Email service for sending transactional emails via Google SMTP."""

import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    """
    Async email service using Google SMTP (Gmail).

    Reads configuration from environment variables:
    - SMTP_HOST: smtp.gmail.com (default)
    - SMTP_PORT: 587 (default)
    - SMTP_USERNAME: Gmail address
    - SMTP_PASSWORD: Gmail App Password (not account password)
    - SMTP_FROM: Sender email address (defaults to SMTP_USERNAME)
    """

    def __init__(
        self,
        host: str = "",
        port: int = 0,
        username: str = "",
        password: str = "",
        from_addr: str = "",
    ) -> None:
        self.host = host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = port or int(os.getenv("SMTP_PORT", "587"))
        self.username = username or os.getenv("SMTP_USERNAME", "")
        self.password = password or os.getenv("SMTP_PASSWORD", "")
        self.from_addr = from_addr or os.getenv("SMTP_FROM") or self.username

    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        """
        Send an email asynchronously via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.from_addr
        message["To"] = to_email
        message.attach(MIMEText(body, "plain", "utf-8"))

        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            start_tls=True,
            username=self.username,
            password=self.password,
        )

    async def send_temp_password(self, to_email: str, temp_password: str) -> None:
        """
        Send temporary password reset email.

        Args:
            to_email: User's email address
            temp_password: Temporary password string
        """
        subject = "Your Temporary Password"
        body = (
            f"Hello,\n\n"
            f"Your temporary password is: {temp_password}\n\n"
            f"This password will expire in 1 hour.\n"
            f"Please log in and change your password immediately.\n\n"
            f"If you did not request this, please ignore this email.\n"
        )
        await self.send_email(to_email, subject, body)
