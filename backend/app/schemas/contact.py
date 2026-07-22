from pydantic import BaseModel


class SendContactRequestPayload(BaseModel):
    username: str | None = None
