"""
Integration tests for the Flask app.
These run against a real Redis instance (provided as a service in CI).
"""
import os
import pytest
import redis

# point the app at the test Redis before importing main
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")

from app.main import app   # noqa: E402  (import after env setup)


@pytest.fixture
def client():
    """Flask test client with a clean Redis state for each test."""
    app.config["TESTING"] = True

    # flush the test Redis so each test starts from zero
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    r.flushall()

    with app.test_client() as c:
        yield c


# ── Health endpoint ────────────────────────────────────────────────────────────
def test_health_returns_200(client):
    res = client.get("/health")
    assert res.status_code == 200

def test_health_body(client):
    res = client.get("/health")
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["redis"] == "ok"


# ── Root endpoint ─────────────────────────────────────────────────────────────
def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert "app" in data
    assert "endpoints" in data


# ── Count endpoint ────────────────────────────────────────────────────────────
def test_get_count_starts_at_zero(client):
    res = client.get("/count")
    assert res.status_code == 200
    assert res.get_json()["visits"] == 0

def test_post_increments_count(client):
    client.post("/count")
    client.post("/count")
    res = client.post("/count")
    assert res.get_json()["visits"] == 3

def test_get_count_after_increments(client):
    client.post("/count")
    client.post("/count")
    res = client.get("/count")
    assert res.get_json()["visits"] == 2


# ── Reset endpoint ────────────────────────────────────────────────────────────
def test_reset(client):
    client.post("/count")
    client.post("/count")
    res = client.post("/reset")
    assert res.get_json()["visits"] == 0

def test_count_after_reset(client):
    client.post("/count")
    client.post("/reset")
    res = client.get("/count")
    assert res.get_json()["visits"] == 0
