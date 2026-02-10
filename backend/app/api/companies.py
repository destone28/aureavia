from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.ncc_company import NCCCompany, CompanyStatus
from app.models.driver import Driver
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyWithStats
import uuid


router = APIRouter()


# ---------------------------------------------------------------------------
# GET /  -  List all companies with active driver count
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=list[CompanyWithStats],
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ASSISTANT))],
)
async def list_companies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all NCC companies with their active driver count."""
    # Sub-query: count active drivers per company
    driver_count_sq = (
        select(
            Driver.ncc_company_id,
            func.count(Driver.id).label("active_drivers"),
        )
        .join(User, Driver.user_id == User.id)
        .where(User.status == "active")
        .group_by(Driver.ncc_company_id)
        .subquery()
    )

    stmt = (
        select(NCCCompany, func.coalesce(driver_count_sq.c.active_drivers, 0).label("active_drivers"))
        .outerjoin(driver_count_sq, NCCCompany.id == driver_count_sq.c.ncc_company_id)
        .order_by(NCCCompany.name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    companies = []
    for company, active_drivers in rows:
        company_data = CompanyWithStats.model_validate(company)
        company_data.active_drivers = active_drivers
        companies.append(company_data)

    return companies


# ---------------------------------------------------------------------------
# GET /{company_id}  -  Get company details
# ---------------------------------------------------------------------------
@router.get(
    "/{company_id}",
    response_model=CompanyWithStats,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ASSISTANT))],
)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single company by ID with its active driver count."""
    result = await db.execute(
        select(NCCCompany).where(NCCCompany.id == company_id)
    )
    company = result.scalar_one_or_none()

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Count active drivers for this company
    driver_count_result = await db.execute(
        select(func.count(Driver.id))
        .join(User, Driver.user_id == User.id)
        .where(
            Driver.ncc_company_id == company_id,
            User.status == "active",
        )
    )
    active_drivers = driver_count_result.scalar() or 0

    company_data = CompanyWithStats.model_validate(company)
    company_data.active_drivers = active_drivers

    return company_data


# ---------------------------------------------------------------------------
# POST /  -  Create a new company
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def create_company(
    company_in: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new NCC company (admin only)."""
    company = NCCCompany(
        id=uuid.uuid4(),
        name=company_in.name,
        website=company_in.website,
        partner_type=company_in.partner_type,
        contact_person=company_in.contact_person,
        contact_email=company_in.contact_email,
        contact_phone=company_in.contact_phone,
        notes=company_in.notes,
        status=CompanyStatus.ACTIVE,
    )

    db.add(company)
    await db.flush()

    return company


# ---------------------------------------------------------------------------
# PUT /{company_id}  -  Update a company
# ---------------------------------------------------------------------------
@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def update_company(
    company_id: uuid.UUID,
    company_in: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing NCC company (admin only)."""
    result = await db.execute(
        select(NCCCompany).where(NCCCompany.id == company_id)
    )
    company = result.scalar_one_or_none()

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.flush()

    return company
