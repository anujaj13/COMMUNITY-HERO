from pydantic import BaseModel
from datetime import datetime

class CommentCreate(BaseModel):
    issue_id: int
    text: str

class CommentResponse(BaseModel):
    id: int
    issue_id: int
    user_id: int
    text: str
    likes: int
    created_at: datetime
    
    class Config:
        from_attributes = True
