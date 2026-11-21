from typing import Any

from fastapi.testclient import TestClient
from httpx import Response

PASSWORD = "password123"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client: TestClient, email: str, password: str = PASSWORD, **extra: Any) -> Response:
    return client.post("/api/auth/register", json={"email": email, "password": password, **extra})


def login(client: TestClient, email: str, password: str = PASSWORD) -> Response:
    return client.post("/api/auth/login", json={"email": email, "password": password})


def assert_error(response: Response, status_code: int, code: str) -> None:
    assert response.status_code == status_code, response.text
    assert response.json()["error"]["code"] == code
