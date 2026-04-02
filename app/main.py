from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import time
import os

app = FastAPI(
    title="DevOps Demo API",
    description="A production-ready FastAPI service with health checks and metrics",
    version="1.0.0",
)

# ---------- Models ----------


class Item(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool = True


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime_seconds: float


# ---------- In-memory store (demo only) ----------

START_TIME = time.time()
ITEMS: List[Item] = [
    Item(id=1, name="Widget A", price=9.99),
    Item(id=2, name="Widget B", price=19.99),
    Item(id=3, name="Widget C", price=4.99, in_stock=False),
]

# ---------- Routes ----------


@app.get("/", tags=["root"])
def root():
    return {"message": "DevOps GitOps Pipeline — API is running"}


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    """Kubernetes liveness + readiness probe endpoint."""
    return HealthResponse(
        status="healthy",
        version=os.getenv("APP_VERSION", "1.0.0"),
        environment=os.getenv("APP_ENV", "development"),
        uptime_seconds=round(time.time() - START_TIME, 2),
    )


@app.get("/items", response_model=List[Item], tags=["items"])
def list_items():
    return ITEMS


@app.get("/items/{item_id}", response_model=Item, tags=["items"])
def get_item(item_id: int):
    for item in ITEMS:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")


@app.post("/items", response_model=Item, status_code=201, tags=["items"])
def create_item(item: Item):
    for existing in ITEMS:
        if existing.id == item.id:
            raise HTTPException(status_code=409, detail="Item ID already exists")
    ITEMS.append(item)
    return item


@app.delete("/items/{item_id}", status_code=204, tags=["items"])
def delete_item(item_id: int):
    for i, item in enumerate(ITEMS):
        if item.id == item_id:
            ITEMS.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

