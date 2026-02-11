"""Pydantic schemas for ETG Transfers API.

AureaVia is the SUPPLIER: ETG calls our endpoints.
Schemas match the ETG OpenAPI spec / Postman test collection exactly.
"""

from pydantic import BaseModel, Field
from enum import Enum


# --- Enums ---

class TransferCategory(str, Enum):
    """ETG transfer categories (26 total)."""
    ECONOMY = "economy"
    ECONOMY_MPV = "economy_mpv"
    ECONOMY_VAN = "economy_van"
    STANDARD = "standard"
    STANDARD_MPV = "standard_mpv"
    STANDARD_VAN = "standard_van"
    BUSINESS = "business"
    BUSINESS_MPV = "business_mpv"
    BUSINESS_VAN = "business_van"
    FIRST = "first"
    FIRST_MPV = "first_mpv"
    FIRST_VAN = "first_van"
    LUXURY = "luxury"
    LUXURY_MPV = "luxury_mpv"
    LUXURY_VAN = "luxury_van"
    MINIBUS = "minibus"
    MINIBUS_LARGE = "minibus_large"
    BUS = "bus"
    ELECTRO_ECONOMY = "electro_economy"
    ELECTRO_STANDARD = "electro_standard"
    ELECTRO_BUSINESS = "electro_business"
    ELECTRO_FIRST = "electro_first"
    ELECTRO_LUXURY = "electro_luxury"
    ELECTRO_MINIBUS = "electro_minibus"
    ELECTRO_BUS = "electro_bus"
    MICRO = "micro"


class ChildSeatType(str, Enum):
    SEAT_0 = "children_seat_0"
    SEAT_1 = "children_seat_1"
    SEAT_2 = "children_seat_2"
    SEAT_3 = "children_seat_3"


class OrderStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# --- Common ---

class PriceObj(BaseModel):
    """Price object per ETG spec."""
    amount: float
    currency: str = "EUR"


class PointRequest(BaseModel):
    """Origin or destination point."""
    type: str = Field(description="Point type: iata, coordinates, address")
    value: str | None = Field(default=None, description="Value when type is not iata")
    iata: str | None = Field(default=None, description="IATA code when type is iata")
    coordinates: str | None = Field(default=None, description="lat,lng when type is coordinates")


# --- Search ---

class SearchRequest(BaseModel):
    """ETG /search request body."""
    start_point: PointRequest
    end_point: PointRequest
    start_date_time: str = Field(description="RFC3339 datetime")
    passengers: int = Field(ge=1, le=50, default=1)
    children_seat_0: int = Field(default=0)
    children_seat_1: int = Field(default=0)
    children_seat_2: int = Field(default=0)
    children_seat_3: int = Field(default=0)


class SearchOffer(BaseModel):
    """A single offer in search results - matches ETG Postman tests."""
    id: str
    service_type: str = "transfer"
    transfer_category: TransferCategory
    car_model: str
    seats: int
    luggage_places: int
    price: PriceObj
    included_waiting_time_minutes: int = 60
    tolls_included: bool = True
    gratuity_included: bool = False
    free_cancel_until: str | None = None
    estimated_duration_minutes: int | None = None
    distance: float | None = None


class SearchResponse(BaseModel):
    """ETG /search response."""
    start_date_time: str
    offers: list[SearchOffer]


# --- Book ---

class MainPassenger(BaseModel):
    """Main passenger information."""
    first_name: str
    last_name: str
    phone: str
    email: str = ""


class BookRequest(BaseModel):
    """ETG /book request body."""
    offer_id: str
    passengers: int = 1
    luggage_places: int = 0
    children_seat_0: int = 0
    children_seat_1: int = 0
    children_seat_2: int = 0
    children_seat_3: int = 0
    flight_number: str = ""
    shield_text: str = ""
    comment: str = ""
    main_passenger: MainPassenger
    start_point: PointRequest
    end_point: PointRequest


class MeetingImage(BaseModel):
    """Meeting point image."""
    url: str
    description: str = ""


class BookResponse(BaseModel):
    """ETG /book response - matches Postman tests."""
    order_id: str = Field(max_length=15)
    supplier_link: str = ""
    start_time: str
    distance: float | None = None
    estimated_duration_minutes: int | None = None
    included_waiting_time_minutes: int = 60
    passengers: int = 1
    luggage_places: int = 0
    sport_luggage_places: int = 0
    animals: int = 0
    wheelchairs_places: int = 0
    flight_number: str = ""
    shield_text: str = ""
    comment: str = ""
    price: PriceObj
    meeting_instructions: str | None = None
    meeting_images: list[MeetingImage] | None = None


# --- Status ---

class DriverInfo(BaseModel):
    """Driver info in status response."""
    name: str = ""
    phone: str = ""
    photo_url: str = ""


class CarInfo(BaseModel):
    """Car info in status response."""
    model: str = ""
    color: str = ""
    plate_number: str = ""
    photo_url: str = ""


class MeetingInfo(BaseModel):
    """Meeting point information."""
    instructions: str = ""
    images: list[MeetingImage] | None = None


class StatusRequest(BaseModel):
    """ETG /status request body (POST, not GET)."""
    order_id: str


class StatusResponse(BaseModel):
    """ETG /status response - matches Postman tests."""
    status: OrderStatus
    order_id: str
    start_time: str
    price: PriceObj
    driver_info: DriverInfo | None = None
    car_info: CarInfo | None = None
    meeting_info: MeetingInfo | None = None


# --- Cancel ---

class CancelRequest(BaseModel):
    """ETG /cancel request body (order_id in body, not URL)."""
    order_id: str


class CancelPenalty(BaseModel):
    """Cancellation penalty details."""
    amount: float = 0.0
    currency: str = "EUR"


class CancelResponse(BaseModel):
    """ETG /cancel response."""
    penalty: CancelPenalty
