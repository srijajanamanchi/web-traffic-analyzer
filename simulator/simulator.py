#!/usr/bin/env python3
"""
Realistic Website Traffic Simulator
Simulates diverse visitor sessions across the demo site with realistic paths,
varied User Agents, randomized IP headers (X-Forwarded-For), burst spikes,
and intentional anomalies for telemetry dashboard demonstrations.
"""

import argparse
import random
import time
import uuid

import requests

USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Safari iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # Firefox Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    # Chrome Android
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.64 Mobile Safari/537.36",
    # Search Engine Bot
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
]

REFERRERS = [
    "https://www.google.com/search?q=cloudscale+devops",
    "https://news.ycombinator.com/",
    "https://github.com/trending",
    "https://twitter.com/devops_tools",
    "https://linkedin.com/feed",
    "https://reddit.com/r/devops",
    "",  # Direct traffic
    "",
]

SCREEN_RESOLUTIONS = [
    "1920x1080",
    "2560x1440",
    "1440x900",
    "390x844",
    "412x915",
    "1366x768",
]

PAGES = [
    "/index.html",
    "/products.html",
    "/contact.html",
    "/slow.html",
    "/old-page",  # Deliberate 404
]


def generate_random_ip() -> str:
    """Generate realistic public IPv4 address."""
    return f"{random.randint(11, 190)}.{random.randint(20, 240)}.{random.randint(1, 250)}.{random.randint(1, 250)}"


def simulate_visitor_journey(
    demo_url: str,
    collector_url: str,
    ip: str = None,
    user_agent: str = None,
    force_path: str = None,
    burst: bool = False,
):
    """
    Simulates a single visitor performing a browsing journey.
    Sends requests to the demo site HTTP server AND telemetry to /api/collect.
    """
    session_id = f"sim_{uuid.uuid4().hex[:10]}"
    ip = ip or generate_random_ip()
    user_agent = user_agent or random.choice(USER_AGENTS)
    referrer = random.choice(REFERRERS)
    resolution = random.choice(SCREEN_RESOLUTIONS)

    # Journey step count
    steps = 1 if force_path else random.randint(1, 4)
    current_referrer = referrer

    for i in range(steps):
        if force_path:
            path = force_path
        elif i == 0:
            path = random.choice(["/index.html", "/index.html", "/products.html"])
        else:
            # Chance of 404 hit or slow page
            path = random.choices(PAGES, weights=[40, 30, 15, 8, 7])[0]

        # 1. Hit Demo Site HTTP (Generates Nginx access log)
        status_code = 200
        load_time_ms = round(random.uniform(35.0, 180.0), 2)
        if path == "/old-page":
            status_code = 404
        elif path == "/slow.html":
            load_time_ms = round(random.uniform(850.0, 1250.0), 2)

        headers = {
            "User-Agent": user_agent,
            "X-Forwarded-For": ip,
            "X-Real-IP": ip,
            "Referer": current_referrer,
        }

        try:
            demo_target = f"{demo_url.rstrip('/')}{path}"
            resp = requests.get(demo_target, headers=headers, timeout=5)
            status_code = resp.status_code
        except Exception:
            # Demo site might not be listening yet in unit test mode
            pass

        # 2. Ingest via Telemetry Collector /api/collect (simulates tracker.js)
        try:
            telemetry_payload = {
                "site_id": "demo-site",
                "session_id": session_id,
                "event_type": "pageview",
                "path": path,
                "referrer": current_referrer,
                "user_agent": user_agent,
                "screen_resolution": resolution,
                "load_time_ms": load_time_ms,
                "duration_ms": 0.0,
                "status_code": status_code,
            }
            collector_headers = {
                "User-Agent": user_agent,
                "X-Forwarded-For": ip,
                "Content-Type": "application/json",
            }
            requests.post(collector_url, json=telemetry_payload, headers=collector_headers, timeout=4)
        except Exception:
            pass

        current_referrer = f"{demo_url.rstrip('/')}{path}"
        if not burst:
            time.sleep(random.uniform(0.1, 0.6))


def run_traffic_spike(demo_url: str, collector_url: str, count: int = 50):
    """Generates rapid burst of traffic to trigger z-score traffic spike anomaly."""
    print(f"\n⚡ [TRAFFIC SPIKE] Triggering rapid burst of {count} requests...")
    for _ in range(count):
        simulate_visitor_journey(demo_url, collector_url, burst=True)
    print("✓ Traffic spike generated.\n")


def run_error_surge(demo_url: str, collector_url: str, count: int = 25):
    """Generates consecutive 404 errors to trigger error surge anomaly."""
    print(f"\n🚨 [ERROR SURGE] Inundating site with {count} 404 broken-link requests...")
    for _ in range(count):
        simulate_visitor_journey(demo_url, collector_url, force_path="/old-page", burst=True)
        time.sleep(0.05)
    print("✓ Error surge triggered.\n")


def run_suspicious_ip(demo_url: str, collector_url: str, count: int = 15):
    """Simulates malicious automated vulnerability scanner from single IP."""
    attacker_ip = "198.51.100.88"
    attacker_ua = "sqlmap/1.6#stable (https://sqlmap.org)"
    print(f"\n🛡️ [SECURITY ANOMALY] Simulating suspicious vulnerability scanning from {attacker_ip}...")
    for _ in range(count):
        simulate_visitor_journey(
            demo_url,
            collector_url,
            ip=attacker_ip,
            user_agent=attacker_ua,
            force_path="/old-page",
            burst=True,
        )
        time.sleep(0.08)
    print(f"✓ Suspicious IP anomaly created for {attacker_ip}.\n")


def main():
    parser = argparse.ArgumentParser(description="Real-Time Traffic Simulator")
    parser.add_argument("--demo-url", default="http://localhost:8080", help="Demo website base URL")
    parser.add_argument("--collector-url", default="http://localhost:8000/api/collect", help="Collector API URL")
    parser.add_argument("--mode", choices=["continuous", "spike", "errors", "scanner", "demo"], default="continuous")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds (0 for infinite)")
    parser.add_argument("--rate", type=float, default=2.0, help="Visits per second in continuous mode")
    args = parser.parse_args()

    print("==================================================")
    print(" Web Traffic Simulator Initiated")
    print(f" Target Site:      {args.demo_url}")
    print(f" Collector API:    {args.collector_url}")
    print(f" Mode:             {args.mode.upper()}")
    print("==================================================")

    if args.mode == "spike":
        run_traffic_spike(args.demo_url, args.collector_url)
        return
    elif args.mode == "errors":
        run_error_surge(args.demo_url, args.collector_url)
        return
    elif args.mode == "scanner":
        run_suspicious_ip(args.demo_url, args.collector_url)
        return
    elif args.mode == "demo":
        # Interactive demo script: normal traffic -> spike -> error surge -> suspicious IP
        print("\n🎬 Running end-to-end Demonstration Traffic Sequence...")
        print("Stage 1/4: Generating steady baseline traffic (15 visitors)...")
        for _ in range(15):
            simulate_visitor_journey(args.demo_url, args.collector_url)
            time.sleep(0.2)

        time.sleep(1)
        run_traffic_spike(args.demo_url, args.collector_url, count=40)

        time.sleep(1)
        run_error_surge(args.demo_url, args.collector_url, count=15)

        time.sleep(1)
        run_suspicious_ip(args.demo_url, args.collector_url, count=12)

        print("Stage 4/4: Resuming steady traffic...")
        for _ in range(10):
            simulate_visitor_journey(args.demo_url, args.collector_url)
            time.sleep(0.3)

        print("\n✨ Demonstration traffic sequence completed successfully!")
        return

    # Continuous mode
    start_time = time.time()
    counter = 0
    try:
        while True:
            simulate_visitor_journey(args.demo_url, args.collector_url)
            counter += 1
            if counter % 10 == 0:
                print(f"[{time.strftime('%X')}] Generated {counter} user journeys...")

            time.sleep(max(0.05, 1.0 / args.rate))

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                print(f"Completed {counter} simulated visits over {args.duration}s.")
                break
    except KeyboardInterrupt:
        print(f"\nSimulator stopped by user. Total visits simulated: {counter}")


if __name__ == "__main__":
    main()
