import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger("app.email")

RESEND_API_URL = "https://api.resend.com/emails"


def _parse_from_header(value: str) -> tuple[str, str]:
    """Splits 'Display Name <email@domain>' into (name, email)."""
    match = re.match(r"^\s*(.*?)\s*<(.+?)>\s*$", value)
    if match:
        return match.group(1), match.group(2)
    return value, value


async def _send_resend(to: str, subject: str, html: str) -> None:
    """Dormant - Resend only supports full-domain verification. Point the
    public send_* functions at this instead of _send() to re-enable it."""
    if not settings.RESEND_API_KEY:
        logger.warning(
            "RESEND_API_KEY not set; skipping email to %s (subject=%s)", to, subject
        )
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={
                    "from": settings.EMAIL_FROM,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Failed to send email to %s (subject=%s)", to, subject)


async def _send(to: str, subject: str, html: str) -> None:
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP_USERNAME/SMTP_PASSWORD not set; skipping email to %s (subject=%s)",
            to,
            subject,
        )
        return

    from_name, from_email = _parse_from_header(settings.EMAIL_FROM)

    def _send_sync() -> None:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{from_name} <{from_email}>"
        message["To"] = to
        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(from_email, [to], message.as_string())

    try:
        await run_in_threadpool(_send_sync)
    except (smtplib.SMTPException, OSError):
        logger.exception("Failed to send email to %s (subject=%s)", to, subject)


async def send_verification_email(
    to: str, firstname: str | None, username: str, token: str
) -> None:
    greeting_name = firstname or username
    link = f"{settings.FRONTEND_URL}/verify-email/{token}"
    html = f"""
      <p>Hi {greeting_name},</p>
      <p>Welcome to Bilance. Click below to verify your email address:</p>
      <p><a href="{link}">Verify my email</a></p>
      <p>This link expires in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.</p>
    """
    await _send(to, "Verify your Bilance account", html)


async def send_password_reset_email(
    to: str, firstname: str | None, username: str, token: str
) -> None:
    greeting_name = firstname or username
    link = f"{settings.FRONTEND_URL}/reset-password/{token}"
    html = f"""
      <p>Hi {greeting_name},</p>
      <p>You requested a password reset for your account "{username}".
      Click below to set a new password:</p>
      <p><a href="{link}">Reset my password</a></p>
      <p>If you didn't request this, you can ignore this email.
      This link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.</p>
    """
    await _send(to, "Reset your Bilance password", html)


async def send_group_invitation_email(
    to: str,
    invitee_firstname: str | None,
    invitee_username: str,
    inviter_name: str,
    group_name: str,
) -> None:
    greeting_name = invitee_firstname or invitee_username
    html = f"""
      <p>Hi {greeting_name},</p>
      <p>{inviter_name} invited you to join the expense group "{group_name}" on Bilance.</p>
      <p>Log in to accept or decline: <a href="{settings.FRONTEND_URL}/dashboard">{settings.FRONTEND_URL}</a></p>
    """
    await _send(to, f'You\'ve been invited to "{group_name}" on Bilance', html)
