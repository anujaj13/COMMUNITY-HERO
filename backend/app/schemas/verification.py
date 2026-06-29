from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VerificationCreate(BaseModel):
    issue_id: int
    is_confirmed: bool
    severity_level: str
    comment: Optional[str] = None

class VerificationResponse(BaseModel):
    id: int
    issue_id: int
    verified_by_id: int
    is_confirmed: bool
    severity_level: str
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
