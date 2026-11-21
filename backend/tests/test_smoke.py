from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

import app.models  # noqa: F401
from app.core.db import Base
from app.main import app


def test_health():
    r = TestClient(app).get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_schema_creates():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())
    assert {
        "users", "profiles", "titles", "genres", "title_genres", "seasons", "episodes",
        "video_assets", "plans", "subscriptions", "payments", "favorites", "watch_history",
    } <= tables
