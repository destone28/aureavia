from sqlalchemy import String, Boolean, Integer, TIMESTAMP, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class BookingConfig(Base):
    """Singleton table storing Booking.com API configuration.

    Only one row should ever exist (id=1). The application creates it
    automatically on first access if missing.
    """

    __tablename__ = "booking_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # OAuth2 credentials
    client_id: Mapped[str] = mapped_column(String(255), default="")
    client_secret: Mapped[str] = mapped_column(String(500), default="")

    # API endpoints
    api_base_url: Mapped[str] = mapped_column(
        String(500),
        default="https://taxi-api-sandbox.booking.com",
    )

    # Webhook validation
    webhook_secret: Mapped[str] = mapped_column(String(255), default="")

    # Integration state
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    environment: Mapped[str] = mapped_column(String(20), default="sandbox")

    # Cached OAuth token
    access_token: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Sync state
    last_sync_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BookingConfig env={self.environment} enabled={self.is_enabled}>"
