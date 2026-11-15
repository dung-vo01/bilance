import logging

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from app.core.config import settings
from app.services import email_service

SENDER = "Bilance <noreply@example.com>"


class FakeSesClient:
    """Stands in for the boto3 sesv2 client; records calls to send_email."""

    def __init__(self, error: Exception | None = None):
        self.calls: list[dict] = []
        self.error = error

    def send_email(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {"MessageId": "fake-id"}


@pytest.fixture
def ses_configured(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_FROM", SENDER)
    monkeypatch.setattr(settings, "AWS_SES_ACCESS_KEY", "test-key")
    monkeypatch.setattr(settings, "AWS_SES_SECRET_ACCESS_KEY", "test-secret")


@pytest.fixture
def use_client(monkeypatch):
    def _use(client: FakeSesClient) -> FakeSesClient:
        monkeypatch.setattr(
            "app.services.email_service.get_ses_client", lambda: client
        )
        return client

    return _use


@pytest.mark.asyncio
async def test_send_calls_ses_with_expected_arguments(ses_configured, use_client):
    client = use_client(FakeSesClient())

    await email_service._send("john.doe@example.com", "Hello", "<p>Hi</p>")

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["FromEmailAddress"] == SENDER
    assert call["Destination"] == {"ToAddresses": ["john.doe@example.com"]}
    simple = call["Content"]["Simple"]
    assert simple["Subject"]["Data"] == "Hello"
    assert simple["Body"]["Html"]["Data"] == "<p>Hi</p>"


@pytest.mark.asyncio
async def test_send_logs_success(ses_configured, use_client, caplog):
    use_client(FakeSesClient())

    with caplog.at_level(logging.INFO, logger="app.email"):
        await email_service._send("john.doe@example.com", "Hello", "<p>Hi</p>")

    assert "Sent email to john.doe@example.com" in caplog.text


@pytest.mark.asyncio
async def test_send_skips_when_keys_not_set(monkeypatch, use_client, caplog):
    monkeypatch.setattr(settings, "EMAIL_FROM", SENDER)
    client = use_client(FakeSesClient())  # keys are blanked by the autouse fixture

    with caplog.at_level(logging.WARNING, logger="app.email"):
        await email_service._send("john.doe@example.com", "Hello", "<p>Hi</p>")

    assert client.calls == []
    assert "skipping" in caplog.text


@pytest.mark.asyncio
async def test_send_skips_when_email_from_not_set(
    ses_configured, monkeypatch, use_client, caplog
):
    monkeypatch.setattr(settings, "EMAIL_FROM", "")
    client = use_client(FakeSesClient())

    with caplog.at_level(logging.WARNING, logger="app.email"):
        await email_service._send("john.doe@example.com", "Hello", "<p>Hi</p>")

    assert client.calls == []
    assert "EMAIL_FROM not set" in caplog.text


@pytest.mark.asyncio
async def test_send_does_not_raise_when_ses_rejects(
    ses_configured, use_client, caplog
):
    error = ClientError(
        {"Error": {"Code": "MessageRejected", "Message": "Email address is not verified"}},
        "SendEmail",
    )
    use_client(FakeSesClient(error=error))

    with caplog.at_level(logging.ERROR, logger="app.email"):
        await email_service._send("john.doe@example.com", "Hello", "<p>Hi</p>")

    assert "Failed to send email to john.doe@example.com" in caplog.text


@pytest.mark.asyncio
async def test_send_does_not_raise_on_network_error(
    ses_configured, use_client, caplog
):
    error = EndpointConnectionError(endpoint_url="https://email.eu-north-1.amazonaws.com")
    use_client(FakeSesClient(error=error))

    with caplog.at_level(logging.ERROR, logger="app.email"):
        await email_service._send("john.doe@example.com", "Hello", "<p>Hi</p>")

    assert "Failed to send email to john.doe@example.com" in caplog.text


@pytest.mark.asyncio
async def test_password_reset_email_contains_reset_link(monkeypatch):
    sent = {}

    async def fake_send(to, subject, html):
        sent.update(to=to, subject=subject, html=html)

    monkeypatch.setattr("app.services.email_service._send", fake_send)

    await email_service.send_password_reset_email(
        "john.doe@example.com", "John", "johndoe", "tok123"
    )

    assert sent["to"] == "john.doe@example.com"
    assert f"{settings.FRONTEND_URL}/reset-password/tok123" in sent["html"]
