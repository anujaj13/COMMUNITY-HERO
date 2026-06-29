from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum, ForeignKey
from app.utils.database import Base
from datetime import datetime
import enum

class IssueCategory(str, enum.Enum):
    POTHOLE = "pothole"
    WATER_LEAK = "water_leak"
    STREETLIGHT = "streetlight"
    WASTE_MANAGEMENT = "waste_management"
    ROAD_DAMAGE = "road_damage"
    FLOODING = "flooding"
    PUBLIC_FACILITY = "public_facility"
    SAFETY = "safety"
    OTHER = "other"

class IssuePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IssueStatus(str, enum.Enum):
    REPORTED = "reported"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(Enum(IssueCategory), default=IssueCategory.OTHER)
    priority = Column(Enum(IssuePriority), default=IssuePriority.MEDIUM)
    status = Column(Enum(IssueStatus), default=IssueStatus.REPORTED)
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String)
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    reported_by_id = Column(Integer, ForeignKey("users.id"))
    verification_count = Column(Integer, default=0)
    impact_score = Column(Float, default=0.0)
    estimated_resolution_date = Column(DateTime, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    claimed_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
