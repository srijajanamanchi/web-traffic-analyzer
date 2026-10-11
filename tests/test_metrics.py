from backend.app.analytics import calculate_percentiles


def test_calculate_percentiles_empty():
    res = calculate_percentiles([])
    assert res == {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}


def test_calculate_percentiles_single_element():
    res = calculate_percentiles([100.0])
    assert res["avg"] == 100.0
    assert res["p50"] == 100.0
    assert res["p95"] == 100.0
    assert res["p99"] == 100.0


def test_calculate_percentiles_distribution():
    # 100 sample latencies from 1ms to 100ms
    latencies = [float(i) for i in range(1, 101)]
    res = calculate_percentiles(latencies)
    assert res["avg"] == 50.5
    assert 49.0 <= res["p50"] <= 51.5
    assert 94.0 <= res["p95"] <= 96.0
    assert 98.0 <= res["p99"] <= 100.0
