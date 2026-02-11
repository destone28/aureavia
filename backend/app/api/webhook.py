"""Webhook endpoints for receiving data from external platforms.

Includes both:
- Generic webhook for manual/test bookings (backwards compatible)
- Booking.com Taxi Supplier API webhooks (search, booking, update, incident)
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ride import Ride, RideStatus
from app.models.ride_history import RideHistory
from app.schemas.booking import (
    BookingUpdatePayload,
    BookingWebhookPayload,
    IncidentPayload,
    SearchWebhookPayload,
    SearchWebhookResponse,
)
from app.schemas.ride import RideResponse, RideWebhook
from app.services.booking_service import (
    calculate_search_price,
    get_booking_config,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Webhook secret validation helper
# ---------------------------------------------------------------------------

async def _validate_webhook_secret(
    db: AsyncSession,
    authorization: str | None,
) -> None:
    """Validate the webhook Authorization header against stored secret.

    If no webhook_secret is configured, all requests are accepted (dev mode).
    """
    config = await get_booking_config(db)
    if not config.webhook_secret:
        return  # No secret configured, accept all (development)

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    expected = f"Bearer {config.webhook_secret}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )


# ---------------------------------------------------------------------------
# POST /booking  -  Generic webhook (backwards compatible)
# ---------------------------------------------------------------------------

@router.post(
    "/booking",
    response_model=RideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def receive_booking(
    payload: RideWebhook,
    db: AsyncSession = Depends(get_db),
):
    """Receive a booking from an external platform and create a ride.

    This is the generic/manual endpoint. For Booking.com specific webhooks,
    use the /booking/search, /booking/new, etc. endpoints.
    """
    if payload.external_id:
        result = await db.execute(
            select(Ride).where(
                Ride.external_id == payload.external_id,
                Ride.source_platform == payload.source_platform,
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ride with external_id '{payload.external_id}' "
                       f"from '{payload.source_platform}' already exists",
            )

    now = datetime.now(timezone.utc)
    ride = Ride(
        external_id=payload.external_id,
        source_platform=payload.source_platform,
        status=RideStatus.TO_ASSIGN,
        pickup_address=payload.pickup_address,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        dropoff_address=payload.dropoff_address,
        dropoff_lat=payload.dropoff_lat,
        dropoff_lng=payload.dropoff_lng,
        scheduled_at=payload.scheduled_at,
        passenger_name=payload.passenger_name,
        passenger_phone=payload.passenger_phone,
        passenger_count=payload.passenger_count,
        route_type=payload.route_type,
        distance_km=payload.distance_km,
        duration_min=payload.duration_min,
        price=payload.price,
        notes=payload.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(ride)
    await db.flush()
    return ride


# ---------------------------------------------------------------------------
# POST /booking/search  -  Booking.com asks for pricing
# ---------------------------------------------------------------------------

@router.post("/booking/search", response_model=SearchWebhookResponse)
async def booking_search(
    payload: SearchWebhookPayload,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Booking.com search webhook — respond with pricing.

    SLA: response must be < 5 seconds (target < 2.5s).
    """
    await _validate_webhook_secret(db, authorization)

    logger.info(
        "Search request: %s → %s, %d pax, %.1f km",
        payload.origin.name or payload.origin.city,
        payload.destination.name or payload.destination.city,
        payload.passengers,
        payload.drivingDistanceInKm or 0,
    )

    return calculate_search_price(payload)


# ---------------------------------------------------------------------------
# POST /booking/new  -  New booking from Booking.com
# ---------------------------------------------------------------------------

@router.post("/booking/new", status_code=status.HTTP_204_NO_CONTENT)
async def booking_new(
    payload: BookingWebhookPayload,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Booking.com booking webhook — new booking notification.

    Creates a Ride with status TO_ASSIGN and stores Booking.com metadata.
    Returns 204 (fire & forget from Booking.com's perspective).
    """
    await _validate_webhook_secret(db, authorization)

    # Check for duplicate
    existing_result = await db.execute(
        select(Ride).where(
            Ride.booking_reference == payload.bookingReference,
            Ride.source_platform == "booking.com",
        )
    )
    if existing_result.scalar_one_or_none():
        logger.info("Duplicate booking %s, ignoring", payload.bookingReference)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    now = datetime.now(timezone.utc)

    # Build passenger info
    passenger_name = f"{payload.leadPassenger.firstName} {payload.leadPassenger.lastName}"
    passenger_phone = payload.leadPassenger.phoneNumber

    # Services as serializable dicts
    services = (
        [{"name": s.name, "value": s.value} for s in payload.services]
        if payload.services
        else None
    )

    ride = Ride(
        id=uuid.uuid4(),
        external_id=payload.bookingReference,
        source_platform="booking.com",
        status=RideStatus.TO_ASSIGN,
        pickup_address="Da definire",  # Will be filled by search or polling
        dropoff_address="Da definire",
        scheduled_at=now + timedelta(hours=24),  # placeholder
        passenger_name=passenger_name,
        passenger_phone=passenger_phone,
        passenger_count=1,
        notes=payload.comment,
        flight_number=payload.flightNumber,
        booking_reference=payload.bookingReference,
        booking_customer_ref=payload.customerReference,
        booking_services=services,
        booking_raw_payload=payload.model_dump(),
        created_at=now,
        updated_at=now,
    )
    db.add(ride)

    # Record history
    history = RideHistory(
        ride_id=ride.id,
        old_status=None,
        new_status=RideStatus.TO_ASSIGN.value,
        changed_by=None,
        changed_at=now,
        notes=f"Booking received from Booking.com (ref: {payload.bookingReference})",
    )
    db.add(history)
    await db.flush()

    logger.info(
        "New booking from Booking.com: %s, passenger: %s",
        payload.bookingReference,
        passenger_name,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# PATCH /booking/{booking_reference}  -  Update/cancel from Booking.com
# ---------------------------------------------------------------------------

@router.patch("/booking/{booking_reference}", status_code=status.HTTP_204_NO_CONTENT)
async def booking_update(
    booking_reference: str,
    payload: BookingUpdatePayload,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Booking.com update webhook — amendment or cancellation."""
    await _validate_webhook_secret(db, authorization)

    # Find the ride
    result = await db.execute(
        select(Ride).where(
            Ride.booking_reference == booking_reference,
            Ride.source_platform == "booking.com",
        )
    )
    ride = result.scalar_one_or_none()

    if not ride:
        logger.warning("Booking update for unknown ref: %s", booking_reference)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    now = datetime.now(timezone.utc)

    if payload.action == "CANCELLATION":
        old_status = ride.status
        ride.status = RideStatus.CANCELLED
        ride.updated_at = now

        history = RideHistory(
            ride_id=ride.id,
            old_status=old_status.value,
            new_status=RideStatus.CANCELLED.value,
            changed_by=None,
            changed_at=now,
            notes=f"Cancelled by Booking.com: {payload.cancellationReason or 'No reason'}",
        )
        db.add(history)
        logger.info("Booking %s cancelled by Booking.com", booking_reference)

    elif payload.action == "AMENDMENT":
        # Update amendable fields
        if payload.leadPassenger:
            ride.passenger_name = (
                f"{payload.leadPassenger.firstName} {payload.leadPassenger.lastName}"
            )
            if payload.leadPassenger.phoneNumber:
                ride.passenger_phone = payload.leadPassenger.phoneNumber

        if payload.flightNumber:
            ride.flight_number = payload.flightNumber
        if payload.comment:
            ride.notes = payload.comment
        if payload.pickupDateTime:
            try:
                ride.scheduled_at = datetime.fromisoformat(
                    payload.pickupDateTime.replace("Z", "+00:00")
                )
            except ValueError:
                pass
        if payload.services:
            ride.booking_services = [
                {"name": s.name, "value": s.value} for s in payload.services
            ]

        ride.updated_at = now

        history = RideHistory(
            ride_id=ride.id,
            old_status=ride.status.value,
            new_status=ride.status.value,
            changed_by=None,
            changed_at=now,
            notes="Booking amended by Booking.com",
        )
        db.add(history)
        logger.info("Booking %s amended by Booking.com", booking_reference)

    await db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# POST /booking/incident  -  Incident from Booking.com
# ---------------------------------------------------------------------------

@router.post("/booking/incident", status_code=status.HTTP_204_NO_CONTENT)
async def booking_incident(
    payload: IncidentPayload,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Booking.com incident webhook — log the incident."""
    await _validate_webhook_secret(db, authorization)

    logger.warning(
        "Booking.com incident: ref=%s, type=%s, status=%s, responsible=%s, desc=%s",
        payload.bookingReference,
        payload.incidentType,
        payload.status,
        payload.responsibleParty,
        payload.description,
    )

    # Find associated ride and add a note
    result = await db.execute(
        select(Ride).where(
            Ride.booking_reference == payload.bookingReference,
            Ride.source_platform == "booking.com",
        )
    )
    ride = result.scalar_one_or_none()

    if ride:
        now = datetime.now(timezone.utc)
        history = RideHistory(
            ride_id=ride.id,
            old_status=ride.status.value,
            new_status=ride.status.value,
            changed_by=None,
            changed_at=now,
            notes=f"Booking.com incident: {payload.incidentType} - {payload.description or 'No details'}",
        )
        db.add(history)
        await db.flush()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
