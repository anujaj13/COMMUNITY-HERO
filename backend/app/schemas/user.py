from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    CITIZEN = "citizen"
    AUTHORITY = "authority"
    ADMIN = "admin"

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.CITIZEN

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    role: UserRole
    is_verified: bool
    reputation_score: int
    badges_earned: int
    issues_reported: int
    verifications_made: int
    issues_resolved: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    id: int
    username: str
    full_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    address: Optional[str] = None
    role: UserRole
    reputation_score: int
    badges_earned: int
    issues_reported: int
    verifications_made: int
    issues_resolved: int
    is_verified: bool
    
    class Config:
        from_attributes = True

class UserRoleAssignment(BaseModel):
    """Schema for admin role assignment"""
    role: UserRole

class AdminPromotionRequest(BaseModel):
    """Schema for admin promotion request using a secret key"""
    user_identifier: str
    secret_key: str

