"""Pydantic schemas for Booking.com Taxi Supplier API integration."""

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Webhook payloads (Booking.com → AureaVia)
# ---------------------------------------------------------------------------

class SearchLocation(BaseModel):
    latitude: float
    longitude: float
    name: str | None = None
    city: str | None = None
    country: str | None = None
    postcode: str | None = None
    iata: str | None = None


class GeniusInfo(BaseModel):
    level: str = "NON_GENIUS"


class SearchWebhookPayload(BaseModel):
    """Booking.com asks us for pricing."""
    origin: SearchLocation
    destination: SearchLocation
    passengers: int
    pickupDateTime: str
    pickupTimezone: str | None = None
    drivingDistanceInKm: float | None = None
    genius: GeniusInfo | None = None


class SearchPriceResponse(BaseModel):
    salePriceMin: float
    salePriceMax: float
    currency: str = "EUR"


class SearchFeature(BaseModel):
    name: str
    value: str


class SearchWebhookResponse(BaseModel):
    """Our response with pricing."""
    searchResultId: str
    transportCategory: str = "STANDARD"
    price: SearchPriceResponse
    minPassengers: int = 1
    maxPassengers: int = 4
    features: list[SearchFeature] = []
    servicesAvailable: list[str] = []


class LeadPassenger(BaseModel):
    title: str | None = None
    firstName: str
    lastName: str
    phoneNumber: str | None = None
    customerId: str | None = None


class BookingService(BaseModel):
    name: str
    value: str | None = None


class BookingWebhookPayload(BaseModel):
    """New booking notification from Booking.com."""
    bookingReference: str
    customerReference: str
    searchResultId: str | None = None
    leadPassenger: LeadPassenger
    flightNumber: str | None = None
    comment: str | None = None
    services: list[BookingService] = []


class BookingUpdatePayload(BaseModel):
    """Booking amendment or cancellation from Booking.com."""
    leadPassenger: LeadPassenger | None = None
    comment: str | None = None
    flightNumber: str | None = None
    pickupDateTime: str | None = None
    services: list[BookingService] | None = None
    action: str  # "AMENDMENT" or "CANCELLATION"
    cancellationReason: str | None = None


class IncidentPayload(BaseModel):
    """Incident notification from Booking.com."""
    bookingReference: str
    customerReference: str | None = None
    incidentType: str
    status: str | None = None
    responsibleParty: str | None = None
    description: str | None = None


# ---------------------------------------------------------------------------
# API responses (from Booking.com REST API)
# ---------------------------------------------------------------------------

class BookingAPIBooking(BaseModel):
    """A booking as returned by GET /v1/bookings."""
    bookingReference: str
    customerReference: str
    status: str
    stateHash: str | None = None
    origin: SearchLocation | None = None
    destination: SearchLocation | None = None
    pickupDateTime: str | None = None
    leadPassenger: LeadPassenger | None = None
    flightNumber: str | None = None
    comment: str | None = None
    services: list[BookingService] = []
    drivingDistanceInKm: float | None = None


class BookingAPIListResponse(BaseModel):
    """Response from GET /v1/bookings."""
    bookings: list[BookingAPIBooking] = []


class BookingAcceptRejectRequest(BaseModel):
    """Request body for POST /v1/bookings/:ref/responses."""
    supplierResponse: str  # "ACCEPT" or "REJECT"
    state_hash: str
    cancellationReason: str | None = None


# ---------------------------------------------------------------------------
# Admin config schemas
# ---------------------------------------------------------------------------

class BookingConfigResponse(BaseModel):
    """Config returned to frontend (no secrets)."""
    client_id: str
    api_base_url: str
    webhook_secret: str
    is_enabled: bool
    environment: str
    last_sync_at: str | None = None
    has_client_secret: bool = False


class BookingConfigUpdate(BaseModel):
    """Config update from frontend."""
    client_id: str | None = None
    client_secret: str | None = None
    api_base_url: str | None = None
    webhook_secret: str | None = None
    is_enabled: bool | None = None
    environment: str | None = None


class BookingTestResult(BaseModel):
    """Result of testing connection to Booking.com."""
    success: bool
    message: str


class BookingSyncResult(BaseModel):
    """Result of manual sync."""
    success: bool
    new_rides: int = 0
    updated_rides: int = 0
    message: str
