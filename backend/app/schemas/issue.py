from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class IssueCategory(str, Enum):
    POTHOLE = "pothole"
    WATER_LEAK = "water_leak"
    STREETLIGHT = "streetlight"
    WASTE_MANAGEMENT = "waste_management"
    ROAD_DAMAGE = "road_damage"
    FLOODING = "flooding"
    PUBLIC_FACILITY = "public_facility"
    SAFETY = "safety"
    OTHER = "other"

class IssuePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IssueStatus(str, Enum):
    REPORTED = "reported"
    VERIFIED = "verified"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IssueCreate(BaseModel):
    title: str
    description: str
    category: IssueCategory
    priority: IssuePriority = IssuePriority.MEDIUM
    latitude: float
    longitude: float
    address: str

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[IssueCategory] = None
    priority: Optional[IssuePriority] = None
    status: Optional[IssueStatus] = None

class IssueResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    latitude: float
    longitude: float
    address: str
    image_url: Optional[str]
    video_url: Optional[str]
    reported_by_id: int
    assigned_to_id: Optional[int] = None
    verification_count: int
    impact_score: float
    estimated_resolution_date: Optional[datetime]
    claimed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class IssueCategoryResponse(BaseModel):
    category: str
    count: int
    percentage: float
