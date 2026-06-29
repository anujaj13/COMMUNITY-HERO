from pydantic import BaseModel
from datetime import datetime

class BadgeResponse(BaseModel):
    id: int
    badge_name: str
    badge_description: str
    badge_icon: str
    earned_at: datetime
    
    class Config:
        from_attributes = True
