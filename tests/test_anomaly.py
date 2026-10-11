from backend.app.anomaly import (
    calculate_z_score,
    detect_traffic_spike,
    detect_error_surge,
    detect_suspicious_ips,
)


def test_calculate_z_score_basic():
    history = [10.0, 10.0, 10.0, 10.0, 10.0]
    res = calculate_z_score(10.0, history)
    assert res["mean"] == 10.0
    assert res["std_dev"] == 0.0
    assert res["z_score"] == 0.0


def test_calculate_z_score_spike():
    history = [10.0, 12.0, 9.0, 11.0, 10.0]
    res = calculate_z_score(50.0, history)
    assert res["mean"] == 10.4
    assert res["z_score"] > 3.0


def test_detect_traffic_spike_insufficient_data():
    # Less than 3 points
    assert detect_traffic_spike(20, [10, 10]) is None
    # Less than min volume floor
    assert detect_traffic_spike(5, [1, 1, 1, 1]) is None


def test_detect_traffic_spike_trigger():
    history = [10, 12, 11, 10, 13, 9, 10]
    # Current volume 65 vs mean ~10.7
    alert = detect_traffic_spike(65, history, threshold=2.5)
    assert alert is not None
    assert alert["anomaly_type"] == "traffic_spike"
    assert alert["severity"] in ("warning", "critical")
    assert alert["metric_value"] == 65.0
    assert alert["z_score"] >= 2.5


def test_detect_error_surge():
    # Status codes with only 200s
    normal_codes = [200] * 20
    assert detect_error_surge(normal_codes, error_rate_threshold=0.15) is None

    # Status codes with 50% 404/500 errors
    failing_codes = [200] * 10 + [404] * 8 + [500] * 2
    alert = detect_error_surge(failing_codes, error_rate_threshold=0.15)
    assert alert is not None
    assert alert["anomaly_type"] == "error_surge"
    assert alert["metric_value"] == 50.0  # 50%


def test_detect_suspicious_ips():
    events = [
        # Normal user
        {"ip": "203.0.113.10", "status_code": 200},
        {"ip": "203.0.113.10", "status_code": 200},
        # Scanner IP generating repeated 404s
        {"ip": "198.51.100.99", "status_code": 404},
        {"ip": "198.51.100.99", "status_code": 404},
        {"ip": "198.51.100.99", "status_code": 401},
        {"ip": "198.51.100.99", "status_code": 403},
        {"ip": "198.51.100.99", "status_code": 404},
    ]

    alerts = detect_suspicious_ips(events, error_threshold=5, rate_threshold=20)
    assert len(alerts) == 1
    assert alerts[0]["anomaly_type"] == "suspicious_ip"
    assert alerts[0]["ip"] == "198.51.100.99"
