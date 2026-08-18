from typing import List, Dict, Any
from .fuel_stations import StationOnRoute

class RouteOptimizationError(Exception):
    pass

class RouteOptimizationService:
    """
    Greedy Look-Ahead Minimum-Cost Fueling Algorithm.
    Respects vehicle range (500 miles max range, 10 MPG, 50 gallon tank).
    Vehicle starts with a full tank (50 gallons) which is not charged to total_cost.
    """
    def optimize_fuel_stops(
        self,
        total_distance: float,
        stations_on_route: List[StationOnRoute],
        tank_capacity: float = 50.0,
        mpg: float = 10.0,
        max_range: float = 500.0
    ) -> Dict[str, Any]:

        current_fuel = tank_capacity
        current_mile = 0.0
        stops = []
        stations = list(stations_on_route)

        while current_mile + (current_fuel * mpg) < total_distance:
            remaining_range = current_fuel * mpg
            max_reachable_mile = current_mile + remaining_range

            reachable = [s for s in stations if current_mile < s.route_mile <= max_reachable_mile]

            if not reachable:
                raise RouteOptimizationError("No feasible fuel plan: distance between fuel stations exceeds maximum range of 500 miles.")

            cheapest = min(reachable, key=lambda s: s.station.price)

            distance_to_cheapest = cheapest.route_mile - current_mile
            fuel_to_reach = distance_to_cheapest / mpg
            fuel_at_cheapest = current_fuel - fuel_to_reach

            max_from_cheapest = cheapest.route_mile + (tank_capacity * mpg)
            future_stations = [s for s in stations if cheapest.route_mile < s.route_mile <= max_from_cheapest]
            cheaper_ahead = [s for s in future_stations if s.station.price < cheapest.station.price]

            if cheaper_ahead:
                # Buy just enough fuel at cheapest to reach the next even cheaper station
                target = min(cheaper_ahead, key=lambda s: s.station.price)
                distance_to_target = target.route_mile - cheapest.route_mile
                fuel_needed = distance_to_target / mpg
                gallons_to_buy = max(0.0, fuel_needed - fuel_at_cheapest)
            elif cheapest.route_mile + (tank_capacity * mpg) >= total_distance:
                # Can reach destination directly from here - buy only what is strictly needed
                remaining_distance = total_distance - cheapest.route_mile
                fuel_needed = remaining_distance / mpg
                gallons_to_buy = max(0.0, fuel_needed - fuel_at_cheapest)
            else:
                # Fill up completely since this is the cheapest station in the 500-mile horizon
                gallons_to_buy = tank_capacity - fuel_at_cheapest

            gallons_to_buy = min(gallons_to_buy, tank_capacity - fuel_at_cheapest)
            gallons_to_buy = max(0.0, gallons_to_buy)

            if gallons_to_buy > 0.0:
                cost = round(gallons_to_buy * cheapest.station.price, 2)
                stops.append({
                    "station_name": cheapest.station.name,
                    "address": cheapest.station.address,
                    "city": cheapest.station.city,
                    "state": cheapest.station.state,
                    "price_per_gallon": round(cheapest.station.price, 3),
                    "latitude": round(cheapest.station.latitude, 6),
                    "longitude": round(cheapest.station.longitude, 6),
                    "route_mile": round(cheapest.route_mile, 1),
                    "distance_from_previous_stop_miles": round(distance_to_cheapest, 1),
                    "gallons_purchased": round(gallons_to_buy, 2),
                    "cost": cost
                })

            current_fuel = fuel_at_cheapest + gallons_to_buy
            current_mile = cheapest.route_mile

            stations = [s for s in stations if s.route_mile > current_mile]

        ending_fuel = current_fuel - ((total_distance - current_mile) / mpg)
        total_gallons_purchased = sum(s["gallons_purchased"] for s in stops)
        total_cost = sum(s["cost"] for s in stops)

        return {
            "stops": stops,
            "total_gallons_purchased": round(total_gallons_purchased, 2),
            "total_cost": round(total_cost, 2),
            "initial_fuel": tank_capacity,
            "ending_fuel": round(max(0.0, ending_fuel), 2)
        }
