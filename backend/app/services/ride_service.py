from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Any

from app.models.ride import Ride, RideStatus
from app.models.ride_history import RideHistory
from app.models.driver import Driver
from app.models.notification import Notification
from app.models.user import User, UserRole


# ---------------------------------------------------------------------------
# Valid state transitions
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[RideStatus, set[RideStatus]] = {
    RideStatus.TO_ASSIGN: {RideStatus.BOOKED, RideStatus.CANCELLED, RideStatus.CRITICAL},
    RideStatus.CRITICAL: {RideStatus.BOOKED, RideStatus.CANCELLED},
    RideStatus.BOOKED: {RideStatus.IN_PROGRESS, RideStatus.CANCELLED},
    RideStatus.IN_PROGRESS: {RideStatus.COMPLETED, RideStatus.CANCELLED},
    RideStatus.COMPLETED: set(),
    RideStatus.CANCELLED: set(),
}


class RideServiceError(Exception):
    """Base exception for ride service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_transition(current: RideStatus, target: RideStatus) -> None:
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise RideServiceError(
            f"Invalid status transition: {current.value} -> {target.value}"
        )


def _create_history(
    ride: Ride,
    old_status: RideStatus | None,
    new_status: RideStatus,
    changed_by: UUID | None,
    notes: str | None = None,
) -> RideHistory:
    return RideHistory(
        ride_id=ride.id,
        old_status=old_status.value if old_status else None,
        new_status=new_status.value,
        changed_by=changed_by,
        changed_at=_now(),
        notes=notes,
    )


def _create_notification(
    user_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    ride_id: UUID | None = None,
) -> Notification:
    return Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        ride_id=ride_id,
        sent_at=_now(),
    )


# ---------------------------------------------------------------------------
# 1. get_rides
# ---------------------------------------------------------------------------

async def get_rides(
    db: AsyncSession,
    *,
    status: RideStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    driver_id: UUID | None = None,
    source_platform: str | None = None,
    page: int = 1,
    page_size: int = 50,
    requesting_user: User | None = None,
) -> tuple[list[Ride], int]:
    """Return a paginated list of rides with optional filters.

    If *requesting_user* is a driver, results are limited to their own rides
    plus rides that are still unassigned (TO_ASSIGN / CRITICAL).
    """
    query = select(Ride)
    count_query = select(func.count(Ride.id))

    filters: list[Any] = []

    # Scope rides for driver users
    if requesting_user and requesting_user.role == UserRole.DRIVER:
        filters.append(
            or_(
                Ride.driver_id == requesting_user.id,
                Ride.status.in_([RideStatus.TO_ASSIGN, RideStatus.CRITICAL]),
            )
        )

    if status is not None:
        filters.append(Ride.status == status)
    if date_from is not None:
        filters.append(Ride.scheduled_at >= date_from)
    if date_to is not None:
        filters.append(Ride.scheduled_at <= date_to)
    if driver_id is not None:
        filters.append(Ride.driver_id == driver_id)
    if source_platform is not None:
        filters.append(Ride.source_platform == source_platform)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch page
    offset = (page - 1) * page_size
    query = (
        query
        .options(selectinload(Ride.driver))
        .order_by(Ride.scheduled_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    rides = list(result.scalars().all())

    return rides, total


# ---------------------------------------------------------------------------
# 2. get_ride
# ---------------------------------------------------------------------------

async def get_ride(db: AsyncSession, ride_id: UUID) -> Ride:
    """Fetch a single ride by ID, including driver and history."""
    query = (
        select(Ride)
        .where(Ride.id == ride_id)
        .options(
            selectinload(Ride.driver),
            selectinload(Ride.history),
        )
    )
    result = await db.execute(query)
    ride = result.scalar_one_or_none()
    if ride is None:
        raise RideServiceError("Ride not found", status_code=404)
    return ride


# ---------------------------------------------------------------------------
# 3. create_ride
# ---------------------------------------------------------------------------

async def create_ride(
    db: AsyncSession,
    ride_data: dict[str, Any],
    created_by_id: UUID | None = None,
) -> Ride:
    """Create a new ride and record the initial history entry."""
    ride = Ride(**ride_data)
    if ride.status is None:
        ride.status = RideStatus.TO_ASSIGN
    ride.created_at = _now()
    ride.updated_at = _now()

    db.add(ride)
    await db.flush()

    # Record creation in history
    history = _create_history(
        ride=ride,
        old_status=None,
        new_status=ride.status,
        changed_by=created_by_id,
        notes="Ride created",
    )
    db.add(history)
    await db.flush()

    return ride


# ---------------------------------------------------------------------------
# 4. update_ride
# ---------------------------------------------------------------------------

async def update_ride(
    db: AsyncSession,
    ride_id: UUID,
    ride_data: dict[str, Any],
) -> Ride:
    """Update mutable fields on a ride. Does NOT handle status changes --
    use the dedicated transition functions instead.
    """
    ride = await get_ride(db, ride_id)

    # Pop status to prevent accidental state changes through this endpoint
    ride_data.pop("status", None)

    for field, value in ride_data.items():
        if value is not None and hasattr(ride, field):
            setattr(ride, field, value)

    ride.updated_at = _now()
    await db.flush()
    return ride


# ---------------------------------------------------------------------------
# 5. assign_ride
# ---------------------------------------------------------------------------

async def assign_ride(
    db: AsyncSession,
    ride_id: UUID,
    driver_id: UUID,
    assigned_by_id: UUID,
) -> Ride:
    """Assign a ride to a driver. Status stays TO_ASSIGN (or CRITICAL) until
    the driver explicitly accepts.
    """
    ride = await get_ride(db, ride_id)

    if ride.status not in (RideStatus.TO_ASSIGN, RideStatus.CRITICAL):
        raise RideServiceError(
            f"Cannot assign a ride in status '{ride.status.value}'. "
            "Only TO_ASSIGN or CRITICAL rides can be assigned."
        )

    # Verify driver exists and is active
    driver_user = await db.execute(
        select(User).where(User.id == driver_id, User.role == UserRole.DRIVER)
    )
    driver_user = driver_user.scalar_one_or_none()
    if driver_user is None:
        raise RideServiceError("Driver not found", status_code=404)

    ride.driver_id = driver_id
    ride.assigned_by = assigned_by_id
    ride.updated_at = _now()

    # If the ride was critical, note the resolution
    if ride.status == RideStatus.CRITICAL:
        ride.critical_resolved_at = _now()
        ride.critical_resolution_type = "assigned"

    await db.flush()

    # Notify the driver
    notification = _create_notification(
        user_id=driver_id,
        notification_type="ride_assigned",
        title="Nuova corsa assegnata",
        body=f"Ti è stata assegnata una corsa: {ride.pickup_address} → {ride.dropoff_address}",
        ride_id=ride.id,
    )
    db.add(notification)
    await db.flush()

    return ride


# ---------------------------------------------------------------------------
# 6. accept_ride
# ---------------------------------------------------------------------------

async def accept_ride(
    db: AsyncSession,
    ride_id: UUID,
    driver_id: UUID,
) -> Ride:
    """Driver accepts an assigned ride. Transitions to BOOKED."""
    ride = await get_ride(db, ride_id)

    if ride.driver_id != driver_id:
        raise RideServiceError(
            "You are not assigned to this ride", status_code=403
        )

    old_status = ride.status
    _validate_transition(old_status, RideStatus.BOOKED)

    ride.status = RideStatus.BOOKED
    ride.updated_at = _now()

    # If ride was critical, mark as resolved
    if old_status == RideStatus.CRITICAL:
        ride.critical_resolved_at = _now()
        ride.critical_resolution_type = "accepted"

    history = _create_history(
        ride=ride,
        old_status=old_status,
        new_status=RideStatus.BOOKED,
        changed_by=driver_id,
        notes="Driver accepted the ride",
    )
    db.add(history)

    # Notify admins that ride was accepted
    admin_query = select(User).where(
        User.role.in_([UserRole.ADMIN, UserRole.ASSISTANT])
    )
    admin_result = await db.execute(admin_query)
    admins = admin_result.scalars().all()
    for admin in admins:
        notification = _create_notification(
            user_id=admin.id,
            notification_type="ride_accepted",
            title="Corsa accettata",
            body=f"La corsa {ride.pickup_address} → {ride.dropoff_address} è stata accettata dal driver.",
            ride_id=ride.id,
        )
        db.add(notification)

    await db.flush()
    return ride


# ---------------------------------------------------------------------------
# 7. start_ride
# ---------------------------------------------------------------------------

async def start_ride(
    db: AsyncSession,
    ride_id: UUID,
    driver_id: UUID,
) -> Ride:
    """Driver starts a ride. Transitions from BOOKED to IN_PROGRESS."""
    ride = await get_ride(db, ride_id)

    if ride.driver_id != driver_id:
        raise RideServiceError(
            "You are not assigned to this ride", status_code=403
        )

    old_status = ride.status
    _validate_transition(old_status, RideStatus.IN_PROGRESS)

    ride.status = RideStatus.IN_PROGRESS
    ride.started_at = _now()
    ride.updated_at = _now()

    history = _create_history(
        ride=ride,
        old_status=old_status,
        new_status=RideStatus.IN_PROGRESS,
        changed_by=driver_id,
        notes="Driver started the ride",
    )
    db.add(history)
    await db.flush()

    return ride


# ---------------------------------------------------------------------------
# 8. complete_ride
# ---------------------------------------------------------------------------

async def complete_ride(
    db: AsyncSession,
    ride_id: UUID,
    driver_id: UUID,
) -> Ride:
    """Driver completes a ride. Transitions from IN_PROGRESS to COMPLETED
    and updates driver statistics.
    """
    ride = await get_ride(db, ride_id)

    if ride.driver_id != driver_id:
        raise RideServiceError(
            "You are not assigned to this ride", status_code=403
        )

    old_status = ride.status
    _validate_transition(old_status, RideStatus.COMPLETED)

    ride.status = RideStatus.COMPLETED
    ride.completed_at = _now()
    ride.updated_at = _now()

    history = _create_history(
        ride=ride,
        old_status=old_status,
        new_status=RideStatus.COMPLETED,
        changed_by=driver_id,
        notes="Driver completed the ride",
    )
    db.add(history)

    # Update driver stats
    driver_result = await db.execute(
        select(Driver).where(Driver.user_id == driver_id)
    )
    driver = driver_result.scalar_one_or_none()
    if driver is not None:
        driver.total_rides = (driver.total_rides or 0) + 1
        if ride.distance_km:
            driver.total_km = float(driver.total_km or 0) + float(ride.distance_km)
        if ride.driver_share:
            driver.total_earnings = float(driver.total_earnings or 0) + float(ride.driver_share)
        driver.updated_at = _now()

    await db.flush()
    return ride


# ---------------------------------------------------------------------------
# 9. cancel_ride
# ---------------------------------------------------------------------------

async def cancel_ride(
    db: AsyncSession,
    ride_id: UUID,
    cancelled_by_id: UUID,
    notes: str | None = None,
) -> Ride:
    """Cancel a ride from any active status."""
    ride = await get_ride(db, ride_id)

    old_status = ride.status
    _validate_transition(old_status, RideStatus.CANCELLED)

    ride.status = RideStatus.CANCELLED
    ride.updated_at = _now()

    history = _create_history(
        ride=ride,
        old_status=old_status,
        new_status=RideStatus.CANCELLED,
        changed_by=cancelled_by_id,
        notes=notes or "Ride cancelled",
    )
    db.add(history)

    # Notify the assigned driver if any
    if ride.driver_id:
        notification = _create_notification(
            user_id=ride.driver_id,
            notification_type="ride_cancelled",
            title="Corsa cancellata",
            body=f"La corsa {ride.pickup_address} → {ride.dropoff_address} è stata cancellata.",
            ride_id=ride.id,
        )
        db.add(notification)

    await db.flush()
    return ride


# ---------------------------------------------------------------------------
# 10. check_critical_rides
# ---------------------------------------------------------------------------

async def check_critical_rides(db: AsyncSession) -> list[Ride]:
    """Find rides that are still TO_ASSIGN and scheduled within the next
    3 hours. Mark them as CRITICAL and notify admins/assistants.

    Intended to be called periodically by a Celery beat task.
    """
    threshold = _now() + timedelta(hours=3)

    query = select(Ride).where(
        and_(
            Ride.status == RideStatus.TO_ASSIGN,
            Ride.scheduled_at <= threshold,
            Ride.scheduled_at > _now(),  # exclude past rides
        )
    )
    result = await db.execute(query)
    rides = list(result.scalars().all())

    if not rides:
        return []

    # Fetch admin / assistant users for notifications
    admin_result = await db.execute(
        select(User).where(
            User.role.in_([UserRole.ADMIN, UserRole.ASSISTANT])
        )
    )
    admins = list(admin_result.scalars().all())

    critical_rides: list[Ride] = []
    for ride in rides:
        old_status = ride.status
        ride.status = RideStatus.CRITICAL
        ride.critical_at = _now()
        ride.updated_at = _now()

        history = _create_history(
            ride=ride,
            old_status=old_status,
            new_status=RideStatus.CRITICAL,
            changed_by=None,
            notes="Auto-marked as critical: < 3h to scheduled time",
        )
        db.add(history)

        # Notify each admin / assistant
        for admin in admins:
            notification = _create_notification(
                user_id=admin.id,
                notification_type="ride_critical",
                title="Corsa critica",
                body=(
                    f"La corsa {ride.pickup_address} → {ride.dropoff_address} "
                    f"(prevista alle {ride.scheduled_at:%H:%M}) non è ancora assegnata."
                ),
                ride_id=ride.id,
            )
            db.add(notification)

        critical_rides.append(ride)

    await db.flush()
    return critical_rides
