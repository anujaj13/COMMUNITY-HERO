from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ResolutionStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IssueAssign(BaseModel):
    """Schema for assigning/claiming an issue"""
    estimated_resolution_date: Optional[datetime] = None

class IssueStatusUpdate(BaseModel):
    """Schema for updating issue status"""
    status: str
    notes: Optional[str] = None
    estimated_resolution_date: Optional[datetime] = None

class ResolutionComplete(BaseModel):
    """Schema for marking issue as resolved"""
    resolution_notes: str
    estimated_completion: Optional[datetime] = None

class IssueResolutionResponse(BaseModel):
    """Response schema for resolution history"""
    id: int
    issue_id: int
    resolver_id: int
    status: str
    notes: Optional[str] = None
    previous_status: Optional[str] = None
    changed_at: datetime
    
    class Config:
        from_attributes = True

class IssueDetailedResponse(BaseModel):
    """Detailed issue response with resolver info"""
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    address: str
    latitude: float
    longitude: float
    reported_by_id: int
    verification_count: int
    impact_score: float
    assigned_to_id: Optional[int] = None
    resolved_by_id: Optional[int] = None
    resolution_notes: Optional[str] = None
    claimed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    estimated_resolution_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
