from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    body: str | None
    ride_id: UUID | None
    read_at: datetime | None
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)
