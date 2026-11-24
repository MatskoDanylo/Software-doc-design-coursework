from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_code: str
    expires_at: datetime | None
    cancelled: bool
