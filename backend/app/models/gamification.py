from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.utils.database import Base
from datetime import datetime

class UserBadge(Base):
    __tablename__ = "user_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    badge_name = Column(String)
    badge_description = Column(Text)
    badge_icon = Column(String)  # emoji or icon code
    earned_at = Column(DateTime, default=datetime.utcnow)
