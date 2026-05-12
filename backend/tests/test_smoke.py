"""Smoke tests for the travel-agent backend.

Runs without a real OPENAI_API_KEY: nothing here hits /api/chat (the only route
that calls OpenAI). The orchestrator's lifespan still constructs an OpenAI
client, which needs *some* key string, so we set a dummy value.
"""

import os

from fastapi.testclient import TestClient


def _client() -> TestClient:
    os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-real")
    os.environ.setdefault("BACKEND_BASE_URL", "http://testserver")
    from backend.app import app
    return TestClient(app)


def test_knowledge_base_has_expected_cities():
    from backend.knowledge_base import get_place, list_place_keys

    keys = list_place_keys()
    assert "tokyo" in keys
    assert "bali" in keys
    assert get_place("Tokyo")["country"] == "Japan"


def test_forecast_is_deterministic_for_same_date():
    from backend.knowledge_base import get_forecast

    a = get_forecast("Bali", "2026-07-10")
    b = get_forecast("Bali", "2026-07-10")
    assert a == b
    assert "temp_high_c" in a


def test_forecast_returns_none_for_unknown_city():
    from backend.knowledge_base import get_forecast

    assert get_forecast("Atlantis", "2026-07-10") is None


def test_health_endpoint():
    with _client() as c:
        r = c.get("/api/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_weather_agent_card_is_discoverable():
    with _client() as c:
        r = c.get("/agents/weather/.well-known/agent.json")
        assert r.status_code == 200
        card = r.json()
        assert card["name"] == "WeatherAgent"
        assert any(s["id"] == "get_forecast" for s in card["skills"])


def test_weather_agent_returns_forecast_via_a2a():
    with _client() as c:
        r = c.post(
            "/agents/weather/a2a/task",
            json={
                "id": "t1",
                "skill_id": "get_forecast",
                "inputs": {"city": "Tokyo", "travel_date": "2026-04-12"},
                "requester": "test",
            },
        )
        assert r.status_code == 200
        out = r.json()
        assert out["status"] == "completed"
        assert out["output"]["city"] == "Tokyo"


def test_weather_agent_rejects_unknown_skill():
    with _client() as c:
        r = c.post(
            "/agents/weather/a2a/task",
            json={"id": "t2", "skill_id": "nope", "inputs": {}, "requester": "test"},
        )
        assert r.status_code == 400


def test_booking_agent_creates_booking_via_a2a():
    with _client() as c:
        r = c.post(
            "/agents/booking/a2a/task",
            json={
                "id": "b1",
                "skill_id": "create_booking",
                "inputs": {
                    "city": "Bali",
                    "travel_date": "2026-07-10",
                    "traveler_name": "Test Traveller",
                    "num_travelers": 2,
                    "nights": 3,
                },
                "requester": "test",
            },
        )
        assert r.status_code == 200
        out = r.json()
        assert out["status"] == "completed"
        assert out["output"]["confirmation_code"].startswith("TRV-")
        assert out["output"]["total_price_usd"] > 0


def test_booking_agent_rejects_missing_fields():
    with _client() as c:
        r = c.post(
            "/agents/booking/a2a/task",
            json={
                "id": "b2",
                "skill_id": "create_booking",
                "inputs": {"city": "Bali"},
                "requester": "test",
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "failed"
