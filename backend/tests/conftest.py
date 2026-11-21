import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.exc import OperationalError

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://cinema:cinema@localhost:5432/cinema_test"
)
if not make_url(TEST_DATABASE_URL).database.endswith("_test"):
    raise RuntimeError(f"Refusing to run tests against non-test database: {TEST_DATABASE_URL}")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402
from tests.helpers import PASSWORD, bearer, login, register  # noqa: E402

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def _ensure_database_exists() -> None:
    url = make_url(TEST_DATABASE_URL)
    server = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5}
    )
    try:
        with server.connect() as conn:
            exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database})
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    except OperationalError as exc:
        pytest.exit(f"PostgreSQL is not reachable ({url.host}:{url.port}). Run `docker compose up -d db`.\n{exc}")
    finally:
        server.dispose()


@pytest.fixture(scope="session", autouse=True)
def _database() -> Iterator[None]:
    _ensure_database_exists()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    yield
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded() -> None:
    with SessionLocal() as session, session.begin():
        seed(session)


@pytest.fixture
def user_headers(client: TestClient) -> dict[str, str]:
    register(client, "user@example.com")
    return bearer(login(client, "user@example.com", PASSWORD).json()["access_token"])


@pytest.fixture
def admin_headers(client: TestClient, seeded: None) -> dict[str, str]:
    return bearer(login(client, settings.admin_email, settings.admin_password).json()["access_token"])
