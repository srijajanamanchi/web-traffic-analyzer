import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Combined Log Format:
# $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
NGINX_COMBINED_LOG_REGEX = re.compile(
    r'^(?P<ip>\S+)\s+'
    r'\S+\s+'  # remote ident (usually -)
    r'(?P<remote_user>\S+)\s+'  # remote user
    r'\[(?P<time_local>[^\]]+)\]\s+'  # [11/Oct/2026:18:50:00 +0000]
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s*(?P<protocol>[^"]*)"\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<bytes_sent>\S+)\s+'
    r'"(?P<referrer>[^"]*)"\s+'
    r'"(?P<user_agent>[^"]*)"'
)


def parse_nginx_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single line from an Nginx access log in combined format.
    Returns a dictionary of parsed fields or None if parsing fails.
    """
    line = line.strip()
    if not line:
        return None

    match = NGINX_COMBINED_LOG_REGEX.match(line)
    if not match:
        return None

    data = match.groupdict()

    # Parse status code
    try:
        status_code = int(data["status"])
    except ValueError:
        status_code = 200

    # Parse timestamp
    timestamp = datetime.now(timezone.utc)
    raw_time = data.get("time_local", "")
    if raw_time:
        try:
            # Format: 11/Oct/2026:18:50:00 +0000
            # Remove colon between day/month/year and hours for strptime if needed, or parse directly:
            # '%d/%b/%Y:%H:%M:%S %z'
            parsed_dt = datetime.strptime(raw_time, "%d/%b/%Y:%H:%M:%S %z")
            timestamp = parsed_dt.astimezone(timezone.utc)
        except Exception:
            pass

    # Parse bytes
    try:
        bytes_sent = int(data["bytes_sent"]) if data["bytes_sent"] != "-" else 0
    except ValueError:
        bytes_sent = 0

    referrer = data.get("referrer", "")
    if referrer == "-":
        referrer = ""

    user_agent = data.get("user_agent", "")
    if user_agent == "-":
        user_agent = ""

    ua_info = parse_user_agent(user_agent)

    return {
        "ip": data["ip"],
        "method": data["method"],
        "path": data["path"],
        "status_code": status_code,
        "bytes_sent": bytes_sent,
        "referrer": referrer,
        "user_agent": user_agent,
        "timestamp": timestamp,
        "browser": ua_info["browser"],
        "os": ua_info["os"],
        "device": ua_info["device"],
    }


def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """
    Rule-based user-agent parser to extract browser, operating system, and device type.
    """
    if not user_agent:
        return {"browser": "Unknown", "os": "Unknown", "device": "Desktop"}

    ua_lower = user_agent.lower()

    # 1. Device Category
    if any(bot in ua_lower for bot in ["bot", "crawler", "spider", "scraper", "curl", "python", "k6", "locust"]):
        device = "Bot"
    elif any(tablet in ua_lower for tablet in ["ipad", "tablet", "playbook", "silk"]):
        device = "Tablet"
    elif any(mobile in ua_lower for mobile in ["mobile", "android", "iphone", "ipod", "windows phone"]):
        device = "Mobile"
    else:
        device = "Desktop"

    # 2. Operating System
    if "windows" in ua_lower:
        os_name = "Windows"
    elif "iphone" in ua_lower or "ipad" in ua_lower or "ipod" in ua_lower:
        os_name = "iOS"
    elif "macintosh" in ua_lower or "mac os" in ua_lower:
        os_name = "macOS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "linux" in ua_lower:
        os_name = "Linux"
    elif device == "Bot":
        os_name = "Bot"
    else:
        os_name = "Other"

    # 3. Browser (order matters: check Edge/Opera before Chrome, Chrome before Safari)
    if device == "Bot":
        browser = "Bot/Crawler"
    elif "edg/" in ua_lower or "edge/" in ua_lower:
        browser = "Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    elif "chrome/" in ua_lower and "chromium" not in ua_lower:
        browser = "Chrome"
    elif "firefox/" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower:
        # Covers: Version/x.x Safari, Mobile/xxxx Safari, AppleWebKit ... Safari
        browser = "Safari"
    elif "applewebkit" in ua_lower and os_name in ("iOS", "macOS"):
        # iOS/macOS WebKit UA strings may omit the explicit 'Safari' token
        # (e.g. WKWebView / SFSafariViewController on iPhone)
        browser = "Safari"
    else:
        browser = "Other"

    return {
        "browser": browser,
        "os": os_name,
        "device": device,
    }
