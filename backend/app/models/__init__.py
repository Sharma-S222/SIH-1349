from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Float,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Station(Base):
    __tablename__ = "station"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(50), nullable=True, unique=True)
    timezone = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<Station(id={self.id}, name={self.name})>"


class Camera(Base):
    __tablename__ = "camera"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("station.id"), nullable=False)
    name = Column(String(255), nullable=False)
    zone_context = Column(String(255), nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, server_default=func.now())

    station = relationship("Station", backref="cameras")

    def __repr__(self):
        return f"<Camera(id={self.id}, name={self.name})>"


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), nullable=False, unique=True)
    schema_version = Column(String(20), nullable=False)
    camera_id = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    zone_id = Column(String(100), nullable=True)
    people_count = Column(Integer, nullable=True)
    raw_metadata = Column(Text, nullable=True, server_default="{}")
    snapshot_path = Column(String(500), nullable=True)
    clip_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_event_timestamp", "timestamp"),
        Index("ix_event_camera_id", "camera_id"),
        Index("ix_event_event_type", "event_type"),
    )

    def __repr__(self):
        return f"<Event(event_id={self.event_id}, camera_id={self.camera_id})>"


class Incident(Base):
    __tablename__ = "incident"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(20), default="NEW")
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Incident(id={self.id}, event_id={self.event_id}, status={self.status})>"


class CrowdMetric(Base):
    __tablename__ = "crowd_metric"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), nullable=False)
    zone_id = Column(String(100), nullable=True)
    people_count = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<CrowdMetric(id={self.id}, camera_id={self.camera_id}, people_count={self.people_count})>"


class OperatorAction(Base):
    __tablename__ = "operator_action"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incident.id"), nullable=True)
    action = Column(String(50), nullable=False)
    user = Column(String(100), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    note = Column(Text, nullable=True)

    incident = relationship("Incident", backref="operator_actions")

    def __repr__(self):
        return f"<OperatorAction(id={self.id}, incident_id={self.incident_id}, action={self.action})>"