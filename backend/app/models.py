from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from backend.app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class TrafficEvent(Base):
    __tablename__ = "traffic_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    site_id = Column(String(64), index=True, default="demo-site", nullable=False)
    session_id = Column(String(64), index=True, nullable=False)
    event_type = Column(String(32), index=True, default="pageview", nullable=False)
    path = Column(String(256), index=True, nullable=False)
    referrer = Column(String(512), default="", nullable=False)
    user_agent = Column(String(512), default="", nullable=False)
    ip = Column(String(64), index=True, default="127.0.0.1", nullable=False)
    status_code = Column(Integer, index=True, default=200, nullable=False)
    response_time_ms = Column(Float, default=0.0, nullable=False)
    duration_ms = Column(Float, default=0.0, nullable=False)
    browser = Column(String(64), default="Unknown", nullable=False)
    os = Column(String(64), default="Unknown", nullable=False)
    device = Column(String(32), default="Desktop", nullable=False)
    screen_resolution = Column(String(32), default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "site_id": self.site_id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "path": self.path,
            "referrer": self.referrer,
            "user_agent": self.user_agent,
            "ip": self.ip,
            "status_code": self.status_code,
            "response_time_ms": round(self.response_time_ms, 2),
            "duration_ms": round(self.duration_ms, 2),
            "browser": self.browser,
            "os": self.os,
            "device": self.device,
            "screen_resolution": self.screen_resolution,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    anomaly_type = Column(String(64), index=True, nullable=False)  # traffic_spike, error_surge, suspicious_ip
    severity = Column(String(32), default="warning", nullable=False)  # info, warning, critical
    description = Column(Text, nullable=False)
    metric_value = Column(Float, default=0.0, nullable=False)
    baseline_value = Column(Float, default=0.0, nullable=False)
    z_score = Column(Float, default=0.0, nullable=False)
    ip = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "metric_value": round(self.metric_value, 2),
            "baseline_value": round(self.baseline_value, 2),
            "z_score": round(self.z_score, 2),
            "ip": self.ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
