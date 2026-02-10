from sqlalchemy import String, Integer, Date, TIMESTAMP, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
import uuid
from app.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    ncc_company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ncc_companies.id", ondelete="SET NULL"))

    # License
    license_number: Mapped[str | None] = mapped_column(String(50))
    license_expiry: Mapped[date | None] = mapped_column(Date)

    # Vehicle info
    vehicle_make: Mapped[str | None] = mapped_column(String(100))
    vehicle_model: Mapped[str | None] = mapped_column(String(100))
    vehicle_plate: Mapped[str | None] = mapped_column(String(20))
    vehicle_year: Mapped[int | None] = mapped_column(Integer)
    vehicle_seats: Mapped[int] = mapped_column(Integer, default=4)
    vehicle_luggage_capacity: Mapped[int] = mapped_column(Integer, default=2)
    vehicle_fuel_type: Mapped[str | None] = mapped_column(String(30))

    # Insurance & inspection
    insurance_number: Mapped[str | None] = mapped_column(String(100))
    insurance_expiry: Mapped[date | None] = mapped_column(Date)
    vehicle_inspection_date: Mapped[date | None] = mapped_column(Date)

    # Additional capabilities
    special_permits: Mapped[dict | None] = mapped_column(JSON, default=lambda: [])

    # Stats (updated after each completed ride)
    rating_avg: Mapped[float] = mapped_column(DECIMAL(3, 2), default=0.00)
    total_km: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0.00)
    total_rides: Mapped[int] = mapped_column(Integer, default=0)
    total_earnings: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0.00)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="driver")
    ncc_company: Mapped["NCCCompany"] = relationship("NCCCompany", back_populates="drivers")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="driver")

    def __repr__(self):
        return f"<Driver {self.id} - {self.vehicle_make} {self.vehicle_model}>"
