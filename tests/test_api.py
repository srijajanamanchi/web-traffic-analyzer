import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_prometheus_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "traffic_analyzer_requests_total" in response.text


def test_collect_telemetry_valid_json():
    payload = {
        "site_id": "demo-site",
        "session_id": "test_sess_123",
        "event_type": "pageview",
        "path": "/products.html",
        "referrer": "https://google.com",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "screen_resolution": "1920x1080",
        "load_time_ms": 115.5,
        "duration_ms": 0.0,
        "status_code": 200,
    }
    response = client.post("/api/collect", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ok"
    assert "event_id" in data


def test_collect_telemetry_beacon_text():
    # navigator.sendBeacon sends stringified json with text/plain
    payload = {
        "site_id": "demo-site",
        "session_id": "test_sess_456",
        "event_type": "unload",
        "path": "/index.html",
        "referrer": "",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15",
        "screen_resolution": "1440x900",
        "load_time_ms": 0.0,
        "duration_ms": 5200.0,
        "status_code": 200,
    }
    response = client.post(
        "/api/collect",
        content=json.dumps(payload),
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "ok"


def test_get_stats_endpoint():
    response = client.get("/api/stats?time_range=1h")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "unique_visitors" in data
    assert "active_users_now" in data
    assert "error_rate" in data
    assert "latency" in data
    assert "status_codes" in data
    assert "top_pages" in data
    assert "breakdown" in data


def test_get_recent_events_endpoint():
    response = client.get("/api/events?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_anomalies_endpoint():
    response = client.get("/api/anomalies?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_ingest_raw_nginx_logs():
    lines = [
        '10.10.10.10 - - [11/Oct/2026:18:50:00 +0000] "GET /contact.html HTTP/1.1" 200 1200 "-" "curl/8.0.0"',
        '10.10.10.11 - - [11/Oct/2026:18:50:02 +0000] "GET /old-page HTTP/1.1" 404 450 "-" "curl/8.0.0"',
    ]
    response = client.post("/api/logs/ingest", json={"lines": lines})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["ingested_count"] == 2
