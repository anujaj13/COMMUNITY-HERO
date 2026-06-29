from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from app.utils.database import Base
from datetime import datetime
import enum

class ResolutionStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IssueResolution(Base):
    __tablename__ = "issue_resolutions"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), index=True)
    resolver_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(ResolutionStatus))
    notes = Column(Text, nullable=True)
    previous_status = Column(String, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)
    estimated_completion = Column(DateTime, nullable=True)
