from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.services.reports import GroupBy

type ReportCell = int | float | date | str | None


class ReportFormat(StrEnum):
    JSON = "json"
    CSV = "csv"


class ReportColumnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str


class ReportSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    title: str
    columns: list[ReportColumnRead]
    rows: list[dict[str, ReportCell]]


class SummaryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    value: ReportCell


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: str
    title: str
    date_from: date
    date_to: date
    group_by: GroupBy
    timezone: str
    summary: list[SummaryItemRead]
    sections: list[ReportSectionRead]


class DashboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_users: int
    active_users_7d: int
    active_premium: int
    revenue_30d: float
    titles_with_video: int
