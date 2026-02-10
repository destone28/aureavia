from sqlalchemy import String, Integer, TIMESTAMP, ForeignKey, DECIMAL, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class RideStatus(str, enum.Enum):
    TO_ASSIGN = "to_assign"
    BOOKED = "booked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CRITICAL = "critical"


class RouteType(str, enum.Enum):
    URBAN = "urban"
    EXTRA_URBAN = "extra_urban"


class Ride(Base):
    __tablename__ = "rides"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(String(100))
    source_platform: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[RideStatus] = mapped_column(
        SQLEnum(RideStatus, name="ride_status"),
        default=RideStatus.TO_ASSIGN,
        nullable=False,
        index=True
    )

    # Locations
    pickup_address: Mapped[str] = mapped_column(String(500), nullable=False)
    pickup_lat: Mapped[float | None] = mapped_column(DECIMAL(10, 8))
    pickup_lng: Mapped[float | None] = mapped_column(DECIMAL(11, 8))
    dropoff_address: Mapped[str] = mapped_column(String(500), nullable=False)
    dropoff_lat: Mapped[float | None] = mapped_column(DECIMAL(10, 8))
    dropoff_lng: Mapped[float | None] = mapped_column(DECIMAL(11, 8))

    # Timing
    scheduled_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Passenger info
    passenger_name: Mapped[str | None] = mapped_column(String(200))
    passenger_phone: Mapped[str | None] = mapped_column(String(30))
    passenger_count: Mapped[int] = mapped_column(Integer, default=1)

    # Ride details
    route_type: Mapped[RouteType | None] = mapped_column(SQLEnum(RouteType, name="route_type"))
    distance_km: Mapped[float | None] = mapped_column(DECIMAL(8, 2))
    duration_min: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    driver_share: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    notes: Mapped[str | None] = mapped_column(Text)

    # Assignment
    driver_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    # Critical ride handling
    critical_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    critical_resolved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    critical_resolution_type: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    driver: Mapped["User"] = relationship("User", foreign_keys=[driver_id], back_populates="rides_as_driver")
    assigner: Mapped["User"] = relationship("User", foreign_keys=[assigned_by], back_populates="rides_assigned")
    history: Mapped[list["RideHistory"]] = relationship("RideHistory", back_populates="ride", cascade="all, delete-orphan")
    review: Mapped["Review"] = relationship("Review", back_populates="ride", uselist=False)
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="ride")

    def __repr__(self):
        return f"<Ride {self.id} {self.status} - {self.pickup_address} → {self.dropoff_address}>"
