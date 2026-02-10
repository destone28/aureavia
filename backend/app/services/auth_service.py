import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    create_temp_token,
)
from app.config import settings


def generate_2fa_code() -> str:
    """Generate a 6-digit 2FA code."""
    return ''.join(random.choices(string.digits, k=6))


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return None

    return user


async def initiate_2fa(db: AsyncSession, user: User) -> str:
    """
    Generate and store a 2FA code for the user.
    Returns the code (in dev mode) or None (in production).
    """
    code = generate_2fa_code()
    user.two_factor_code = hash_password(code)  # Store hashed
    user.two_factor_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    await db.flush()

    # In dev mode, return the code; in prod, send email and return None
    if settings.DEV_MODE:
        print(f"\n🔐 2FA CODE for {user.email}: {code}\n")
        return code
    else:
        # TODO: Send email with code
        return None


async def verify_2fa_code(db: AsyncSession, user: User, code: str) -> bool:
    """Verify the 2FA code provided by the user."""
    if not user.two_factor_code or not user.two_factor_expires:
        return False

    if datetime.now(timezone.utc) > user.two_factor_expires:
        return False

    is_valid = verify_password(code, user.two_factor_code)

    if is_valid:
        # Clear the 2FA code after successful verification
        user.two_factor_code = None
        user.two_factor_expires = None
        user.last_login = datetime.now(timezone.utc)
        await db.flush()

    return is_valid
