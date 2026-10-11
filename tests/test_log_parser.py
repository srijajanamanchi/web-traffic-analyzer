import pytest

from backend.app.parser import parse_nginx_log_line, parse_user_agent


def test_parse_valid_nginx_combined_log():
    sample_line = (
        '192.168.1.50 - - [11/Oct/2026:18:50:00 +0000] "GET /products.html HTTP/1.1" '
        '200 4520 "https://www.google.com/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"'
    )
    result = parse_nginx_log_line(sample_line)
    assert result is not None
    assert result["ip"] == "192.168.1.50"
    assert result["method"] == "GET"
    assert result["path"] == "/products.html"
    assert result["status_code"] == 200
    assert result["bytes_sent"] == 4520
    assert result["referrer"] == "https://www.google.com/"
    assert result["browser"] == "Chrome"
    assert result["os"] == "Windows"
    assert result["device"] == "Desktop"


def test_parse_nginx_log_with_dash_values():
    sample_line = '10.0.0.1 - - [11/Oct/2026:18:52:10 +0000] "GET /old-page HTTP/1.1" 404 - "-" "-"'
    result = parse_nginx_log_line(sample_line)
    assert result is not None
    assert result["ip"] == "10.0.0.1"
    assert result["status_code"] == 404
    assert result["bytes_sent"] == 0
    assert result["referrer"] == ""
    assert result["user_agent"] == ""


def test_parse_invalid_nginx_log():
    assert parse_nginx_log_line("") is None
    assert parse_nginx_log_line("invalid gibberish log line") is None


@pytest.mark.parametrize(
    "user_agent,expected_browser,expected_os,expected_device",
    [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
            "Chrome",
            "Windows",
            "Desktop",
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
            "Safari",
            "macOS",
            "Desktop",
        ),
        (
            "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Firefox",
            "Linux",
            "Desktop",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
            "Safari",
            "iOS",
            "Mobile",
        ),
        (
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36",
            "Chrome",
            "Android",
            "Mobile",
        ),
        (
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Bot/Crawler",
            "Bot",
            "Bot",
        ),
        (
            "",
            "Unknown",
            "Unknown",
            "Desktop",
        ),
    ],
)
def test_parse_user_agent_varieties(user_agent, expected_browser, expected_os, expected_device):
    parsed = parse_user_agent(user_agent)
    assert parsed["browser"] == expected_browser
    assert parsed["os"] == expected_os
    assert parsed["device"] == expected_device
