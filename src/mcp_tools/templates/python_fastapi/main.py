from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="FastAPI Application",
    description="A modern Python API built with FastAPI",
    version="1.0.0"
)
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    tax: Optional[float]
    total: float

# In-memory storage (use database in production)
items_db: List[ItemResponse] = []
next_id = 1

@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI!",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/items/", response_model=ItemResponse)
async def create_item(item: Item):
    global next_id
    
    total = item.price + (item.tax or 0)
    new_item = ItemResponse(
        id=next_id,
        name=item.name,
        description=item.description,
        price=item.price,
        tax=item.tax,
        total=total
    )
    
    items_db.append(new_item)
    next_id += 1
    
    return new_item

@app.get("/items/", response_model=List[ItemResponse])
async def get_items():
    return items_db

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: Item):
    for i, existing_item in enumerate(items_db):
        if existing_item.id == item_id:
            total = item.price + (item.tax or 0)
            updated_item = ItemResponse(
                id=item_id,
                name=item.name,
                description=item.description,
                price=item.price,
                tax=item.tax,
                total=total
            )
            items_db[i] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            del items_db[i]
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)