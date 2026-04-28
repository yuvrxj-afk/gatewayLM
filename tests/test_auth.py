from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.gateway.models.schemas import ChatResponse, UsageStats


def test_missing_api_key_returns_422():
    from src.gateway.main import app

    client = TestClient(app)
    response = client.post(
        "/v1/chat",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "ping"}],
        },
    )

    assert response.status_code == 422


def test_invalid_api_key_returns_401():
    from src.gateway.main import app

    client = TestClient(app)
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
    # Mock the provider routing so tests never call real providers.
    from src.gateway.main import app
    import src.gateway.routers.chat as chat_router

    chat_router.route = AsyncMock(
        return_value=ChatResponse(
            id="test",
            model_requested="gpt-4o-mini",
            model_served="gpt-4o-mini",
            provider="mock",
            content="ok",
            usage=UsageStats(input_tokens=1, output_tokens=1),
            latency_ms=1,
        )
    )

    client = TestClient(app)
    response = client.post(
        "/v1/chat",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "ping"}],
        },
        headers={"x-api-key": "gw-alpha-dev-key-1234"},
    )
    assert response.status_code == 200
