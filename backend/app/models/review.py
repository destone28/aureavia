from sqlalchemy import String, Integer, TIMESTAMP, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ride_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rides.id", ondelete="CASCADE"))
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    reviewer_name: Mapped[str | None] = mapped_column(String(200))
    source_platform: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    ride: Mapped["Ride"] = relationship("Ride", back_populates="review")
    driver: Mapped["Driver"] = relationship("Driver", back_populates="reviews")

    def __repr__(self):
        return f"<Review {self.id} - {self.rating}/5 for driver {self.driver_id}>"
