from fastapi.testclient import TestClient
from src.gateway.main import app

client = TestClient(app)


def test_missing_api_key_returns_422():
    response = client.post(
        "/v1/chat",
        json={
            "model": "gpt-40-mini",
            "messages": [{"role": "user", "content": "ping"}],
        },
    )

    assert response.status_code == 422


def test_invalid_api_key_returns_401():
    response = client.post(
        "/v1/chat",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "ping"}],
        },
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 401


def test_valid_api_key_is_accepted():
    # This one will hit Redis for rate limiting — we'll mock that in a moment
    # For now just check it doesn't 401
    response = client.post(
        "/v1/chat",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "ping"}],
        },
        headers={"x-api-key": "gw-alpha-dev-key-1234"},
    )
    assert response.status_code != 401
