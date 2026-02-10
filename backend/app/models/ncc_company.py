from sqlalchemy import String, TIMESTAMP, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class CompanyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class NCCCompany(Base):
    __tablename__ = "ncc_companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255))
    partner_type: Mapped[str] = mapped_column(String(50), default="ncc_partner")
    contact_person: Mapped[str | None] = mapped_column(String(200))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[CompanyStatus] = mapped_column(
        SQLEnum(CompanyStatus, name="company_status"),
        default=CompanyStatus.ACTIVE,
        nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    drivers: Mapped[list["Driver"]] = relationship("Driver", back_populates="ncc_company")

    def __repr__(self):
        return f"<NCCCompany {self.name}>"
