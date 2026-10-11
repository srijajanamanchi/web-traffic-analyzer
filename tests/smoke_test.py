#!/usr/bin/env python3
"""
Post-Deploy Smoke Test
Tests the complete pipeline end-to-end:
1. Load demo site home page
2. Verify tracking event appears in the analyzer API
3. Confirm /health returns healthy
"""

import sys
import time
import uuid

import requests


def run_smoke_test(
    api_url: str = "http://localhost:8000",
    demo_url: str = "http://localhost:8080",
) -> bool:
    print("=" * 60)
    print("  Post-Deploy Smoke Test")
    print(f"  API:       {api_url}")
    print(f"  Demo Site: {demo_url}")
    print("=" * 60)

    # 1. Health check
    print("\n[1/4] Verifying API health endpoint...")
    try:
        resp = requests.get(f"{api_url}/health", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        health = resp.json()
        assert health["status"] == "healthy", f"Unhealthy status: {health}"
        assert health["database"] == "connected", "Database not connected"
        print(f"      ✓ /health OK: {health['status']} (env: {health.get('environment', 'unknown')})")
    except Exception as e:
        print(f"      ✗ FAIL: {e}")
        return False

    # 2. Demo site home page
    print("\n[2/4] Loading demo site home page...")
    try:
        resp = requests.get(f"{demo_url}/index.html", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert "CloudScale" in resp.text or "tracker.js" in resp.text, "Missing expected content"
        print(f"      ✓ Demo site home page loaded OK (status {resp.status_code})")
    except Exception as e:
        print(f"      ✗ FAIL: {e}")
        return False

    # 3. Send a pageview tracking event
    session_id = f"smoke_test_{uuid.uuid4().hex[:8]}"
    print(f"\n[3/4] Sending telemetry pageview event (session: {session_id})...")
    try:
        payload = {
            "site_id": "demo-site",
            "session_id": session_id,
            "event_type": "pageview",
            "path": "/smoke-test",
            "referrer": "",
            "user_agent": "SmokeTestBot/1.0",
            "screen_resolution": "1920x1080",
            "load_time_ms": 55.0,
            "duration_ms": 0.0,
            "status_code": 200,
        }
        resp = requests.post(
            f"{api_url}/api/collect",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "ok", f"Unexpected response: {data}"
        print(f"      ✓ Event collected successfully (event_id: {data.get('event_id')})")
    except Exception as e:
        print(f"      ✗ FAIL: {e}")
        return False

    # 4. Verify event appears in the API
    print("\n[4/4] Verifying event is visible in /api/events...")
    time.sleep(0.5)  # Brief pause for DB write
    try:
        resp = requests.get(f"{api_url}/api/events?limit=20", timeout=10)
        assert resp.status_code == 200
        events = resp.json()
        matching = [e for e in events if e.get("session_id") == session_id]
        assert len(matching) >= 1, (
            f"No event found for session {session_id} in recent events (got {len(events)} total)"
        )
        found = matching[0]
        print(f"      ✓ Event verified in API: path={found['path']} device={found['device']}")
    except Exception as e:
        print(f"      ✗ FAIL: {e}")
        return False

    print("\n" + "=" * 60)
    print("  ✨ All smoke tests passed! Pipeline is healthy.")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Post-Deploy Smoke Test")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--demo-url", default="http://localhost:8080")
    args = parser.parse_args()

    ok = run_smoke_test(args.api_url, args.demo_url)
    sys.exit(0 if ok else 1)
