from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Sample API",
    description="A simple API built with FastAPI",
    version="0.1.0"
)

# Define a Pydantic model for data validation
class Item(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50, description="Name of the item")
    description: Optional[str] = Field(None, max_length=200, description="Description of the item")
    price: float = Field(..., gt=0, description="Price of the item")
    tax: Optional[float] = Field(None, ge=0, description="Tax rate for the item")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Laptop",
                "description": "A high-performance laptop",
                "price": 999.99,
                "tax": 0.1
            }
        }

# Sample database (in-memory list for this example)
items_db = []
item_id_counter = 1

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to my first FastAPI application!"}

# GET all items
@app.get("/items/", response_model=List[Item], tags=["Items"])
async def get_items(skip: int = 0, limit: int = 10):
    return items_db[skip: skip + limit]

# GET a specific item by ID
@app.get("/items/{item_id}", response_model=Item, tags=["Items"])
async def get_item(
    item_id: int = Path(..., title="ID of the item to get", ge=1)):

    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# POST a new item
@app.post("/items/", response_model=Item, status_code=201, tags=["Items"])
async def create_item(item: Item):
    global item_id_counter
    
    # Set the item ID
    item.id = item_id_counter
    item_id_counter += 1
    
    # Store the item
    items_db.append(item)
    return item

# PUT (update) an existing item
@app.put("/items/{item_id}", response_model=Item, tags=["Items"])
async def update_item(
    item_id: int = Path(..., title="ID of the item to update", ge=1),
    item: Item = None):

    for i, stored_item in enumerate(items_db):
        if stored_item.id == item_id:
            # Preserve the ID
            item.id = item_id
            # Update the item based on the one from the input
            items_db[i] = item
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# DELETE an item
@app.delete("/items/{item_id}", status_code=204, tags=["Items"])
async def delete_item(item_id: int = Path(..., title="ID of the item to delete", ge=1)):
    for i, stored_item in enumerate(items_db):
        if stored_item.id == item_id:
            # Remove the item
            items_db.pop(i)
            return
    raise HTTPException(status_code=404, detail="Item not found")

# Run the server if this file is executed directly
if __name__ == "__main__":
    # Add some sample data
    sample_item = Item(name="Sample Item", description="This is a sample item", price=10.99, tax=0.2)
    sample_item.id = item_id_counter
    item_id_counter += 1
    items_db.append(sample_item)
    
    # Start the server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)