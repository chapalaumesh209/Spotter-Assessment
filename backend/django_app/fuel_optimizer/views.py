from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .serializers import RouteRequestSerializer
from .services.geocoding import GeocodingService, GeocodingError
from .services.routing import RoutingService, RoutingError
from .services.fuel_stations import FuelStationService
from .services.optimization import RouteOptimizationService, RouteOptimizationError

class RouteCalculateView(APIView):
    """
    POST /api/v1/route
    Calculates driving route, identifies corridor stations, and optimizes fuel stops.
    Makes EXACTLY ONE single HTTP call to the routing API per calculation.
    """
    def post(self, request, *args, **kwargs):
        serializer = RouteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_address = serializer.validated_data['start']
        finish_address = serializer.validated_data['finish']

        geocoding_service = GeocodingService()
        routing_service = RoutingService()
        fuel_station_service = FuelStationService.get_instance()
        optimization_service = RouteOptimizationService()

        # 1. Geocode start and finish
        try:
            start_lat, start_lng = geocoding_service.geocode(start_address)
            finish_lat, finish_lng = geocoding_service.geocode(finish_address)
        except GeocodingError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Get driving route via OSRM (Exactly 1 single external call)
        try:
            route_data = routing_service.get_route(start_lat, start_lng, finish_lat, finish_lng)
        except RoutingError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        route_coords = route_data["geometry"]["coordinates"]
        distance_miles = route_data["distance_miles"]
        duration_minutes = route_data["duration_minutes"]

        # 3. Spatial corridor filtering & mileage projection (<10ms)
        stations_near_route = fuel_station_service.find_stations_near_route(
            route_coordinates=route_coords,
            corridor_miles=settings.ROUTE_CORRIDOR_MILES
        )

        # 4. Greedy look-ahead fuel stop optimization (<1ms)
        try:
            opt_result = optimization_service.optimize_fuel_stops(
                total_distance=distance_miles,
                stations_on_route=stations_near_route,
                tank_capacity=settings.TANK_CAPACITY_GALLONS,
                mpg=settings.MPG,
                max_range=settings.MAX_RANGE_MILES
            )
        except RouteOptimizationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Format response payload
        total_fuel_consumed = round(distance_miles / settings.MPG, 2)

        response_payload = {
            "start": {
                "address": start_address,
                "latitude": round(start_lat, 6),
                "longitude": round(start_lng, 6)
            },
            "finish": {
                "address": finish_address,
                "latitude": round(finish_lat, 6),
                "longitude": round(finish_lng, 6)
            },
            "vehicle": {
                "max_range_miles": settings.MAX_RANGE_MILES,
                "mpg": settings.MPG,
                "tank_capacity_gallons": settings.TANK_CAPACITY_GALLONS
            },
            "route": {
                "distance_miles": distance_miles,
                "duration_minutes": duration_minutes,
                "geometry": route_data["geometry"]
            },
            "fuel": {
                "total_fuel_consumed": total_fuel_consumed,
                "total_gallons_purchased": opt_result["total_gallons_purchased"],
                "total_cost": opt_result["total_cost"],
                "initial_fuel_gallons": opt_result["initial_fuel"],
                "ending_fuel_gallons": opt_result["ending_fuel"]
            },
            "fuel_stops": opt_result["stops"]
        }

        return Response(response_payload, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """
    GET /api/v1/health or GET /
    """
    def get(self, request, *args, **kwargs):
        station_count = len(FuelStationService.get_instance().stations)
        return Response({
            "status": "healthy",
            "message": "Fuel-Optimal Route Planner Django API is running.",
            "loaded_fuel_stations": station_count
        }, status=status.HTTP_200_OK)
