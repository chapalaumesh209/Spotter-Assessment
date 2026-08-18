import pytest
from app.services.optimization import RouteOptimizationService, RouteOptimizationError
from app.services.fuel_stations import StationOnRoute, Station

def create_station(route_mile: float, price: float) -> StationOnRoute:
    return StationOnRoute(
        station=Station(
            opis_id=1, name="Test", address="123", city="C", state="S", rack_id=1,
            price=price, latitude=0.0, longitude=0.0
        ),
        route_mile=route_mile,
        distance_from_route=0.1
    )

def test_short_route_no_stops():
    service = RouteOptimizationService()
    result = service.optimize_fuel_stops(
        total_distance=300.0,
        stations_on_route=[],
        tank_capacity=50.0,
        mpg=10.0,
        max_range=500.0
    )
    assert len(result["stops"]) == 0
    assert result["total_gallons_purchased"] == 0.0

def test_medium_route_one_stop():
    service = RouteOptimizationService()
    stations = [create_station(400.0, 3.0)]
    result = service.optimize_fuel_stops(
        total_distance=700.0,
        stations_on_route=stations,
        tank_capacity=50.0,
        mpg=10.0,
        max_range=500.0
    )
    assert len(result["stops"]) == 1
    assert result["stops"][0]["route_mile"] == 400.0

def test_multiple_stops():
    service = RouteOptimizationService()
    stations = [
        create_station(400.0, 3.5),
        create_station(800.0, 3.2),
        create_station(1200.0, 3.0)
    ]
    result = service.optimize_fuel_stops(
        total_distance=1500.0,
        stations_on_route=stations,
        tank_capacity=50.0,
        mpg=10.0,
        max_range=500.0
    )
    assert len(result["stops"]) > 1

def test_cheapest_unreachable():
    service = RouteOptimizationService()
    stations = [
        create_station(400.0, 4.0),
        create_station(600.0, 2.0)  # Unreachable with initial 500 miles
    ]
    result = service.optimize_fuel_stops(
        total_distance=800.0,
        stations_on_route=stations,
        tank_capacity=50.0,
        mpg=10.0,
        max_range=500.0
    )
    # Should stop at 400 first (reachable), then at 600 (cheaper)
    assert len(result["stops"]) == 2
    assert result["stops"][0]["route_mile"] == 400.0
    assert result["stops"][1]["route_mile"] == 600.0
    assert result["stops"][0]["distance_from_previous_stop_miles"] <= 500.0
    assert result["stops"][1]["distance_from_previous_stop_miles"] <= 500.0

def test_no_feasible_station():
    service = RouteOptimizationService()
    stations = [
        create_station(600.0, 3.0)  # Unreachable
    ]
    with pytest.raises(RouteOptimizationError):
        service.optimize_fuel_stops(
            total_distance=1000.0,
            stations_on_route=stations,
            tank_capacity=50.0,
            mpg=10.0,
            max_range=500.0
        )

def test_fuel_cost_calculation():
    service = RouteOptimizationService()
    stations = [create_station(400.0, 3.0)]
    result = service.optimize_fuel_stops(
        total_distance=700.0,
        stations_on_route=stations,
        tank_capacity=50.0,
        mpg=10.0,
        max_range=500.0
    )
    stop = result["stops"][0]
    expected_cost = round(stop["gallons_purchased"] * stop["price_per_gallon"], 2)
    assert stop["cost"] == expected_cost

def test_full_tank_not_charged():
    service = RouteOptimizationService()
    stations = [create_station(400.0, 3.0)]
    result = service.optimize_fuel_stops(
        total_distance=700.0,
        stations_on_route=stations,
        tank_capacity=50.0,
        mpg=10.0,
        max_range=500.0
    )
    assert result["initial_fuel"] == 50.0
    # They should only buy what they need
    assert result["total_gallons_purchased"] < 50.0
