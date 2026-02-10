from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.ride import (
    RideCreate,
    RideUpdate,
    RideResponse,
    RideListResponse,
    AssignRideRequest,
)
from app.services.ride_service import (
    get_rides,
    get_ride,
    create_ride,
    update_ride,
    assign_ride,
    accept_ride,
    start_ride,
    complete_ride,
    cancel_ride,
    RideServiceError,
)
from datetime import date
from typing import Optional
import uuid


router = APIRouter()


class CancelRequest(BaseModel):
    notes: str | None = None


def _handle_service_error(exc: RideServiceError):
    """Convert RideServiceError to HTTPException."""
    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.message,
    )


# ---------------------------------------------------------------------------
# GET /  -  List rides
# ---------------------------------------------------------------------------
@router.get("/", response_model=RideListResponse)
async def list_rides(
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    driver_id: Optional[uuid.UUID] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List rides. Admin/assistant/finance see all; drivers see own + unassigned."""
    effective_driver_id = driver_id
    if current_user.role == UserRole.DRIVER:
        effective_driver_id = None

    rides, total = await get_rides(
        db=db,
        requesting_user=current_user,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        driver_id=effective_driver_id,
        source_platform=source,
        page=page,
        page_size=page_size,
    )

    return RideListResponse(
        rides=rides,
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /{ride_id}  -  Get single ride
# ---------------------------------------------------------------------------
@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride_detail(
    ride_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single ride by id."""
    try:
        ride = await get_ride(db=db, ride_id=ride_id)
    except RideServiceError as exc:
        _handle_service_error(exc)

    # Drivers may only view their own rides or unassigned rides
    if current_user.role == UserRole.DRIVER:
        if ride.driver_id is not None and ride.driver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this ride",
            )

    return ride


# ---------------------------------------------------------------------------
# POST /  -  Create ride (admin / assistant only)
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=RideResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ASSISTANT))],
)
async def create_ride_endpoint(
    ride_in: RideCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new ride (admin/assistant only)."""
    ride_data = ride_in.model_dump()
    ride = await create_ride(db=db, ride_data=ride_data, created_by_id=current_user.id)
    return ride


# ---------------------------------------------------------------------------
# PUT /{ride_id}  -  Update ride (admin / assistant only)
# ---------------------------------------------------------------------------
@router.put(
    "/{ride_id}",
    response_model=RideResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ASSISTANT))],
)
async def update_ride_endpoint(
    ride_id: uuid.UUID,
    ride_in: RideUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update ride details (admin/assistant only)."""
    try:
        ride_data = ride_in.model_dump(exclude_unset=True)
        updated = await update_ride(db=db, ride_id=ride_id, ride_data=ride_data)
    except RideServiceError as exc:
        _handle_service_error(exc)

    return updated


# ---------------------------------------------------------------------------
# PUT /{ride_id}/assign  -  Assign ride to a driver (admin / assistant only)
# ---------------------------------------------------------------------------
@router.put(
    "/{ride_id}/assign",
    response_model=RideResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ASSISTANT))],
)
async def assign_ride_endpoint(
    ride_id: uuid.UUID,
    body: AssignRideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a ride to a specific driver (admin/assistant only)."""
    try:
        updated = await assign_ride(
            db=db,
            ride_id=ride_id,
            driver_id=body.driver_id,
            assigned_by_id=current_user.id,
        )
    except RideServiceError as exc:
        _handle_service_error(exc)

    return updated


# ---------------------------------------------------------------------------
# PUT /{ride_id}/accept  -  Driver accepts an assigned ride
# ---------------------------------------------------------------------------
@router.put("/{ride_id}/accept", response_model=RideResponse)
async def accept_ride_endpoint(
    ride_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Driver accepts an assigned ride."""
    if current_user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can accept rides",
        )

    try:
        updated = await accept_ride(
            db=db, ride_id=ride_id, driver_id=current_user.id
        )
    except RideServiceError as exc:
        _handle_service_error(exc)

    return updated


# ---------------------------------------------------------------------------
# PUT /{ride_id}/start  -  Driver starts a ride
# ---------------------------------------------------------------------------
@router.put("/{ride_id}/start", response_model=RideResponse)
async def start_ride_endpoint(
    ride_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Driver starts an accepted ride."""
    if current_user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can start rides",
        )

    try:
        updated = await start_ride(
            db=db, ride_id=ride_id, driver_id=current_user.id
        )
    except RideServiceError as exc:
        _handle_service_error(exc)

    return updated


# ---------------------------------------------------------------------------
# PUT /{ride_id}/complete  -  Driver completes a ride
# ---------------------------------------------------------------------------
@router.put("/{ride_id}/complete", response_model=RideResponse)
async def complete_ride_endpoint(
    ride_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Driver completes an in-progress ride."""
    if current_user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can complete rides",
        )

    try:
        updated = await complete_ride(
            db=db, ride_id=ride_id, driver_id=current_user.id
        )
    except RideServiceError as exc:
        _handle_service_error(exc)

    return updated


# ---------------------------------------------------------------------------
# PUT /{ride_id}/cancel  -  Cancel a ride (admin or assigned driver)
# ---------------------------------------------------------------------------
@router.put("/{ride_id}/cancel", response_model=RideResponse)
async def cancel_ride_endpoint(
    ride_id: uuid.UUID,
    body: CancelRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a ride. Admins/assistants can cancel any ride; drivers can only
    cancel rides assigned to them."""
    notes = body.notes if body else None

    try:
        updated = await cancel_ride(
            db=db,
            ride_id=ride_id,
            cancelled_by_id=current_user.id,
            notes=notes,
        )
    except RideServiceError as exc:
        _handle_service_error(exc)

    return updated
