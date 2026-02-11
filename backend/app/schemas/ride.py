from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from app.models.ride import RideStatus, RouteType


class RideBase(BaseModel):
    pickup_address: str = Field(min_length=1, max_length=500)
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    dropoff_address: str = Field(min_length=1, max_length=500)
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    scheduled_at: datetime
    passenger_name: str | None = None
    passenger_phone: str | None = None
    passenger_count: int = 1
    route_type: RouteType | None = None
    distance_km: float | None = None
    duration_min: int | None = None
    price: float | None = None
    driver_share: float | None = None
    notes: str | None = None


class RideWebhook(RideBase):
    external_id: str | None = None
    source_platform: str


class RideCreate(RideBase):
    external_id: str | None = None
    source_platform: str
    driver_id: UUID | None = None


class RideUpdate(BaseModel):
    status: RideStatus | None = None
    pickup_address: str | None = None
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    dropoff_address: str | None = None
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    scheduled_at: datetime | None = None
    passenger_name: str | None = None
    passenger_phone: str | None = None
    passenger_count: int | None = None
    route_type: RouteType | None = None
    distance_km: float | None = None
    duration_min: int | None = None
    price: float | None = None
    driver_share: float | None = None
    notes: str | None = None
    driver_id: UUID | None = None


class RideResponse(RideBase):
    id: UUID
    external_id: str | None
    source_platform: str
    status: RideStatus
    driver_id: UUID | None
    assigned_by: UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    critical_at: datetime | None
    # Booking.com fields
    booking_reference: str | None = None
    flight_number: str | None = None
    booking_services: list | dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RideWithDriverResponse(RideResponse):
    driver_name: str | None = None


class RideListResponse(BaseModel):
    rides: list[RideResponse]
    total: int
    page: int = 1
    page_size: int = 50


class AssignRideRequest(BaseModel):
    driver_id: UUID
