from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole, UserStatus
from app.models.driver import Driver
from app.models.ride import Ride, RideStatus
from app.models.review import Review
from app.models.ncc_company import NCCCompany
from app.utils.security import hash_password
from app.schemas.driver import (
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverStats,
    DriverWithUserResponse,
)
from app.schemas.review import ReviewResponse
from datetime import datetime, date, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid

router = APIRouter()


# ---------------------------------------------------------------------------
# Request schema for creating a driver (user + driver in one request)
# ---------------------------------------------------------------------------

class CreateDriverRequest(BaseModel):
    # User fields
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    # Driver fields
    ncc_company_id: uuid.UUID | None = None
    license_number: str
    license_expiry: date | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_plate: str | None = None
    vehicle_year: int | None = None
    vehicle_seats: int | None = None
    vehicle_luggage_capacity: int | None = None
    vehicle_fuel_type: str | None = None
    insurance_number: str | None = None


# ---------------------------------------------------------------------------
# Helper: build DriverWithUserResponse from a Driver with loaded relationships
# ---------------------------------------------------------------------------

def _build_driver_with_user(driver: Driver) -> DriverWithUserResponse:
    """Map a Driver ORM object (with user + ncc_company loaded) to the response schema."""
    user = driver.user
    return DriverWithUserResponse(
        id=driver.id,
        user_id=driver.user_id,
        ncc_company_id=driver.ncc_company_id,
        license_number=driver.license_number,
        license_expiry=driver.license_expiry,
        vehicle_make=driver.vehicle_make,
        vehicle_model=driver.vehicle_model,
        vehicle_plate=driver.vehicle_plate,
        vehicle_year=driver.vehicle_year,
        vehicle_seats=driver.vehicle_seats,
        vehicle_luggage_capacity=driver.vehicle_luggage_capacity,
        vehicle_fuel_type=driver.vehicle_fuel_type,
        insurance_number=driver.insurance_number,
        insurance_expiry=driver.insurance_expiry,
        vehicle_inspection_date=driver.vehicle_inspection_date,
        special_permits=driver.special_permits,
        rating_avg=float(driver.rating_avg),
        total_km=float(driver.total_km),
        total_rides=driver.total_rides,
        total_earnings=float(driver.total_earnings),
        created_at=driver.created_at,
        updated_at=driver.updated_at,
        # User fields
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        # Company name
        company_name=driver.ncc_company.name if driver.ncc_company else None,
    )


# ---------------------------------------------------------------------------
# GET / — List all drivers (admin/assistant/finance)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[DriverWithUserResponse])
async def list_drivers(
    company_id: uuid.UUID | None = Query(None, description="Filter by NCC company"),
    status_filter: UserStatus | None = Query(None, alias="status", description="Filter by user status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.ASSISTANT, UserRole.FINANCE)
    ),
):
    """List all drivers with user info and company name. Admin roles only."""
    query = (
        select(Driver)
        .options(selectinload(Driver.user), selectinload(Driver.ncc_company))
    )

    if company_id is not None:
        query = query.where(Driver.ncc_company_id == company_id)

    if status_filter is not None:
        query = query.join(User, Driver.user_id == User.id).where(
            User.status == status_filter
        )

    result = await db.execute(query)
    drivers = result.scalars().all()

    return [_build_driver_with_user(d) for d in drivers]


# ---------------------------------------------------------------------------
# GET /{driver_id} — Get driver details
# ---------------------------------------------------------------------------

@router.get("/{driver_id}", response_model=DriverWithUserResponse)
async def get_driver(
    driver_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get driver details with user info.
    Admin/assistant/finance can access any driver.
    A driver can only access their own profile.
    """
    query = (
        select(Driver)
        .options(selectinload(Driver.user), selectinload(Driver.ncc_company))
        .where(Driver.id == driver_id)
    )
    result = await db.execute(query)
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Access control: drivers can only view their own profile
    if current_user.role == UserRole.DRIVER and driver.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own driver profile",
        )

    return _build_driver_with_user(driver)


# ---------------------------------------------------------------------------
# POST / — Create a new driver (admin only)
# ---------------------------------------------------------------------------

@router.post("/", response_model=DriverWithUserResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    data: CreateDriverRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Create a new driver together with their user account. Admin only."""

    # Check if a user with this email already exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Validate ncc_company_id if provided
    if data.ncc_company_id is not None:
        company_result = await db.execute(
            select(NCCCompany).where(NCCCompany.id == data.ncc_company_id)
        )
        if not company_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NCC company not found",
            )

    # 1. Create the User record
    new_user = User(
        id=uuid.uuid4(),
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.DRIVER,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        status=UserStatus.ACTIVE,
    )
    db.add(new_user)
    await db.flush()

    # 2. Create the Driver record
    new_driver = Driver(
        id=uuid.uuid4(),
        user_id=new_user.id,
        ncc_company_id=data.ncc_company_id,
        license_number=data.license_number,
        license_expiry=data.license_expiry,
        vehicle_make=data.vehicle_make,
        vehicle_model=data.vehicle_model,
        vehicle_plate=data.vehicle_plate,
        vehicle_year=data.vehicle_year,
        vehicle_seats=data.vehicle_seats if data.vehicle_seats is not None else 4,
        vehicle_luggage_capacity=(
            data.vehicle_luggage_capacity
            if data.vehicle_luggage_capacity is not None
            else 2
        ),
        vehicle_fuel_type=data.vehicle_fuel_type,
        insurance_number=data.insurance_number,
    )
    db.add(new_driver)
    await db.flush()

    # Reload with relationships
    query = (
        select(Driver)
        .options(selectinload(Driver.user), selectinload(Driver.ncc_company))
        .where(Driver.id == new_driver.id)
    )
    result = await db.execute(query)
    driver = result.scalar_one()

    return _build_driver_with_user(driver)


# ---------------------------------------------------------------------------
# PUT /{driver_id} — Update driver (admin only)
# ---------------------------------------------------------------------------

@router.put("/{driver_id}", response_model=DriverWithUserResponse)
async def update_driver(
    driver_id: uuid.UUID,
    data: DriverUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Update a driver's information. Admin only."""
    query = (
        select(Driver)
        .options(selectinload(Driver.user), selectinload(Driver.ncc_company))
        .where(Driver.id == driver_id)
    )
    result = await db.execute(query)
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Validate ncc_company_id if being changed
    if data.ncc_company_id is not None:
        company_result = await db.execute(
            select(NCCCompany).where(NCCCompany.id == data.ncc_company_id)
        )
        if not company_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NCC company not found",
            )

    # Apply only the fields that were explicitly set
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)

    await db.flush()

    # Reload with relationships to pick up any company change
    result = await db.execute(
        select(Driver)
        .options(selectinload(Driver.user), selectinload(Driver.ncc_company))
        .where(Driver.id == driver_id)
    )
    driver = result.scalar_one()

    return _build_driver_with_user(driver)


# ---------------------------------------------------------------------------
# GET /{driver_id}/stats — Driver statistics
# ---------------------------------------------------------------------------

@router.get("/{driver_id}/stats", response_model=DriverStats)
async def get_driver_stats(
    driver_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get driver statistics: all-time totals and current-month figures.
    Admin roles can see any driver. Drivers can only see their own stats.
    """
    # Fetch driver
    result = await db.execute(
        select(Driver).options(selectinload(Driver.user)).where(Driver.id == driver_id)
    )
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Access control
    if current_user.role == UserRole.DRIVER and driver.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own statistics",
        )

    # Current month boundaries
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Query completed rides this month for this driver
    # Rides are linked via driver_id -> users.id, so match on driver.user_id
    month_query = (
        select(
            func.count(Ride.id).label("count"),
            func.coalesce(func.sum(Ride.driver_share), 0).label("earnings"),
        )
        .where(
            Ride.driver_id == driver.user_id,
            Ride.status == RideStatus.COMPLETED,
            Ride.completed_at >= month_start,
        )
    )
    month_result = await db.execute(month_query)
    month_row = month_result.one()

    return DriverStats(
        total_rides=driver.total_rides,
        total_earnings=float(driver.total_earnings),
        total_km=float(driver.total_km),
        rating_avg=float(driver.rating_avg),
        completed_this_month=month_row.count,
        earnings_this_month=float(month_row.earnings),
    )


# ---------------------------------------------------------------------------
# GET /{driver_id}/reviews — Driver reviews (paginated)
# ---------------------------------------------------------------------------

@router.get("/{driver_id}/reviews", response_model=list[ReviewResponse])
async def get_driver_reviews(
    driver_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get paginated reviews for a driver.
    Admin roles can see any driver's reviews. Drivers can only see their own.
    """
    # Verify driver exists
    result = await db.execute(
        select(Driver).options(selectinload(Driver.user)).where(Driver.id == driver_id)
    )
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Access control
    if current_user.role == UserRole.DRIVER and driver.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own reviews",
        )

    query = (
        select(Review)
        .where(Review.driver_id == driver_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    reviews = result.scalars().all()

    return [ReviewResponse.model_validate(r) for r in reviews]
