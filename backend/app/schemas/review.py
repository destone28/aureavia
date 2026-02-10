from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class ReviewBase(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
    reviewer_name: str | None = None


class ReviewCreate(ReviewBase):
    ride_id: UUID | None = None
    driver_id: UUID
    source_platform: str | None = None


class ReviewResponse(ReviewBase):
    id: UUID
    ride_id: UUID | None
    driver_id: UUID
    source_platform: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewWithRideResponse(ReviewResponse):
    ride_route: str | None = None
