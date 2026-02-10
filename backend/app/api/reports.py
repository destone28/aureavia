from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_, case
from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.ride import Ride, RideStatus
from app.models.driver import Driver
from app.models.review import Review
from app.schemas.report import DashboardKPIs, EarningsReport, EarningsDataPoint
from datetime import datetime, date, timedelta, timezone
from typing import Optional


router = APIRouter()

# Roles that can access reports
REPORT_ROLES = (UserRole.ADMIN, UserRole.ASSISTANT, UserRole.FINANCE)


# ---------------------------------------------------------------------------
# GET /dashboard  -  Dashboard KPIs
# ---------------------------------------------------------------------------
@router.get(
    "/dashboard",
    response_model=DashboardKPIs,
    dependencies=[Depends(require_role(*REPORT_ROLES))],
)
async def get_dashboard_kpis(
    period_days: int = Query(30, ge=1, le=365, description="Number of days for the current period"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return dashboard KPIs with change percentages vs. the previous period.

    The current period covers the last `period_days` days. The previous period
    covers the `period_days` before that, and is used to calculate the change
    percentages for rides and revenue.
    """
    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=period_days)
    previous_start = current_start - timedelta(days=period_days)

    # -- Total rides (current period) -----------------------------------------
    current_rides_result = await db.execute(
        select(func.count(Ride.id)).where(
            Ride.created_at >= current_start,
            Ride.created_at < now,
        )
    )
    total_rides = current_rides_result.scalar() or 0

    # -- Total rides (previous period) ----------------------------------------
    previous_rides_result = await db.execute(
        select(func.count(Ride.id)).where(
            Ride.created_at >= previous_start,
            Ride.created_at < current_start,
        )
    )
    previous_rides = previous_rides_result.scalar() or 0

    # -- Revenue (current period) — sum of price for completed rides ----------
    current_revenue_result = await db.execute(
        select(func.coalesce(func.sum(Ride.price), 0)).where(
            Ride.status == RideStatus.COMPLETED,
            Ride.completed_at >= current_start,
            Ride.completed_at < now,
        )
    )
    total_revenue = float(current_revenue_result.scalar() or 0)

    # -- Revenue (previous period) --------------------------------------------
    previous_revenue_result = await db.execute(
        select(func.coalesce(func.sum(Ride.price), 0)).where(
            Ride.status == RideStatus.COMPLETED,
            Ride.completed_at >= previous_start,
            Ride.completed_at < current_start,
        )
    )
    previous_revenue = float(previous_revenue_result.scalar() or 0)

    # -- Active drivers (drivers with at least one ride in the current period)
    active_drivers_result = await db.execute(
        select(func.count(func.distinct(Ride.driver_id))).where(
            Ride.driver_id.is_not(None),
            Ride.created_at >= current_start,
            Ride.created_at < now,
        )
    )
    active_drivers = active_drivers_result.scalar() or 0

    # -- Average rating (all-time) --------------------------------------------
    avg_rating_result = await db.execute(
        select(func.coalesce(func.avg(Review.rating), 0))
    )
    avg_rating = round(float(avg_rating_result.scalar() or 0), 2)

    # -- Change percentages ---------------------------------------------------
    rides_change_pct = _calc_change_pct(total_rides, previous_rides)
    revenue_change_pct = _calc_change_pct(total_revenue, previous_revenue)

    return DashboardKPIs(
        total_rides=total_rides,
        active_drivers=active_drivers,
        total_revenue=total_revenue,
        avg_rating=avg_rating,
        rides_change_pct=rides_change_pct,
        revenue_change_pct=revenue_change_pct,
    )


# ---------------------------------------------------------------------------
# GET /earnings  -  Earnings data points for charts
# ---------------------------------------------------------------------------
@router.get(
    "/earnings",
    response_model=EarningsReport,
    dependencies=[Depends(require_role(*REPORT_ROLES))],
)
async def get_earnings(
    granularity: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return earnings data points aggregated by the requested granularity.

    Only completed rides are included. Defaults to the last 30 days when no
    date range is provided.
    """
    today = date.today()

    if date_from is None:
        date_from = today - timedelta(days=30)
    if date_to is None:
        date_to = today

    # Convert date bounds to datetimes for comparison with TIMESTAMP columns
    dt_from = datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc)
    dt_to = datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc)

    # Build the date-truncation expression based on granularity
    if granularity == "daily":
        date_trunc = func.date_trunc("day", Ride.completed_at)
        date_fmt = "%Y-%m-%d"
    elif granularity == "weekly":
        date_trunc = func.date_trunc("week", Ride.completed_at)
        date_fmt = "%Y-%m-%d"  # start-of-week date
    else:  # monthly
        date_trunc = func.date_trunc("month", Ride.completed_at)
        date_fmt = "%Y-%m"

    stmt = (
        select(
            date_trunc.label("period"),
            func.coalesce(func.sum(Ride.price), 0).label("amount"),
        )
        .where(
            Ride.status == RideStatus.COMPLETED,
            Ride.completed_at >= dt_from,
            Ride.completed_at <= dt_to,
        )
        .group_by("period")
        .order_by("period")
    )

    result = await db.execute(stmt)
    rows = result.all()

    data = []
    for period, amount in rows:
        # period comes back as a datetime from date_trunc
        if isinstance(period, datetime):
            label = period.strftime(date_fmt)
        else:
            label = str(period)
        data.append(EarningsDataPoint(date=label, amount=float(amount)))

    return EarningsReport(granularity=granularity, data=data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _calc_change_pct(current: float, previous: float) -> float:
    """Calculate percentage change between two values.

    Returns 0.0 when there is no previous data, avoiding division by zero.
    """
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)
