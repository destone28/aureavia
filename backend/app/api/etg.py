"""ETG Transfers API endpoints.

AureaVia is the SUPPLIER. ETG calls these 4 endpoints to:
- Search available transfers (POST /search)
- Book a transfer (POST /book)
- Check order status (POST /status)
- Cancel an order (POST /cancel)

All endpoints require ETG authentication (Basic Auth or API Key).
All endpoints are POST per ETG spec.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import verify_etg_auth
from app.schemas.etg import (
    SearchRequest,
    SearchResponse,
    BookRequest,
    BookResponse,
    StatusRequest,
    StatusResponse,
    CancelRequest,
    CancelResponse,
)
from app.services.etg_service import (
    ETGServiceError,
    search_offers,
    book_transfer,
    get_order_status,
    cancel_order,
)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def etg_search(
    request: SearchRequest,
    _auth: bool = Depends(verify_etg_auth),
    db: AsyncSession = Depends(get_db),
):
    """Search available transfer offers. SLA: < 5 seconds."""
    try:
        return await search_offers(request, db)
    except ETGServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/book", response_model=BookResponse)
async def etg_book(
    request: BookRequest,
    _auth: bool = Depends(verify_etg_auth),
    db: AsyncSession = Depends(get_db),
):
    """Book a transfer. Creates a Ride with status TO_ASSIGN. SLA: < 30 seconds."""
    try:
        return await book_transfer(request, db)
    except ETGServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/status", response_model=StatusResponse)
async def etg_status(
    request: StatusRequest,
    _auth: bool = Depends(verify_etg_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get order status. SLA: < 30 seconds."""
    try:
        return await get_order_status(request.order_id, db)
    except ETGServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/cancel", response_model=CancelResponse)
async def etg_cancel(
    request: CancelRequest,
    _auth: bool = Depends(verify_etg_auth),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an order. Free cancellation if > 24h before pickup. SLA: < 30 seconds."""
    try:
        return await cancel_order(request.order_id, db)
    except ETGServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
