# app/crud/prompt.py
from typing import List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptUpdate

class CRUDPrompt(CRUDBase[Prompt, PromptCreate, PromptUpdate]):
    """CRUD operations for Prompt model"""
    
    def create_with_owner(
        self, db: Session, *, obj_in: PromptCreate, user_id: int
    ) -> Prompt:
        """
        Create a new prompt associated with a specific user.

        Args:
            db: Database session
            obj_in: Data for creating the prompt (contains 'prompt' text)
            user_id: ID of the user creating the prompt

        Returns:
            The created prompt object
        """
        # Convert the Pydantic model to a dictionary
        # Note: obj_in only contains 'prompt' based on PromptCreate schema
        obj_in_data = obj_in.dict() 
        
        # Create the Prompt model instance, adding the required user_id
        # The 'response' will initially be None as per the model definition (nullable=True)
        # It might be populated later or by a separate process/service.
        db_obj = self.model(**obj_in_data, user_id=user_id, response=None) 
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Prompt]:
        """
        Get multiple prompts belonging to a specific user with pagination.

        Args:
            db: Database session
            user_id: ID of the owner user
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of prompts belonging to the user
        """
        return (
            db.query(self.model)
            .filter(Prompt.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # The base 'update' method from CRUDBase should work fine for updating
    # 'prompt' or 'response' fields if they are provided in the PromptUpdate schema.
    # If you needed specific logic during update (e.g., triggering a re-generation
    # of the response when the prompt text changes), you would override 'update' here.

    # The base 'get' and 'remove' methods from CRUDBase should also work as expected.

# Create a singleton instance for easy import and use in API routes
# prompt = CRUDPrompt(Prompt)
