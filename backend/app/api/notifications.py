from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from datetime import datetime, timezone
import uuid


router = APIRouter()


# ---------------------------------------------------------------------------
# GET /  -  List notifications for the current user
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notifications for the current user, newest first."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
    )

    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))

    stmt = (
        stmt
        .order_by(Notification.sent_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    notifications = result.scalars().all()

    return notifications


# ---------------------------------------------------------------------------
# GET /unread-count  -  Count of unread notifications
# ---------------------------------------------------------------------------
@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the count of unread notifications for the current user."""
    result = await db.execute(
        select(func.count(Notification.id))
        .where(
            Notification.user_id == current_user.id,
            Notification.read_at.is_(None),
        )
    )
    count = result.scalar() or 0

    return {"unread_count": count}


# ---------------------------------------------------------------------------
# PUT /{notification_id}/read  -  Mark a notification as read
# ---------------------------------------------------------------------------
@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a single notification as read."""
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this notification",
        )

    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        await db.flush()

    return notification
