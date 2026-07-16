from pydantic import BaseModel

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    phone_number: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    email: str | None = None
    password: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class AuthResponse(TokenPair):
    user: UserOut
