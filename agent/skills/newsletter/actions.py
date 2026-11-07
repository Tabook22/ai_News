import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def is_smtp_configured():
    return bool(os.environ.get('SMTP_HOST') and os.environ.get('SMTP_USERNAME') and os.environ.get('SMTP_PASSWORD'))


def send_email(to_email, subject, html_body):
    """
    Sends one HTML email via the SMTP settings saved in Settings -> API Keys.
    Returns (ok: bool, error: str | None).
    """
    host = os.environ.get('SMTP_HOST')
    port = int(os.environ.get('SMTP_PORT') or 587)
    username = os.environ.get('SMTP_USERNAME')
    password = os.environ.get('SMTP_PASSWORD')
    from_email = os.environ.get('SMTP_FROM_EMAIL') or username
    from_name = os.environ.get('SMTP_FROM_NAME') or 'Nasser AI News'

    if not host or not username or not password:
        return False, "SMTP not configured — add it in Settings → API Keys."

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.sendmail(from_email, [to_email], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)
