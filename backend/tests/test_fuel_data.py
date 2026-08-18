import pytest
import os
import pandas as pd
from app.services.fuel_stations import FuelStationService, Station
from app.config import get_settings

def test_find_stations_near_route():
    service = FuelStationService()
    service.stations = [
        Station(1, "Test Station", "123 Main", "City", "ST", 1, 3.0, 40.0, -80.0),
        Station(2, "Far Station", "456 Oak", "City", "ST", 2, 2.5, 45.0, -70.0)
    ]
    route_coords = [[-80.0, 40.0], [-79.0, 40.0]]
    result = service.find_stations_near_route(route_coords, corridor_miles=25.0)
    assert len(result) == 1
    assert result[0].station.opis_id == 1
    assert result[0].distance_from_route <= 25.0

def test_load_real_processed_csv():
    settings = get_settings()
    service = FuelStationService()
    if os.path.exists(settings.FUEL_DATA_PATH):
        service.load_stations(settings.FUEL_DATA_PATH)
        assert len(service.stations) > 0
        first_station = service.stations[0]
        assert first_station.price > 0
        assert -180.0 <= first_station.longitude <= 180.0
        assert -90.0 <= first_station.latitude <= 90.0

