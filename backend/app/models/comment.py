from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.utils.database import Base
from datetime import datetime

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(Text)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
