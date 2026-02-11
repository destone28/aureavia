import logging
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
from app.utils.email import send_2fa_email

logger = logging.getLogger(__name__)


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


async def initiate_2fa(db: AsyncSession, user: User) -> bool:
    """Generate, store, and send a 2FA code to the user.

    The email module handles DEV_MODE internally:
    - DEV_MODE=True → code logged to console
    - DEV_MODE=False → code sent via SMTP

    Returns True if the code was delivered successfully.
    """
    code = generate_2fa_code()
    user.two_factor_code = hash_password(code)  # Store hashed
    user.two_factor_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    await db.flush()

    sent = await send_2fa_email(user.email, code)
    if not sent:
        logger.error("Failed to send 2FA code to %s", user.email)
    return sent


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
