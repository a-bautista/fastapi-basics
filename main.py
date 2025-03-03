from fastapi import FastAPI, HTTPException, Path, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Database configuration - read from environment variables or use defaults
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "db")  # 'db' is the service name in docker-compose
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fastapi_db")

# Create SQLAlchemy connection
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define SQLAlchemy model
class ItemModel(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    tax = Column(Float, nullable=True)

# Initialize FastAPI app
app = FastAPI(
    title="Sample API with PostgreSQL",
    description="A simple API built with FastAPI and PostgreSQL",
    version="0.2.0"
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define a Pydantic model for API validation
class Item(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50, description="Name of the item")
    description: Optional[str] = Field(None, max_length=200, description="Description of the item")
    price: float = Field(..., gt=0, description="Price of the item")
    tax: Optional[float] = Field(None, ge=0, description="Tax rate for the item")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "Laptop",
                "description": "A high-performance laptop",
                "price": 999.99,
                "tax": 0.1
            }
        }

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to my FastAPI application with PostgreSQL!"}

# GET all items
@app.get("/items/", response_model=List[Item], tags=["Items"])
async def get_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(ItemModel).offset(skip).limit(limit).all()
    return items

# GET a specific item by ID
@app.get("/items/{item_id}", response_model=Item, tags=["Items"])
async def get_item(item_id: int = Path(..., title="ID of the item to get", ge=1), db: Session = Depends(get_db)):
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# POST a new item
@app.post("/items/", response_model=Item, status_code=201, tags=["Items"])
async def create_item(item: Item, db: Session = Depends(get_db)):
    db_item = ItemModel(
        name=item.name,
        description=item.description,
        price=item.price,
        tax=item.tax
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# PUT (update) an existing item
@app.put("/items/{item_id}", response_model=Item, tags=["Items"])
async def update_item(
    item_id: int = Path(..., title="ID of the item to update", ge=1),
    item: Item = None,
    db: Session = Depends(get_db)
):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update item fields
    db_item.name = item.name
    db_item.description = item.description
    db_item.price = item.price
    db_item.tax = item.tax
    
    db.commit()
    db.refresh(db_item)
    return db_item

# DELETE an item
@app.delete("/items/{item_id}", status_code=204, tags=["Items"])
async def delete_item(item_id: int = Path(..., title="ID of the item to delete", ge=1), db: Session = Depends(get_db)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return None

# Initialize the database
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    
    # Add sample data if the database is empty
    db = SessionLocal()
    if db.query(ItemModel).count() == 0:
        db_item = ItemModel(
            name="Sample Item",
            description="This is a sample item",
            price=10.99,
            tax=0.2
        )
        db.add(db_item)
        db.commit()
    db.close()

# Run the server if this file is executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)