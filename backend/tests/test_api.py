import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_api_validation_error_missing_finish():
    response = client.post("/api/v1/route", json={"start": "New York, NY"})
    assert response.status_code == 422

def test_api_validation_error_empty_body():
    response = client.post("/api/v1/route", json={})
    assert response.status_code == 422

@patch("app.api.routes.GeocodingService.geocode")
@patch("app.api.routes.RoutingService.get_route")
def test_successful_route_api(mock_get_route, mock_geocode):
    mock_geocode.side_effect = [
        (40.7128, -74.0060),  # New York
        (39.9526, -75.1652)   # Philadelphia (~95 miles)
    ]
    mock_get_route.return_value = {
        "distance_miles": 95.0,
        "duration_minutes": 110.0,
        "geometry": {
            "type": "LineString",
            "coordinates": [[-74.0060, 40.7128], [-75.1652, 39.9526]]
        }
    }
    
    response = client.post(
        "/api/v1/route",
        json={"start": "New York, NY", "finish": "Philadelphia, PA"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["start"]["address"] == "New York, NY"
    assert data["finish"]["address"] == "Philadelphia, PA"
    assert data["vehicle"]["max_range_miles"] == 500.0
    assert data["vehicle"]["mpg"] == 10.0
    assert data["route"]["distance_miles"] == 95.0
    assert data["fuel"]["total_fuel_consumed"] == 9.5
    assert len(data["fuel_stops"]) == 0

