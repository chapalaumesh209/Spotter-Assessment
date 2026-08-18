from django.test import TestCase
from fuel_optimizer.services.optimization import RouteOptimizationService, RouteOptimizationError
from fuel_optimizer.services.fuel_stations import StationOnRoute, Station

def create_station(route_mile: float, price: float) -> StationOnRoute:
    return StationOnRoute(
        station=Station(
            opis_id=1, name="Test Station", address="123 Highway", city="City", state="ST",
            rack_id=1, price=price, latitude=40.0, longitude=-80.0
        ),
        route_mile=route_mile,
        distance_from_route=0.5
    )

class RouteOptimizationTestCase(TestCase):
    def setUp(self):
        self.service = RouteOptimizationService()

    def test_short_route_no_stops(self):
        """Test 1 — Short route (< 500 miles): 0 stops required, starting fuel not charged."""
        result = self.service.optimize_fuel_stops(
            total_distance=300.0,
            stations_on_route=[],
            tank_capacity=50.0,
            mpg=10.0,
            max_range=500.0
        )
        self.assertEqual(len(result["stops"]), 0)
        self.assertEqual(result["total_gallons_purchased"], 0.0)
        self.assertEqual(result["total_cost"], 0.0)
        self.assertEqual(result["ending_fuel"], 20.0)

    def test_medium_route_one_stop(self):
        """Test 2 — Medium route (500-1000 miles): At least one stop, no leg > 500 miles."""
        stations = [create_station(400.0, 3.25)]
        result = self.service.optimize_fuel_stops(
            total_distance=700.0,
            stations_on_route=stations,
            tank_capacity=50.0,
            mpg=10.0,
            max_range=500.0
        )
        self.assertEqual(len(result["stops"]), 1)
        self.assertEqual(result["stops"][0]["route_mile"], 400.0)
        self.assertLessEqual(result["stops"][0]["distance_from_previous_stop_miles"], 500.0)
        self.assertLessEqual(700.0 - 400.0, 500.0)

    def test_multiple_stops(self):
        """Test 3 — Multiple stops: 1500 miles trip requiring multiple reachable stops."""
        stations = [
            create_station(400.0, 3.50),
            create_station(850.0, 3.20),
            create_station(1300.0, 3.00)
        ]
        result = self.service.optimize_fuel_stops(
            total_distance=1500.0,
            stations_on_route=stations,
            tank_capacity=50.0,
            mpg=10.0,
            max_range=500.0
        )
        self.assertGreater(len(result["stops"]), 1)
        for stop in result["stops"]:
            self.assertLessEqual(stop["distance_from_previous_stop_miles"], 500.0)

    def test_cheapest_unreachable(self):
        """Test 4 — Cheapest station unreachable directly: algorithm picks reachable first."""
        stations = [
            create_station(400.0, 4.00),
            create_station(600.0, 2.00)  # Beyond initial 500-mile range
        ]
        result = self.service.optimize_fuel_stops(
            total_distance=800.0,
            stations_on_route=stations,
            tank_capacity=50.0,
            mpg=10.0,
            max_range=500.0
        )
        # First stop MUST be at 400 (reachable)
        self.assertEqual(result["stops"][0]["route_mile"], 400.0)
        self.assertLessEqual(result["stops"][0]["distance_from_previous_stop_miles"], 500.0)

    def test_no_feasible_station(self):
        """Test 5 — Gap > 500 miles with no reachable stations raises RouteOptimizationError."""
        stations = [create_station(600.0, 3.00)]  # First station at 600 miles
        with self.assertRaises(RouteOptimizationError):
            self.service.optimize_fuel_stops(
                total_distance=1000.0,
                stations_on_route=stations,
                tank_capacity=50.0,
                mpg=10.0,
                max_range=500.0
            )

    def test_fuel_cost_calculation(self):
        """Test 6 — Cost verification: cost = gallons_purchased * price_per_gallon."""
        stations = [create_station(400.0, 3.159)]
        result = self.service.optimize_fuel_stops(
            total_distance=700.0,
            stations_on_route=stations,
            tank_capacity=50.0,
            mpg=10.0,
            max_range=500.0
        )
        stop = result["stops"][0]
        expected_cost = round(stop["gallons_purchased"] * stop["price_per_gallon"], 2)
        self.assertEqual(stop["cost"], expected_cost)

    def test_full_tank_not_charged(self):
        """Test 7 — Full tank starting assumption: initial 50 gal not in total purchased cost."""
        stations = [create_station(400.0, 3.00)]
        result = self.service.optimize_fuel_stops(
            total_distance=700.0,
            stations_on_route=stations,
            tank_capacity=50.0,
            mpg=10.0,
            max_range=500.0
        )
        self.assertEqual(result["initial_fuel"], 50.0)
        # For 700 miles, consumed is 70 gal. Initial is 50 gal. Purchased = 20 gal.
        self.assertAlmostEqual(result["total_gallons_purchased"], 20.0, places=1)
