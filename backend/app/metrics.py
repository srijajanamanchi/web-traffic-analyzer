from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Prometheus Metrics Definitions
HTTP_REQUESTS_TOTAL = Counter(
    "traffic_analyzer_requests_total",
    "Total HTTP requests handled by the Traffic Analyzer",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "traffic_analyzer_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

COLLECTED_EVENTS_TOTAL = Counter(
    "traffic_analyzer_collected_events_total",
    "Total tracking events received by collector",
    ["site_id", "event_type"],
)

ACTIVE_USERS_GAUGE = Gauge(
    "traffic_analyzer_active_users",
    "Current active website visitors within the last 5 minutes",
)

ANOMALIES_DETECTED_TOTAL = Counter(
    "traffic_analyzer_anomalies_detected_total",
    "Total anomalies detected by the analyzer engine",
    ["anomaly_type", "severity"],
)


def get_metrics_response() -> tuple[bytes, str]:
    """
    Generate Prometheus metrics output and content type.
    """
    return generate_latest(), CONTENT_TYPE_LATEST
