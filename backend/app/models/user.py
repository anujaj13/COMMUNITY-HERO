from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Enum
from app.utils.database import Base
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    AUTHORITY = "authority"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    avatar_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CITIZEN)
    is_verified = Column(Boolean, default=False)
    reputation_score = Column(Integer, default=0)
    badges_earned = Column(Integer, default=0)
    issues_reported = Column(Integer, default=0)
    verifications_made = Column(Integer, default=0)
    issues_resolved = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
