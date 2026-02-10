from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    TwoFactorRequest,
    TokenResponse,
    TempTokenResponse,
    RefreshRequest,
)
from app.services.auth_service import (
    authenticate_user,
    initiate_2fa,
    verify_2fa_code,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    create_temp_token,
    decode_access_token,
)
from app.models.user import User
from app.config import settings

router = APIRouter()


@router.post("/login", response_model=TempTokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1 of 2FA login: Validate email+password, send 2FA code.
    Returns a temporary token to use in the verify-2fa endpoint.
    """
    user = await authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Generate and send 2FA code
    await initiate_2fa(db, user)

    # Create temporary token (10 min expiry)
    temp_token = create_temp_token(str(user.id))

    return TempTokenResponse(
        temp_token=temp_token,
        message="2FA code sent to your email" if not settings.DEV_MODE else "Check console for 2FA code"
    )


@router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa(
    request: TwoFactorRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2 of 2FA login: Verify the 2FA code.
    Returns access and refresh tokens upon success.
    """
    # Decode temp token to get user_id
    payload = decode_access_token(request.temp_token)
    if not payload or payload.get("type") != "temp":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired temporary token"
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Verify 2FA code
    is_valid = await verify_2fa_code(db, user, request.code)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired 2FA code"
        )

    # Create access and refresh tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh an access token using a refresh token."""
    payload = decode_access_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload.get("sub")

    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new access token
    access_token = create_access_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token  # Return the same refresh token
    )


# TODO: Implement forgot-password and reset-password endpoints (Giorno 2)
