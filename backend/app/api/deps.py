import secrets
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.utils.security import decode_access_token
from app.models.user import User, UserRole
from app.config import settings

security = HTTPBearer(auto_error=False)
basic_security = HTTPBasic(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def require_role(*allowed_roles: UserRole):
    """Dependency factory to require specific user roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user
    return role_checker


async def verify_etg_auth(
    credentials: HTTPBasicCredentials | None = Depends(basic_security),
    x_api_key: str | None = Header(None),
) -> bool:
    """Verify ETG API authentication via Basic Auth or API Key header.

    ETG can authenticate using either:
    - HTTP Basic Auth (username=ETG_API_KEY, password=ETG_API_SECRET)
    - X-API-Key header matching ETG_API_KEY
    """
    # Try Basic Auth first
    if credentials is not None:
        correct_username = secrets.compare_digest(credentials.username, settings.ETG_API_KEY)
        correct_password = secrets.compare_digest(credentials.password, settings.ETG_API_SECRET)
        if correct_username and correct_password:
            return True

    # Try API Key header
    if x_api_key is not None:
        if secrets.compare_digest(x_api_key, settings.ETG_API_KEY):
            return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid ETG credentials",
        headers={"WWW-Authenticate": "Basic"},
    )
