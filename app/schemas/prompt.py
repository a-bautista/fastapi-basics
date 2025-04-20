# app/schemas/prompt.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Shared properties (can be used for base input/output)
class PromptBase(BaseModel):
    """Base schema with common Prompt fields"""
    prompt: str = Field(..., description="Content of the user's prompt")
    # Response might not always be present on creation or update input because you need to hit the api
    response: Optional[str] = Field(None, description="Generated response to the prompt") 

# Properties to receive via API on creation
class PromptCreate(BaseModel):
    """Schema for creating a new prompt. Only the prompt text is needed from the user."""
    prompt: str = Field(..., min_length=5, description="Content of the prompt to be processed")
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "How can I optimize this Python list comprehension for speed?"
            }
        }

# Properties to receive via API on update
# Decide carefully what should be updatable but generally the prompts are immutable, so no need to update them
class PromptUpdate(BaseModel):
    """Schema for updating an existing prompt."""
    response: Optional[str] = Field(None, description="Updated or regenerated response")
    
    class Config:
        schema_extra = {
            "example": {
                "response": "Consider using a generator expression if memory is also a concern."
            }
        }

# Properties to return to client (API response)
class Prompt(PromptBase):
    """Schema for representing a prompt in API responses."""
    id: int
    user_id: int # Include the ID of the user who owns the prompt
    #created_at: datetime
    #updated_at: datetime # Include updated_at timestamp

    class Config:
        orm_mode = True # Enable ORM mode to read data directly from SQLAlchemy models
        schema_extra = {
            "example": {
                "id": 123,
                "prompt": "How can I optimize this Python list comprehension for speed?",
                "response": "Using list comprehensions is generally fast in Python. Show me the code for specific advice.",
                "user_id": 1
            }
        }
        
# You might also want a schema for listing multiple prompts, often nested
#class PromptInDBBase(Prompt):
#    owner: Optional["User"] # Forward reference for nested User info if needed

# Import User schema if you nest it
# from app.schemas.user import User