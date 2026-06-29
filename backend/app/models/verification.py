from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, UniqueConstraint
from app.utils.database import Base
from datetime import datetime

class Verification(Base):
    __tablename__ = "verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"))
    verified_by_id = Column(Integer, ForeignKey("users.id"))
    is_confirmed = Column(Boolean, default=False)
    severity_level = Column(String)  # low, medium, high, critical
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('issue_id', 'verified_by_id', name='unique_user_verification_per_issue'),
    )
