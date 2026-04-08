import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from .config import settings


WELCOME_TEMPLATE = """
<html>
<body style="font-family: Arial, sans-serif; background: #f8fafc; padding: 40px;">
  <div style="max-width: 500px; margin: auto; background: white; border-radius: 12px; padding: 40px;">
    <h1 style="color: #1e293b;">Welcome to MathLens</h1>
    <p>Hi {{ name }},</p>
    <p>Your account is ready. MathLens solves math problems from photos or typed expressions with step-by-step solutions.</p>
    <a href="{{ frontend_url }}" style="display: inline-block; background: #f59e0b; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; margin-top: 16px;">Start Solving</a>
    <p style="color: #888; margin-top: 24px; font-size: 12px;">&copy; Humanoid Maker &mdash; www.humanoidmaker.com</p>
  </div>
</body>
</html>
"""

RESET_TEMPLATE = """
<html>
<body style="font-family: Arial, sans-serif; background: #f8fafc; padding: 40px;">
  <div style="max-width: 500px; margin: auto; background: white; border-radius: 12px; padding: 40px;">
    <h1 style="color: #1e293b;">Reset Your Password</h1>
    <p>Hi {{ name }},</p>
    <p>Use the code below to reset your password. It expires in 15 minutes.</p>
    <div style="background: #fffbeb; padding: 16px; border-radius: 8px; text-align: center; font-size: 28px; letter-spacing: 6px; font-weight: bold; color: #1e293b;">{{ code }}</div>
    <p style="color: #888; margin-top: 24px; font-size: 12px;">&copy; Humanoid Maker &mdash; www.humanoidmaker.com</p>
  </div>
</body>
</html>
"""


async def send_email(to: str, subject: str, html_body: str):
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        print(f"[EMAIL SKIP] SMTP not configured. Would send to {to}: {subject}")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        start_tls=True,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASS,
    )


async def send_welcome_email(to: str, name: str):
    html = Template(WELCOME_TEMPLATE).render(name=name, frontend_url=settings.FRONTEND_URL)
    await send_email(to, "Welcome to MathLens", html)


async def send_reset_email(to: str, name: str, code: str):
    html = Template(RESET_TEMPLATE).render(name=name, code=code)
    await send_email(to, "MathLens — Password Reset Code", html)
