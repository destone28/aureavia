"""Booking.com Taxi Supplier API integration service.

Handles OAuth2 token management, outbound API calls, and booking sync.
"""

import httpx
import uuid
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.booking_config import BookingConfig
from app.models.ride import Ride, RideStatus
from app.models.ride_history import RideHistory
from app.schemas.booking import (
    BookingAPIBooking,
    BookingAcceptRejectRequest,
    SearchWebhookPayload,
    SearchWebhookResponse,
    SearchPriceResponse,
    SearchFeature,
)

logger = logging.getLogger(__name__)

# Base prices per km (can be made configurable later)
BASE_PRICE_PER_KM = 1.80
MIN_PRICE = 25.00


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

async def get_booking_config(db: AsyncSession) -> BookingConfig:
    """Get or create the singleton BookingConfig row."""
    result = await db.execute(select(BookingConfig).where(BookingConfig.id == 1))
    config = result.scalar_one_or_none()
    if config is None:
        config = BookingConfig(id=1)
        db.add(config)
        await db.flush()
    return config


async def is_booking_enabled(db: AsyncSession) -> bool:
    """Check if Booking.com integration is enabled and configured."""
    config = await get_booking_config(db)
    return config.is_enabled and bool(config.client_id) and bool(config.client_secret)


# ---------------------------------------------------------------------------
# OAuth2 Token Management
# ---------------------------------------------------------------------------

async def get_oauth_token(config: BookingConfig) -> str:
    """Get a valid OAuth2 access token, refreshing if needed.

    Uses the Client Credentials flow as per Booking.com Taxi API docs.
    """
    now = datetime.now(timezone.utc)

    # Return cached token if still valid (with 60s buffer)
    if (
        config.access_token
        and config.token_expires_at
        and config.token_expires_at > now + timedelta(seconds=60)
    ):
        return config.access_token

    # Request new token
    token_url = f"{config.api_base_url.rstrip('/')}/oauth/token"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": config.client_id,
                "client_secret": config.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        data = response.json()

    config.access_token = data["access_token"]
    expires_in = data.get("expires_in", 3600)
    config.token_expires_at = now + timedelta(seconds=expires_in)

    return config.access_token


def _get_auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Outbound API: Accept / Reject booking
# ---------------------------------------------------------------------------

async def accept_booking(db: AsyncSession, ride: Ride) -> bool:
    """Call Booking.com API to accept a booking."""
    config = await get_booking_config(db)
    if not config.is_enabled:
        logger.info("Booking.com integration disabled, skipping accept")
        return True

    if not ride.booking_reference or not ride.booking_customer_ref:
        logger.warning("Ride %s has no booking_reference, cannot accept on Booking.com", ride.id)
        return True  # Not a Booking.com ride, no action needed

    try:
        token = await get_oauth_token(config)
        url = (
            f"{config.api_base_url.rstrip('/')}/v1/bookings"
            f"/{ride.booking_customer_ref}/{ride.booking_reference}/responses"
        )
        body = BookingAcceptRejectRequest(
            supplierResponse="ACCEPT",
            state_hash=ride.booking_state_hash or "",
        )

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json=body.model_dump(),
                headers=_get_auth_headers(token),
            )
            response.raise_for_status()

        logger.info("Accepted booking %s on Booking.com", ride.booking_reference)
        await db.flush()
        return True
    except Exception as e:
        logger.error("Failed to accept booking %s: %s", ride.booking_reference, e)
        return False


async def reject_booking(
    db: AsyncSession,
    ride: Ride,
    reason: str = "NO_AVAILABILITY",
) -> bool:
    """Call Booking.com API to reject a booking."""
    config = await get_booking_config(db)
    if not config.is_enabled or not ride.booking_reference:
        return True

    try:
        token = await get_oauth_token(config)
        url = (
            f"{config.api_base_url.rstrip('/')}/v1/bookings"
            f"/{ride.booking_customer_ref}/{ride.booking_reference}/responses"
        )
        body = BookingAcceptRejectRequest(
            supplierResponse="REJECT",
            state_hash=ride.booking_state_hash or "",
            cancellationReason=reason,
        )

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json=body.model_dump(),
                headers=_get_auth_headers(token),
            )
            response.raise_for_status()

        logger.info("Rejected booking %s on Booking.com", ride.booking_reference)
        return True
    except Exception as e:
        logger.error("Failed to reject booking %s: %s", ride.booking_reference, e)
        return False


# ---------------------------------------------------------------------------
# Outbound API: Poll new bookings
# ---------------------------------------------------------------------------

async def poll_new_bookings(db: AsyncSession) -> tuple[int, int]:
    """Poll Booking.com for NEW bookings and import them.

    Returns (new_count, updated_count).
    """
    config = await get_booking_config(db)
    if not config.is_enabled:
        return 0, 0

    try:
        token = await get_oauth_token(config)
        url = f"{config.api_base_url.rstrip('/')}/v1/bookings"
        params = {"status": "NEW", "size": 500}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                params=params,
                headers=_get_auth_headers(token),
            )
            response.raise_for_status()

        data = response.json()
        bookings = data.get("bookings", [])

        new_count = 0
        updated_count = 0

        for booking_data in bookings:
            booking = BookingAPIBooking.model_validate(booking_data)

            # Check if we already have this booking
            existing_result = await db.execute(
                select(Ride).where(
                    Ride.booking_reference == booking.bookingReference,
                    Ride.source_platform == "booking.com",
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                # Update state_hash if changed
                if booking.stateHash and existing.booking_state_hash != booking.stateHash:
                    existing.booking_state_hash = booking.stateHash
                    updated_count += 1
                continue

            # Create new ride from booking
            ride = _booking_to_ride(booking)
            db.add(ride)

            # Record history
            history = RideHistory(
                ride_id=ride.id,
                old_status=None,
                new_status=RideStatus.TO_ASSIGN.value,
                changed_by=None,
                changed_at=datetime.now(timezone.utc),
                notes=f"Imported from Booking.com (ref: {booking.bookingReference})",
            )
            db.add(history)
            new_count += 1

        # Update last sync time
        config.last_sync_at = datetime.now(timezone.utc)
        await db.flush()

        logger.info("Booking.com sync: %d new, %d updated", new_count, updated_count)
        return new_count, updated_count

    except Exception as e:
        logger.error("Failed to poll Booking.com bookings: %s", e)
        raise


def _booking_to_ride(booking: BookingAPIBooking) -> Ride:
    """Convert a Booking.com API booking to a Ride model."""
    now = datetime.now(timezone.utc)

    # Parse pickup datetime
    scheduled_at = now + timedelta(hours=24)  # fallback
    if booking.pickupDateTime:
        try:
            scheduled_at = datetime.fromisoformat(booking.pickupDateTime.replace("Z", "+00:00"))
        except ValueError:
            pass

    # Build passenger name
    passenger_name = None
    passenger_phone = None
    if booking.leadPassenger:
        passenger_name = f"{booking.leadPassenger.firstName} {booking.leadPassenger.lastName}"
        passenger_phone = booking.leadPassenger.phoneNumber

    # Calculate price estimate from distance
    price = None
    distance_km = booking.drivingDistanceInKm
    if distance_km:
        price = max(round(distance_km * BASE_PRICE_PER_KM, 2), MIN_PRICE)

    # Build addresses from location objects
    pickup_address = "Pickup location"
    pickup_lat = None
    pickup_lng = None
    if booking.origin:
        parts = [p for p in [booking.origin.name, booking.origin.city] if p]
        pickup_address = ", ".join(parts) or "Pickup location"
        pickup_lat = booking.origin.latitude
        pickup_lng = booking.origin.longitude

    dropoff_address = "Dropoff location"
    dropoff_lat = None
    dropoff_lng = None
    if booking.destination:
        parts = [p for p in [booking.destination.name, booking.destination.city] if p]
        dropoff_address = ", ".join(parts) or "Dropoff location"
        dropoff_lat = booking.destination.latitude
        dropoff_lng = booking.destination.longitude

    # Services as serializable dicts
    services = [{"name": s.name, "value": s.value} for s in booking.services] if booking.services else None

    return Ride(
        id=uuid.uuid4(),
        external_id=booking.bookingReference,
        source_platform="booking.com",
        status=RideStatus.TO_ASSIGN,
        pickup_address=pickup_address,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        dropoff_address=dropoff_address,
        dropoff_lat=dropoff_lat,
        dropoff_lng=dropoff_lng,
        scheduled_at=scheduled_at,
        passenger_name=passenger_name,
        passenger_phone=passenger_phone,
        passenger_count=1,
        distance_km=distance_km,
        price=price,
        notes=booking.comment,
        flight_number=booking.flightNumber,
        booking_reference=booking.bookingReference,
        booking_customer_ref=booking.customerReference,
        booking_state_hash=booking.stateHash,
        booking_services=services,
        booking_raw_payload=booking.model_dump(),
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Pricing for search webhook
# ---------------------------------------------------------------------------

def calculate_search_price(payload: SearchWebhookPayload) -> SearchWebhookResponse:
    """Calculate price for a Booking.com search request.

    Returns a SearchWebhookResponse with pricing information.
    """
    distance_km = payload.drivingDistanceInKm or 20.0
    price = max(round(distance_km * BASE_PRICE_PER_KM, 2), MIN_PRICE)

    # Determine max passengers based on vehicle categories
    max_passengers = 4
    if payload.passengers > 4:
        max_passengers = 8  # PEOPLE_CARRIER / MINIBUS

    category = "STANDARD"
    if payload.passengers > 6:
        category = "MINIBUS"
    elif payload.passengers > 4:
        category = "PEOPLE_CARRIER"

    return SearchWebhookResponse(
        searchResultId=str(uuid.uuid4()),
        transportCategory=category,
        price=SearchPriceResponse(
            salePriceMin=price,
            salePriceMax=price,
            currency="EUR",
        ),
        minPassengers=1,
        maxPassengers=max_passengers,
        features=[SearchFeature(name="noOfBags", value=str(max_passengers))],
        servicesAvailable=["meetAndGreet"],
    )


# ---------------------------------------------------------------------------
# Test connection
# ---------------------------------------------------------------------------

async def test_connection(db: AsyncSession) -> tuple[bool, str]:
    """Test connection to Booking.com API by attempting OAuth2 auth."""
    config = await get_booking_config(db)

    if not config.client_id or not config.client_secret:
        return False, "Client ID e Client Secret sono obbligatori"

    try:
        token = await get_oauth_token(config)
        await db.flush()  # Save the new token
        return True, f"Connessione riuscita (token: {token[:20]}...)"
    except httpx.HTTPStatusError as e:
        return False, f"Errore autenticazione: {e.response.status_code} - {e.response.text[:200]}"
    except httpx.ConnectError:
        return False, f"Impossibile connettersi a {config.api_base_url}"
    except Exception as e:
        return False, f"Errore: {str(e)}"
