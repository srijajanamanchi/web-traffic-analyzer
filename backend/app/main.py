import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import (
    Depends,
    FastAPI,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.analytics import get_traffic_analytics
from backend.app.anomaly import (
    detect_error_surge,
    detect_suspicious_ips,
    dispatch_alert_webhook,
)
from backend.app.config import settings
from backend.app.database import SessionLocal, get_db, init_db
from backend.app.logger import logger
from backend.app.metrics import (
    ACTIVE_USERS_GAUGE,
    ANOMALIES_DETECTED_TOTAL,
    COLLECTED_EVENTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
    get_metrics_response,
)
from backend.app.models import AnomalyAlert, TrafficEvent
from backend.app.parser import parse_nginx_log_line, parse_user_agent
from backend.app.websocket_manager import ws_manager


# --- Schemas ---
class CollectPayload(BaseModel):
    site_id: str = Field(default="demo-site")
    session_id: str = Field(...)
    event_type: str = Field(default="pageview")  # pageview, click, form_submit, unload
    path: str = Field(default="/")
    referrer: str | None = Field(default="")
    user_agent: str | None = Field(default="")
    screen_resolution: str | None = Field(default="")
    load_time_ms: float | None = Field(default=0.0)
    duration_ms: float | None = Field(default=0.0)
    status_code: int | None = Field(default=200)


class LogIngestPayload(BaseModel):
    lines: list[str]


# --- Background Tasks ---
async def tail_nginx_log_task():
    """
    Background worker that tails the Nginx combined log file if configured.
    """
    log_path = settings.NGINX_LOG_PATH
    logger.info(f"Checking Nginx log path for tailing: {log_path}")

    # Wait for file to exist
    while settings.TAIL_NGINX_LOGS:
        if os.path.exists(log_path):
            break
        await asyncio.sleep(2)

    if not settings.TAIL_NGINX_LOGS or not os.path.exists(log_path):
        return

    logger.info(f"Starting active Nginx log tailer on {log_path}")
    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            # Go to end of file
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    parsed = parse_nginx_log_line(line)
                    if parsed:
                        db = SessionLocal()
                        try:
                            event = TrafficEvent(
                                site_id="demo-site",
                                session_id="nginx-log",
                                event_type="nginx_log",
                                path=parsed["path"],
                                referrer=parsed["referrer"],
                                user_agent=parsed["user_agent"],
                                ip=parsed["ip"],
                                status_code=parsed["status_code"],
                                response_time_ms=0.0,
                                duration_ms=0.0,
                                browser=parsed["browser"],
                                os=parsed["os"],
                                device=parsed["device"],
                                screen_resolution="",
                                created_at=parsed["timestamp"],
                            )
                            db.add(event)
                            db.commit()

                            COLLECTED_EVENTS_TOTAL.labels(site_id="demo-site", event_type="nginx_log").inc()
                            await ws_manager.broadcast({
                                "type": "new_event",
                                "event": event.to_dict(),
                            })
                        except Exception as e:
                            db.rollback()
                            logger.error(f"Error persisting tailed log line: {e}")
                        finally:
                            db.close()
                else:
                    await asyncio.sleep(0.5)
    except Exception as exc:
        logger.error(f"Nginx log tailer terminated: {exc}")


async def periodic_stats_broadcast_task():
    """
    Periodically computes live KPIs and broadcasts them to connected WebSocket clients.
    """
    while True:
        try:
            await asyncio.sleep(2.0)
            if not ws_manager.active_connections:
                continue

            db = SessionLocal()
            try:
                now = datetime.now(UTC)
                stats = get_traffic_analytics(db, start_time=now - timedelta(minutes=5), end_time=now)
                active_users = stats["active_users_now"]
                ACTIVE_USERS_GAUGE.set(active_users)

                await ws_manager.broadcast({
                    "type": "kpi_tick",
                    "data": {
                        "active_users_now": active_users,
                        "total_requests_5m": stats["total_requests"],
                        "error_rate_5m": stats["error_rate"],
                        "latency_p95": stats["latency"]["p95"],
                        "avg_latency": stats["latency"]["avg"],
                        "timestamp": now.isoformat(),
                    },
                })
            except Exception as e:
                logger.error(f"Periodic KPI broadcast failed: {e}")
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"Error in broadcast task: {exc}")
            await asyncio.sleep(2.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Web Traffic Analyzer service...")
    init_db()

    broadcast_task = asyncio.create_task(periodic_stats_broadcast_task())
    tail_task = None
    if settings.TAIL_NGINX_LOGS:
        tail_task = asyncio.create_task(tail_nginx_log_task())

    yield

    # Shutdown
    logger.info("Shutting down Web Traffic Analyzer...")
    broadcast_task.cancel()
    if tail_task:
        tail_task.cancel()


# --- Application Instance ---
app = FastAPI(
    title="Real-Time Web Traffic Analyzer API",
    description="Telemetry collection, live analysis, anomaly detection, and Prometheus observability.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request Middleware for Prometheus Metrics ---
@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    endpoint = request.url.path
    # Group static or dynamic endpoints to prevent high cardinality
    endpoint_clean = endpoint.split("?")[0] if endpoint.startswith("/api/") else endpoint

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        path=endpoint_clean,
        status=str(response.status_code),
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        path=endpoint_clean,
    ).observe(duration)

    return response


# --- Helper to extract client IP ---
def extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Take the leftmost IP
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


# --- Anomaly Inspection Helper ---
async def inspect_anomalies(db: Session, event: TrafficEvent):
    """
    Check if incoming event triggers anomaly thresholds (spike, error surge, suspicious IP).
    """
    now = datetime.now(UTC)
    five_min_ago = now - timedelta(minutes=5)

    recent_events = (
        db.query(TrafficEvent)
        .filter(TrafficEvent.created_at >= five_min_ago)
        .all()
    )

    # 1. Check Error Surge
    if event.status_code >= 400:
        codes = [e.status_code for e in recent_events]
        error_alert = detect_error_surge(codes, error_rate_threshold=settings.ERROR_RATE_SURGE_THRESHOLD)
        if error_alert:
            # Check if recently flagged to avoid spamming
            existing = (
                db.query(AnomalyAlert)
                .filter(
                    AnomalyAlert.anomaly_type == "error_surge",
                    AnomalyAlert.created_at >= now - timedelta(minutes=2),
                )
                .first()
            )
            if not existing:
                alert_obj = AnomalyAlert(**error_alert)
                db.add(alert_obj)
                db.commit()
                ANOMALIES_DETECTED_TOTAL.labels(anomaly_type="error_surge", severity=error_alert["severity"]).inc()
                await ws_manager.broadcast({"type": "anomaly_alert", "alert": alert_obj.to_dict()})
                await dispatch_alert_webhook(error_alert)

    # 2. Check Suspicious IP
    if event.ip and event.ip not in ("127.0.0.1", "localhost"):
        ip_events = [{"ip": e.ip, "status_code": e.status_code} for e in recent_events if e.ip == event.ip]
        ip_alerts = detect_suspicious_ips(ip_events, error_threshold=5, rate_threshold=40)
        for ip_alert in ip_alerts:
            existing = (
                db.query(AnomalyAlert)
                .filter(
                    AnomalyAlert.anomaly_type == "suspicious_ip",
                    AnomalyAlert.ip == ip_alert["ip"],
                    AnomalyAlert.created_at >= now - timedelta(minutes=5),
                )
                .first()
            )
            if not existing:
                alert_obj = AnomalyAlert(**ip_alert)
                db.add(alert_obj)
                db.commit()
                ANOMALIES_DETECTED_TOTAL.labels(anomaly_type="suspicious_ip", severity=ip_alert["severity"]).inc()
                await ws_manager.broadcast({"type": "anomaly_alert", "alert": alert_obj.to_dict()})
                await dispatch_alert_webhook(ip_alert)


# --- Endpoints ---
@app.post("/api/collect", status_code=status.HTTP_201_CREATED)
async def collect_telemetry(request: Request, db: Session = Depends(get_db)):
    """
    Collects tracking events sent by the lightweight JS tracker snippet.
    Supports both JSON and text/plain (used by navigator.sendBeacon).
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            raw_data = await request.json()
        else:
            body_bytes = await request.body()
            body_text = body_bytes.decode("utf-8", errors="ignore")
            raw_data = json.loads(body_text) if body_text else {}
    except Exception as exc:
        logger.warning(f"Failed to parse /api/collect payload: {exc}")
        return Response(content=json.dumps({"error": "Invalid JSON"}), status_code=400, media_type="application/json")

    payload = CollectPayload(**raw_data)
    client_ip = extract_client_ip(request)

    # Extract user agent from payload or fallback to request header
    user_agent_str = payload.user_agent or request.headers.get("user-agent", "")
    ua_info = parse_user_agent(user_agent_str)

    event = TrafficEvent(
        site_id=payload.site_id,
        session_id=payload.session_id,
        event_type=payload.event_type,
        path=payload.path or "/",
        referrer=payload.referrer or "",
        user_agent=user_agent_str,
        ip=client_ip,
        status_code=payload.status_code or 200,
        response_time_ms=payload.load_time_ms or 0.0,
        duration_ms=payload.duration_ms or 0.0,
        browser=ua_info["browser"],
        os=ua_info["os"],
        device=ua_info["device"],
        screen_resolution=payload.screen_resolution or "",
        created_at=datetime.now(UTC),
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    COLLECTED_EVENTS_TOTAL.labels(site_id=payload.site_id, event_type=payload.event_type).inc()

    # Broadcast event to WebSocket dashboard
    await ws_manager.broadcast({
        "type": "new_event",
        "event": event.to_dict(),
    })

    # Background anomaly checking
    asyncio.create_task(inspect_anomalies(db, event))

    return {"status": "ok", "event_id": event.id}


@app.post("/api/logs/ingest")
async def ingest_logs(payload: LogIngestPayload, db: Session = Depends(get_db)):
    """
    Ingest raw Nginx combined log lines in bulk.
    """
    count = 0
    for line in payload.lines:
        parsed = parse_nginx_log_line(line)
        if parsed:
            ev = TrafficEvent(
                site_id="demo-site",
                session_id=f"nginx-{parsed['ip']}",
                event_type="nginx_log",
                path=parsed["path"],
                referrer=parsed["referrer"],
                user_agent=parsed["user_agent"],
                ip=parsed["ip"],
                status_code=parsed["status_code"],
                response_time_ms=0.0,
                duration_ms=0.0,
                browser=parsed["browser"],
                os=parsed["os"],
                device=parsed["device"],
                screen_resolution="",
                created_at=parsed["timestamp"],
            )
            db.add(ev)
            count += 1
    db.commit()
    return {"status": "ok", "ingested_count": count}


@app.get("/api/stats")
def get_stats(
    time_range: str = Query("1h", pattern="^(5m|15m|1h|24h|all)$"),
    path: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Query calculated traffic metrics and time-series for the specified duration.
    """
    now = datetime.now(UTC)
    delta_map = {
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "all": timedelta(days=365),
    }
    start_time = now - delta_map.get(time_range, timedelta(hours=1))
    return get_traffic_analytics(db, start_time=start_time, end_time=now, path_filter=path)


@app.get("/api/events")
def get_recent_events(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """
    Retrieve latest tracked events in descending chronological order.
    """
    events = (
        db.query(TrafficEvent)
        .order_by(TrafficEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return [ev.to_dict() for ev in events]


@app.get("/api/anomalies")
def get_recent_anomalies(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """
    Retrieve recent anomaly detections.
    """
    alerts = (
        db.query(AnomalyAlert)
        .order_by(AnomalyAlert.created_at.desc())
        .limit(limit)
        .all()
    )
    return [a.to_dict() for a in alerts]


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Readiness & liveness healthcheck verifying database connectivity.
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:
        logger.error(f"Healthcheck failed: {exc}")
        return Response(
            content=json.dumps({"status": "unhealthy", "error": str(exc)}),
            status_code=503,
            media_type="application/json",
        )


@app.get("/metrics")
def metrics():
    """
    Prometheus telemetry scraping endpoint.
    """
    content, content_type = get_metrics_response()
    return Response(content=content, media_type=content_type)


@app.websocket("/ws/traffic")
async def websocket_traffic_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket feed for live traffic events and alerts.
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial confirmation message
        await websocket.send_text(
            json.dumps({
                "type": "connected",
                "message": "Connected to real-time traffic telemetry stream",
                "timestamp": datetime.now(UTC).isoformat(),
            })
        )
        while True:
            # Keep connection open and receive optional client heartbeats / ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.debug(f"WebSocket client loop exception: {exc}")
        await ws_manager.disconnect(websocket)
