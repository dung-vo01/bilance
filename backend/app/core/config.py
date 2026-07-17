from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "a-very-secret-key"
    JWT_SECRET_KEY: str = "a-very-secret-jwt-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bilance_dev"
    )
    TEST_DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bilance_test"
    )

    CORS_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"

    RESEND_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "Bilance <onboarding@resend.dev>"
    FRONTEND_URL: str = "http://localhost:5173"
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    GUEST_ACCOUNT_TTL_HOURS: int = 24

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


settings = Settings()
