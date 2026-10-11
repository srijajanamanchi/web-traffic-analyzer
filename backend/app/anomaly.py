import math
from typing import List, Dict, Any, Optional
import httpx
from backend.app.config import settings
from backend.app.logger import logger


def calculate_z_score(value: float, history: List[float]) -> Dict[str, float]:
    """
    Calculate mean, standard deviation, and z-score for a given value relative to historical series.
    Formula: z = (value - mean) / std_dev
    """
    if not history:
        return {"z_score": 0.0, "mean": value, "std_dev": 0.0}

    n = len(history)
    mean = sum(history) / n

    variance = sum((x - mean) ** 2 for x in history) / n
    std_dev = math.sqrt(variance)

    if std_dev == 0.0:
        z_score = 0.0
    else:
        z_score = (value - mean) / std_dev

    return {
        "z_score": round(z_score, 2),
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2),
    }


def detect_traffic_spike(
    current_count: int,
    history_counts: List[int],
    threshold: float = 2.5,
    min_volume: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    Detect sudden spikes in requests per minute using rolling z-score.
    """
    if current_count < min_volume or len(history_counts) < 3:
        return None

    stats = calculate_z_score(float(current_count), [float(x) for x in history_counts])
    z_score = stats["z_score"]

    if z_score >= threshold:
        severity = "critical" if z_score >= 4.0 else "warning"
        return {
            "anomaly_type": "traffic_spike",
            "severity": severity,
            "description": (
                f"Traffic spike detected! Current volume: {current_count} req/min "
                f"(baseline mean: {stats['mean']}, z-score: {z_score})"
            ),
            "metric_value": float(current_count),
            "baseline_value": stats["mean"],
            "z_score": z_score,
            "ip": None,
        }
    return None


def detect_error_surge(
    status_codes: List[int],
    error_rate_threshold: float = 0.15,
    min_requests: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    Detect surge in 4xx/5xx error responses.
    """
    if len(status_codes) < min_requests:
        return None

    error_count = sum(1 for code in status_codes if code >= 400)
    total_count = len(status_codes)
    error_rate = error_count / total_count

    if error_rate >= error_rate_threshold:
        severity = "critical" if error_rate >= 0.35 else "warning"
        return {
            "anomaly_type": "error_surge",
            "severity": severity,
            "description": (
                f"Error surge detected! Error rate is {round(error_rate * 100, 1)}% "
                f"({error_count}/{total_count} requests failed)."
            ),
            "metric_value": round(error_rate * 100, 2),
            "baseline_value": round(error_rate_threshold * 100, 2),
            "z_score": round((error_rate - error_rate_threshold) * 10, 2),
            "ip": None,
        }
    return None


def detect_suspicious_ips(
    events: List[Dict[str, Any]],
    error_threshold: int = 5,
    rate_threshold: int = 40,
) -> List[Dict[str, Any]]:
    """
    Detect suspicious IPs exhibiting scanning behavior (repeated 404/401s) or rate abuse.
    """
    ip_stats: Dict[str, Dict[str, int]] = {}

    for ev in events:
        ip = ev.get("ip") or "unknown"
        if ip in ("127.0.0.1", "localhost", "unknown"):
            continue

        if ip not in ip_stats:
            ip_stats[ip] = {"total": 0, "errors": 0}

        ip_stats[ip]["total"] += 1
        status = ev.get("status_code", 200)
        if status in (401, 403, 404, 429):
            ip_stats[ip]["errors"] += 1

    alerts = []
    for ip, counts in ip_stats.items():
        if counts["errors"] >= error_threshold:
            alerts.append({
                "anomaly_type": "suspicious_ip",
                "severity": "critical" if counts["errors"] >= 10 else "warning",
                "description": (
                    f"Suspicious IP scanner detected: {ip} generated {counts['errors']} "
                    f"auth/missing endpoint errors ({counts['total']} total requests)."
                ),
                "metric_value": float(counts["errors"]),
                "baseline_value": float(error_threshold),
                "z_score": 3.0,
                "ip": ip,
            })
        elif counts["total"] >= rate_threshold:
            alerts.append({
                "anomaly_type": "suspicious_ip",
                "severity": "warning",
                "description": (
                    f"High-frequency IP rate abuser: {ip} sent {counts['total']} requests in window."
                ),
                "metric_value": float(counts["total"]),
                "baseline_value": float(rate_threshold),
                "z_score": 2.5,
                "ip": ip,
            })

    return alerts


async def dispatch_alert_webhook(alert_data: Dict[str, Any]) -> None:
    """
    Send alert notification to Slack/Discord webhook if configured.
    """
    webhook_url = settings.ALERT_WEBHOOK_URL
    if not webhook_url:
        return

    payload = {
        "text": f"🚨 *Traffic Analyzer Alert* [{alert_data.get('severity', 'warning').upper()}]\n"
                f"**Type:** {alert_data.get('anomaly_type')}\n"
                f"**Details:** {alert_data.get('description')}\n"
                f"**Metric:** {alert_data.get('metric_value')} (Threshold: {alert_data.get('baseline_value')})",
    }
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code >= 400:
                logger.warning(f"Webhook alert notification returned status {resp.status_code}")
    except Exception as exc:
        logger.warning(f"Failed to dispatch alert webhook: {exc}")
