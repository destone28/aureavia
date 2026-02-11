from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from datetime import datetime, timedelta, timezone
from app.schemas.auth import (
    LoginRequest,
    TwoFactorRequest,
    TokenResponse,
    TempTokenResponse,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import (
    authenticate_user,
    initiate_2fa,
    verify_2fa_code,
    generate_2fa_code,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    create_temp_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.utils.email import send_reset_password_email
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

    # Generate and send 2FA code (DEV_MODE handled inside email module)
    sent = await initiate_2fa(db, user)

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send verification code. Please try again later.",
        )

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

    # Create access and refresh tokens (include user info for frontend)
    user_claims = {
        "email": user.email,
        "role": user.role.value,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    access_token = create_access_token(str(user.id), extra_claims=user_claims)
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

    # Create new access token with user claims
    user_claims = {
        "email": user.email,
        "role": user.role.value,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    access_token = create_access_token(str(user.id), extra_claims=user_claims)

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token  # Return the same refresh token
    )


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a password reset code to the user's email.

    Always returns 200 to avoid email enumeration.
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user:
        code = generate_2fa_code()
        user.two_factor_code = hash_password(code)
        user.two_factor_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        await db.flush()

        # DEV_MODE check is handled inside send_reset_password_email
        await send_reset_password_email(user.email, code)

    return {"message": "If the email exists, a reset code has been sent"}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using the code received via email.

    The token field contains 'email:code' format.
    """
    # Parse token as "email:code"
    parts = request.token.split(":", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token format. Use email:code",
        )

    email, code = parts
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.two_factor_code or not user.two_factor_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    if datetime.now(timezone.utc) > user.two_factor_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired",
        )

    if not verify_password(code, user.two_factor_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code",
        )

    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    user.password_hash = hash_password(request.new_password)
    user.two_factor_code = None
    user.two_factor_expires = None
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return {"message": "Password reset successfully"}
