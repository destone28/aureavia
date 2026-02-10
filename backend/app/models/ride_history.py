from sqlalchemy import String, TIMESTAMP, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
from app.database import Base


class RideHistory(Base):
    __tablename__ = "ride_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ride_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rides.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    changed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    ride: Mapped["Ride"] = relationship("Ride", back_populates="history")
    changer: Mapped["User"] = relationship("User", back_populates="ride_history_changes")

    def __repr__(self):
        return f"<RideHistory {self.ride_id} {self.old_status} → {self.new_status}>"
