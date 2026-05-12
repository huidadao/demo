"""Email service for sending transactional emails via Google SMTP."""

import os
import aiosmtplib
from aiosmtplib.errors import SMTPAuthenticationError, SMTPException
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

        if not self.username or not self.password:
            raise RuntimeError(
                "SMTP credentials not configured. "
                "Please set SMTP_USERNAME and SMTP_PASSWORD environment variables "
                "or create a .env file with these values."
            )

    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        """
        Send an email asynchronously via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body

        Raises:
            SMTPAuthenticationError: If SMTP credentials are invalid.
            SMTPException: If any other SMTP error occurs.
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.from_addr
        message["To"] = to_email
        message.attach(MIMEText(body, "plain", "utf-8"))

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                start_tls=True,
                username=self.username,
                password=self.password,
            )
        except SMTPAuthenticationError as exc:
            raise SMTPAuthenticationError(
                "SMTP authentication failed. Please check your SMTP_USERNAME and "
                "SMTP_PASSWORD. If using Gmail, ensure you are using an App Password, "
                "not your account password. Enable 2FA and generate an App Password at: "
                "https://myaccount.google.com/apppasswords"
            ) from exc

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

    async def send_verification_code(self, to_email: str, code: str, options: list) -> None:
        """
        Send email verification code with CAPTCHA-style options.

        Args:
            to_email: User's email address
            code: The correct verification code (2-digit number)
            options: List of 3 code options to display in the email
        """
        subject = "Verify Your Email Address"
        options_str = "   ".join([f"[{opt}]" for opt in options])
        body = (
            f"Hello,\n\n"
            f"Thank you for registering. Please verify your email address.\n\n"
            f"Your verification code is: {code}\n\n"
            f"Options: {options_str}\n\n"
            f"Please click the correct number button on the verification page.\n\n"
            f"This code will expire in 30 minutes.\n\n"
            f"If you did not request this, please ignore this email.\n"
        )
        await self.send_email(to_email, subject, body)
