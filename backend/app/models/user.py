from sqlalchemy import String, TIMESTAMP, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ASSISTANT = "assistant"
    FINANCE = "finance"
    DRIVER = "driver"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNAVAILABLE = "unavailable"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, name="user_role"), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="user_status"),
        default=UserStatus.ACTIVE,
        nullable=False
    )
    two_factor_code: Mapped[str | None] = mapped_column(String(255))
    two_factor_expires: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    fcm_token: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_login: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Relationships
    driver: Mapped["Driver"] = relationship("Driver", back_populates="user", uselist=False)
    rides_as_driver: Mapped[list["Ride"]] = relationship(
        "Ride",
        foreign_keys="Ride.driver_id",
        back_populates="driver"
    )
    rides_assigned: Mapped[list["Ride"]] = relationship(
        "Ride",
        foreign_keys="Ride.assigned_by",
        back_populates="assigner"
    )
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="user")
    ride_history_changes: Mapped[list["RideHistory"]] = relationship("RideHistory", back_populates="changer")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
