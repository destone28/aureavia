from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from uuid import UUID


class DriverBase(BaseModel):
    license_number: str | None = None
    license_expiry: date | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_plate: str | None = None
    vehicle_year: int | None = None
    vehicle_seats: int = 4
    vehicle_luggage_capacity: int = 2
    vehicle_fuel_type: str | None = None
    insurance_number: str | None = None
    insurance_expiry: date | None = None
    vehicle_inspection_date: date | None = None
    special_permits: dict | None = None


class DriverCreate(DriverBase):
    user_id: UUID
    ncc_company_id: UUID | None = None


class DriverUpdate(BaseModel):
    ncc_company_id: UUID | None = None
    license_number: str | None = None
    license_expiry: date | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_plate: str | None = None
    vehicle_year: int | None = None
    vehicle_seats: int | None = None
    vehicle_luggage_capacity: int | None = None
    vehicle_fuel_type: str | None = None
    insurance_number: str | None = None
    insurance_expiry: date | None = None
    vehicle_inspection_date: date | None = None
    special_permits: dict | None = None


class DriverResponse(DriverBase):
    id: UUID
    user_id: UUID
    ncc_company_id: UUID | None
    rating_avg: float
    total_km: float
    total_rides: int
    total_earnings: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DriverStats(BaseModel):
    total_rides: int
    total_earnings: float
    total_km: float
    rating_avg: float
    completed_this_month: int
    earnings_this_month: float


class DriverWithUserResponse(DriverResponse):
    first_name: str
    last_name: str
    email: str
    phone: str | None
    company_name: str | None
