import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import app

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "running" in res.json()["message"]


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data


def test_list_items():
    res = client.get("/items")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 3


def test_get_item_found():
    res = client.get("/items/1")
    assert res.status_code == 200
    assert res.json()["name"] == "Widget A"


def test_get_item_not_found():
    res = client.get("/items/9999")
    assert res.status_code == 404


def test_create_item():
    new_item = {"id": 99, "name": "Test Widget", "price": 1.99, "in_stock": True}
    res = client.post("/items", json=new_item)
    assert res.status_code == 201
    assert res.json()["name"] == "Test Widget"


def test_create_duplicate_item():
    item = {"id": 1, "name": "Duplicate", "price": 0.99, "in_stock": True}
    res = client.post("/items", json=item)
    assert res.status_code == 409


def test_delete_item():
    res = client.delete("/items/99")
    assert res.status_code == 204


def test_delete_nonexistent_item():
    res = client.delete("/items/9999")
    assert res.status_code == 404
