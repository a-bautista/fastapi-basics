from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.orm import relationship

from app.models.base import Base

class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False, index=True) # Added index=True for potential searches
    response = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    #created_at = Column(DateTime(timezone=True), server_default=func.now()) # Use server_default for consistency
    #updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) # Added updated_at

    # Relationship to User
    # 'owner' is how you'll access the User object from a Prompt object (e.g., my_prompt.owner)
    # 'back_populates' links this relationship to the one defined in the User model
    owner = relationship("User", back_populates="prompts")

    def __repr__(self):
        return f"<Prompt(id={self.id}, user_id={self.user_id})>"
    