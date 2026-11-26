from collections.abc import Collection, Mapping
from typing import Any

from pydantic import ValidationError

from app.core.errors import AppError, UnprocessableError
from app.patterns.recommendation import (
    DEFAULT_RECOMMENDATION_CONFIG,
    HybridStrategy,
    RecommendationConfig,
    UnknownStrategyError,
)
from app.schemas.settings import AppSettingsRead, AppSettingsUpdate
from app.services.ports import SettingsStore

DEFAULT_REPORT_TIMEZONE = "Europe/Kyiv"


def default_settings() -> AppSettingsUpdate:
    config = DEFAULT_RECOMMENDATION_CONFIG
    return AppSettingsUpdate(
        recommendation_default_strategy=config.default_strategy,
        hybrid_weights=dict(config.hybrid_weights),
        popularity_window_days=config.popularity_window_days,
        report_timezone=DEFAULT_REPORT_TIMEZONE,
    )


class SettingsService:
    def __init__(self, store: SettingsStore, strategies: Collection[str]) -> None:
        self.store = store
        self.strategies = tuple(strategies)

    def get(self) -> AppSettingsRead:
        stored = self.store.get_all()
        values = default_settings().model_dump()
        for key in list(values):
            if key in stored:
                candidate = {**values, key: stored[key].value}
                if self._is_valid(candidate):
                    values = candidate
        updated_at = max((s.updated_at for key, s in stored.items() if key in values), default=None)
        return AppSettingsRead(**values, available_strategies=list(self.strategies), updated_at=updated_at)

    def update(self, data: AppSettingsUpdate) -> AppSettingsRead:
        self._check_strategies(data)
        if not self.store.timezone_exists(data.report_timezone):
            raise UnprocessableError(f"Unknown IANA time zone '{data.report_timezone}'", code="unknown_timezone")
        self.store.upsert_many(data.model_dump())
        return self.get()

    def recommendation_config(self) -> RecommendationConfig:
        settings = self.get()
        return RecommendationConfig(
            default_strategy=settings.recommendation_default_strategy,
            hybrid_weights=settings.hybrid_weights,
            popularity_window_days=settings.popularity_window_days,
        )

    def report_timezone(self) -> str:
        return self.get().report_timezone

    def _is_valid(self, values: Mapping[str, Any]) -> bool:
        try:
            self._check_strategies(AppSettingsUpdate.model_validate(values))
        except (ValidationError, AppError):
            return False
        return True

    def _check_strategies(self, data: AppSettingsUpdate) -> None:
        if data.recommendation_default_strategy not in self.strategies:
            raise UnknownStrategyError(
                f"Unknown recommendation strategy '{data.recommendation_default_strategy}'; "
                f"expected one of: {', '.join(self.strategies)}"
            )
        unsupported = sorted(
            code for code in data.hybrid_weights if code not in self.strategies or code == HybridStrategy.code
        )
        if unsupported:
            raise UnknownStrategyError(f"Hybrid weights reference unsupported strategies: {', '.join(unsupported)}")
