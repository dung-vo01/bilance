import asyncio
import logging

from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.ses_client import get_ses_client

logger = logging.getLogger("app.email")


async def _send(to: str, subject: str, html: str) -> None:
    if not settings.EMAIL_FROM:
        logger.warning(
            "EMAIL_FROM not set; skipping email to %s (subject=%s)", to, subject
        )
        return

    if not (settings.AWS_SES_ACCESS_KEY and settings.AWS_SES_SECRET_ACCESS_KEY):
        logger.warning(
            "SES keys not set; skipping email to %s (subject=%s)", to, subject
        )
        return

    try:
        client = get_ses_client()

        await asyncio.to_thread(
            client.send_email,
            FromEmailAddress=settings.EMAIL_FROM,
            Destination={
                "ToAddresses": [
                    to,
                ]
            },
            Content={
                "Simple": {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Html": {"Data": html, "Charset": "UTF-8"},
                    },
                }
            },
        )
        
        logger.info("Sent email to %s (subject=%s)", to, subject)

    except (BotoCoreError, ClientError):
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


async def send_contact_request_email(
    to: str,
    recipient_firstname: str | None,
    recipient_username: str,
    requester_name: str,
) -> None:
    greeting_name = recipient_firstname or recipient_username
    link = f"{settings.FRONTEND_URL}/contacts"
    html = f"""
      <p>Hi {greeting_name},</p>
      <p>{requester_name} sent you a friend request on Bilance.</p>
      <p>Log in to accept or decline: <a href="{link}">{link}</a></p>
    """
    await _send(to, f"{requester_name} sent you a friend request on Bilance", html)
