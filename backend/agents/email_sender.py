import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
import os
from config import settings

SMTP_CONFIGS = {
    "gmail": {"host": "smtp.gmail.com", "port": 587, "use_tls": True},
    "icloud": {"host": "smtp.mail.me.com", "port": 587, "use_tls": True},
    "smtp": {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT, "use_tls": True},
}

async def send_application_email(
    to_email: str,
    subject: str,
    body: str,
    cv_path: str,
    cover_letter_path: str,
    contact_name: str = "",
) -> bool:
    cfg = SMTP_CONFIGS.get(settings.EMAIL_PROVIDER, SMTP_CONFIGS["gmail"])

    msg = MIMEMultipart()
    msg["From"] = formataddr((settings.EMAIL_DISPLAY_NAME, settings.EMAIL_ADDRESS))
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    for path, label in [(cv_path, "CV"), (cover_letter_path, "Cover_Letter")]:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(path))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(path)}"'
            msg.attach(part)

    smtp = aiosmtplib.SMTP(
        hostname=cfg["host"],
        port=cfg["port"],
        use_tls=False,
        start_tls=cfg["use_tls"],
    )

    await smtp.connect()
    await smtp.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
    await smtp.send_message(msg)
    await smtp.quit()
    return True
