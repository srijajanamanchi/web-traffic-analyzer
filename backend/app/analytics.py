from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import TrafficEvent


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    """
    Calculate average, p50 (median), p95, and p99 percentiles from a list of numeric latencies.
    """
    if not values:
        return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    avg = sum(sorted_vals) / n

    def get_percentile(p: float) -> float:
        k = (n - 1) * p
        f = int(k)
        c = f + 1
        if c < n:
            d0 = sorted_vals[f] * (c - k)
            d1 = sorted_vals[c] * (k - f)
            return d0 + d1
        return sorted_vals[f]

    return {
        "avg": round(avg, 2),
        "p50": round(get_percentile(0.50), 2),
        "p95": round(get_percentile(0.95), 2),
        "p99": round(get_percentile(0.99), 2),
    }


def get_traffic_analytics(
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    path_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Comprehensive traffic analytics computation over a time range.
    """
    now = datetime.now(timezone.utc)
    if not end_time:
        end_time = now
    if not start_time:
        start_time = now - timedelta(hours=1)

    query = db.query(TrafficEvent).filter(
        TrafficEvent.created_at >= start_time,
        TrafficEvent.created_at <= end_time,
    )
    if path_filter:
        query = query.filter(TrafficEvent.path == path_filter)

    events: List[TrafficEvent] = query.order_by(TrafficEvent.created_at.asc()).all()

    total_requests = len(events)
    if total_requests == 0:
        return {
            "total_requests": 0,
            "unique_visitors": 0,
            "active_users_now": 0,
            "error_rate": 0.0,
            "latency": {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0},
            "status_codes": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "breakdown": {}},
            "top_pages": [],
            "top_referrers": [],
            "breakdown": {"device": {}, "browser": {}, "os": {}},
            "time_series": [],
        }

    # 1. Unique visitors & Active users in last 5 minutes
    unique_sessions = set()
    active_sessions = set()
    cutoff_active = now - timedelta(minutes=5)

    status_2xx = 0
    status_3xx = 0
    status_4xx = 0
    status_5xx = 0
    status_breakdown: Dict[int, int] = {}

    latencies: List[float] = []
    page_hits: Dict[str, Dict[str, Any]] = {}
    referrer_hits: Dict[str, int] = {}
    device_counts: Dict[str, int] = {}
    browser_counts: Dict[str, int] = {}
    os_counts: Dict[str, int] = {}

    # Time series buckets by minute (YYYY-MM-DD HH:MM)
    time_series_map: Dict[str, Dict[str, Any]] = {}

    for ev in events:
        ev_dt = ev.created_at
        if ev_dt is not None and ev_dt.tzinfo is None:
            ev_dt = ev_dt.replace(tzinfo=timezone.utc)

        unique_sessions.add(ev.session_id)
        if ev_dt and ev_dt >= cutoff_active:
            active_sessions.add(ev.session_id)

        # Status code counting
        code = ev.status_code
        status_breakdown[code] = status_breakdown.get(code, 0) + 1
        if 200 <= code < 300:
            status_2xx += 1
        elif 300 <= code < 400:
            status_3xx += 1
        elif 400 <= code < 500:
            status_4xx += 1
        elif 500 <= code < 600:
            status_5xx += 1

        # Latency collection
        if ev.response_time_ms > 0:
            latencies.append(ev.response_time_ms)

        # Top Pages
        path = ev.path or "/"
        if path not in page_hits:
            page_hits[path] = {"hits": 0, "errors": 0, "latencies": []}
        page_hits[path]["hits"] += 1
        if code >= 400:
            page_hits[path]["errors"] += 1
        if ev.response_time_ms > 0:
            page_hits[path]["latencies"].append(ev.response_time_ms)

        # Referrers
        ref = ev.referrer.strip() if ev.referrer else "Direct"
        referrer_hits[ref] = referrer_hits.get(ref, 0) + 1

        # Breakdowns
        device = ev.device or "Desktop"
        browser = ev.browser or "Other"
        os_name = ev.os or "Other"
        device_counts[device] = device_counts.get(device, 0) + 1
        browser_counts[browser] = browser_counts.get(browser, 0) + 1
        os_counts[os_name] = os_counts.get(os_name, 0) + 1

        # Time-series bucket
        bucket_key = (ev_dt or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M")
        if bucket_key not in time_series_map:
            time_series_map[bucket_key] = {
                "timestamp": bucket_key,
                "requests": 0,
                "errors": 0,
                "latencies": [],
                "sessions": set(),
            }
        time_series_map[bucket_key]["requests"] += 1
        if code >= 400:
            time_series_map[bucket_key]["errors"] += 1
        if ev.response_time_ms > 0:
            time_series_map[bucket_key]["latencies"].append(ev.response_time_ms)
        time_series_map[bucket_key]["sessions"].add(ev.session_id)

    # Calculate error rate
    error_count = status_4xx + status_5xx
    error_rate = round((error_count / total_requests) * 100, 2)

    # Format Top Pages
    top_pages = []
    for path, data in sorted(page_hits.items(), key=lambda item: item[1]["hits"], reverse=True)[:10]:
        avg_lat = sum(data["latencies"]) / len(data["latencies"]) if data["latencies"] else 0.0
        top_pages.append({
            "path": path,
            "hits": data["hits"],
            "errors": data["errors"],
            "avg_latency": round(avg_lat, 2),
            "percentage": round((data["hits"] / total_requests) * 100, 1),
        })

    # Format Top Referrers
    top_referrers = [
        {"referrer": ref, "hits": hits, "percentage": round((hits / total_requests) * 100, 1)}
        for ref, hits in sorted(referrer_hits.items(), key=lambda item: item[1], reverse=True)[:8]
    ]

    # Format Time Series
    formatted_time_series = []
    for key in sorted(time_series_map.keys()):
        item = time_series_map[key]
        item_lats = item["latencies"]
        avg_l = sum(item_lats) / len(item_lats) if item_lats else 0.0
        formatted_time_series.append({
            "timestamp": key,
            "requests": item["requests"],
            "errors": item["errors"],
            "avg_latency": round(avg_l, 2),
            "active_users": len(item["sessions"]),
        })

    return {
        "total_requests": total_requests,
        "unique_visitors": len(unique_sessions),
        "active_users_now": len(active_sessions),
        "error_rate": error_rate,
        "latency": calculate_percentiles(latencies),
        "status_codes": {
            "2xx": status_2xx,
            "3xx": status_3xx,
            "4xx": status_4xx,
            "5xx": status_5xx,
            "breakdown": status_breakdown,
        },
        "top_pages": top_pages,
        "top_referrers": top_referrers,
        "breakdown": {
            "device": device_counts,
            "browser": browser_counts,
            "os": os_counts,
        },
        "time_series": formatted_time_series,
    }
