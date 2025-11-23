from fastapi.testclient import TestClient
from backend.app.main import app, SQLModel, engine

SQLModel.metadata.create_all(engine)


def test_create_and_list_deals():
    with TestClient(app) as client:
        response = client.post("/api/deals", json={"address": "123 Main St", "price": 100000})
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "123 Main St"

        response = client.get("/api/deals")
        assert response.status_code == 200
        deals = response.json()
        assert any(deal["address"] == "123 Main St" for deal in deals)
