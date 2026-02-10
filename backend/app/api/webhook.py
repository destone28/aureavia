from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.ride import Ride, RideStatus
from app.schemas.ride import RideWebhook, RideResponse
from datetime import datetime, timezone


router = APIRouter()


# ---------------------------------------------------------------------------
# POST /booking  -  Receive booking from external platform
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
    """Receive a booking from an external platform and create a ride with
    status TO_ASSIGN.

    No authentication is required (in production, this would be secured
    with an API key header).

    Duplicate external_id values for the same source_platform are rejected
    with HTTP 409 Conflict.
    """
    # Check for duplicate external_id on the same platform
    if payload.external_id:
        result = await db.execute(
            select(Ride).where(
                Ride.external_id == payload.external_id,
                Ride.source_platform == payload.source_platform,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
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
