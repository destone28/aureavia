# Re-export all schemas for easy imports
from app.schemas.auth import (
    LoginRequest,
    TwoFactorRequest,
    TokenResponse,
    TempTokenResponse,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordChangeRequest,
)
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyWithStats,
)
from app.schemas.driver import (
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverStats,
    DriverWithUserResponse,
)
from app.schemas.ride import (
    RideWebhook,
    RideCreate,
    RideUpdate,
    RideResponse,
    RideWithDriverResponse,
    RideListResponse,
    AssignRideRequest,
)
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewWithRideResponse,
)
from app.schemas.notification import (
    NotificationResponse,
)
from app.schemas.report import (
    DashboardKPIs,
    EarningsDataPoint,
    EarningsReport,
    RideExportRow,
)

__all__ = [
    # Auth
    "LoginRequest",
    "TwoFactorRequest",
    "TokenResponse",
    "TempTokenResponse",
    "RefreshRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "PasswordChangeRequest",
    # Company
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyWithStats",
    # Driver
    "DriverCreate",
    "DriverUpdate",
    "DriverResponse",
    "DriverStats",
    "DriverWithUserResponse",
    # Ride
    "RideWebhook",
    "RideCreate",
    "RideUpdate",
    "RideResponse",
    "RideWithDriverResponse",
    "RideListResponse",
    "AssignRideRequest",
    # Review
    "ReviewCreate",
    "ReviewResponse",
    "ReviewWithRideResponse",
    # Notification
    "NotificationResponse",
    # Report
    "DashboardKPIs",
    "EarningsDataPoint",
    "EarningsReport",
    "RideExportRow",
]
