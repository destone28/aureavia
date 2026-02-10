from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from app.models.ncc_company import CompanyStatus


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website: str | None = None
    partner_type: str = "ncc_partner"
    contact_person: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    notes: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    website: str | None = None
    contact_person: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    status: CompanyStatus | None = None
    notes: str | None = None


class CompanyResponse(CompanyBase):
    id: UUID
    status: CompanyStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyWithStats(CompanyResponse):
    active_drivers: int = 0
    monthly_revenue: float = 0.0
