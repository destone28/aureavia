from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aureavia:aureavia@localhost:5433/aureavia"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email (2FA)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@aureavia.com"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Booking API (external)
    BOOKING_API_KEY: str = ""
    BOOKING_API_URL: str = ""

    # App
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Development mode (log 2FA codes to console instead of sending email)
    DEV_MODE: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
