from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

MIN_WINDOW_DAYS, MAX_WINDOW_DAYS = 1, 365

Weight = Annotated[float, Field(ge=0, le=1)]


class AppSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    recommendation_default_strategy: str = Field(min_length=1, max_length=50)
    hybrid_weights: dict[str, Weight] = Field(min_length=1, max_length=20)
    popularity_window_days: int = Field(ge=MIN_WINDOW_DAYS, le=MAX_WINDOW_DAYS)
    report_timezone: str = Field(min_length=1, max_length=64)

    @field_validator("hybrid_weights")
    @classmethod
    def _some_weight_is_positive(cls, value: dict[str, float]) -> dict[str, float]:
        if not any(weight > 0 for weight in value.values()):
            raise ValueError("at least one hybrid weight must be greater than 0")
        return value


class AppSettingsRead(AppSettingsUpdate):
    available_strategies: list[str]
    updated_at: datetime | None
