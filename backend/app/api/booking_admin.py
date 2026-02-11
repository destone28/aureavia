"""Admin endpoints for managing Booking.com integration configuration."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.schemas.booking import (
    BookingConfigResponse,
    BookingConfigUpdate,
    BookingSyncResult,
    BookingTestResult,
)
from app.services.booking_service import (
    get_booking_config,
    poll_new_bookings,
    test_connection,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /config — Read current config (secrets masked)
# ---------------------------------------------------------------------------

@router.get("/config", response_model=BookingConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Get current Booking.com integration configuration."""
    config = await get_booking_config(db)

    return BookingConfigResponse(
        client_id=config.client_id or "",
        api_base_url=config.api_base_url,
        webhook_secret=config.webhook_secret or "",
        is_enabled=config.is_enabled,
        environment=config.environment,
        last_sync_at=config.last_sync_at.isoformat() if config.last_sync_at else None,
        has_client_secret=bool(config.client_secret),
    )


# ---------------------------------------------------------------------------
# PUT /config — Update config
# ---------------------------------------------------------------------------

@router.put("/config", response_model=BookingConfigResponse)
async def update_config(
    data: BookingConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Update Booking.com integration configuration."""
    config = await get_booking_config(db)

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(config, field, value)

    # If environment changed, update api_base_url accordingly (unless explicitly set)
    if "environment" in update_fields and "api_base_url" not in update_fields:
        if data.environment == "sandbox":
            config.api_base_url = "https://taxi-api-sandbox.booking.com"
        elif data.environment == "production":
            config.api_base_url = "https://taxi-api.booking.com"

    # Invalidate cached token when credentials change
    if "client_id" in update_fields or "client_secret" in update_fields:
        config.access_token = None
        config.token_expires_at = None

    config.updated_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info("Booking config updated by user %s", current_user.email)

    return BookingConfigResponse(
        client_id=config.client_id or "",
        api_base_url=config.api_base_url,
        webhook_secret=config.webhook_secret or "",
        is_enabled=config.is_enabled,
        environment=config.environment,
        last_sync_at=config.last_sync_at.isoformat() if config.last_sync_at else None,
        has_client_secret=bool(config.client_secret),
    )


# ---------------------------------------------------------------------------
# POST /test — Test connection to Booking.com API
# ---------------------------------------------------------------------------

@router.post("/test", response_model=BookingTestResult)
async def test_booking_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Test OAuth2 connection to Booking.com API."""
    success, message = await test_connection(db)

    return BookingTestResult(success=success, message=message)


# ---------------------------------------------------------------------------
# POST /sync — Manual sync (poll new bookings)
# ---------------------------------------------------------------------------

@router.post("/sync", response_model=BookingSyncResult)
async def sync_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Manually trigger a sync with Booking.com to import new bookings."""
    try:
        new_count, updated_count = await poll_new_bookings(db)
        return BookingSyncResult(
            success=True,
            new_rides=new_count,
            updated_rides=updated_count,
            message=f"Sincronizzazione completata: {new_count} nuove corse, {updated_count} aggiornate",
        )
    except Exception as e:
        logger.error("Manual sync failed: %s", e)
        return BookingSyncResult(
            success=False,
            message=f"Errore durante la sincronizzazione: {str(e)}",
        )
