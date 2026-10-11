"""
Locust Load Test — Real-Time Web Traffic Analyzer
Usage:
  locust -f tests/load_test.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 60s --headless
"""

import random
import uuid

from locust import HttpUser, between, task


class TrackerUser(HttpUser):
    """Simulates a web visitor sending telemetry events to the API."""

    wait_time = between(0.3, 1.2)

    pages = [
        "/index.html",
        "/products.html",
        "/contact.html",
        "/slow.html",
        "/old-page",
    ]

    def on_start(self):
        self.session_id = f"load_{uuid.uuid4().hex[:8]}"

    @task(5)
    def collect_pageview(self):
        path = random.choice(self.pages)
        status = 404 if path == "/old-page" else 200
        payload = {
            "site_id": "demo-site",
            "session_id": self.session_id,
            "event_type": "pageview",
            "path": path,
            "referrer": random.choice(["", "https://google.com", "https://github.com"]),
            "user_agent": "LocustLoadTest/1.0",
            "screen_resolution": "1920x1080",
            "load_time_ms": round(random.uniform(40, 900), 1),
            "duration_ms": 0.0,
            "status_code": status,
        }
        with self.client.post(
            "/api/collect",
            json=payload,
            catch_response=True,
            name="/api/collect [pageview]",
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(2)
    def get_stats(self):
        time_range = random.choice(["5m", "15m", "1h"])
        self.client.get(
            f"/api/stats?time_range={time_range}",
            name="/api/stats",
        )

    @task(1)
    def get_events(self):
        self.client.get("/api/events?limit=25", name="/api/events")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")
