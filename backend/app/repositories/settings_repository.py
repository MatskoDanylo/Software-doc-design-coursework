from collections.abc import Mapping
from typing import Any

from sqlalchemy import column, exists, func, select, table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import AppSetting
from app.services.ports import StoredSetting

pg_timezone_names = table("pg_timezone_names", column("name"))


class SettingsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self) -> dict[str, StoredSetting]:
        rows = self.session.execute(select(AppSetting.key, AppSetting.value, AppSetting.updated_at))
        return {key: StoredSetting(value, updated_at) for key, value, updated_at in rows}

    def upsert_many(self, values: Mapping[str, Any]) -> None:
        if not values:
            return
        statement = insert(AppSetting).values([{"key": key, "value": value} for key, value in values.items()])
        self.session.execute(statement.on_conflict_do_update(
            index_elements=[AppSetting.key],
            set_={"value": statement.excluded.value, "updated_at": func.now()},
        ))

    def timezone_exists(self, name: str) -> bool:
        return bool(self.session.scalar(select(exists().where(pg_timezone_names.c.name == name))))
