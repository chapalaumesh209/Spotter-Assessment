from fastapi import APIRouter, HTTPException, Depends
import httpx
from app.models.schemas import RouteRequest, RouteResponse, Location, Vehicle, RouteInfo, RouteGeometry, FuelSummary, FuelStop
from app.services.geocoding import GeocodingService, GeocodingError
from app.services.routing import RoutingService, RoutingError
from app.services.fuel_stations import FuelStationService
from app.services.optimization import RouteOptimizationService, RouteOptimizationError
from app.config import get_settings

router = APIRouter(prefix="/api/v1")

# We'll use a global instance for FuelStationService to keep it in memory
fuel_station_service = FuelStationService()

async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client

@router.post("/route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest, client: httpx.AsyncClient = Depends(get_http_client)):
    settings = get_settings()
    geocoding_service = GeocodingService(client)
    routing_service = RoutingService(client)
    optimization_service = RouteOptimizationService()

    try:
        start_lat, start_lng = await geocoding_service.geocode(request.start)
        finish_lat, finish_lng = await geocoding_service.geocode(request.finish)
    except GeocodingError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        route_data = await routing_service.get_route(start_lat, start_lng, finish_lat, finish_lng)
    except RoutingError as e:
        raise HTTPException(status_code=400, detail=str(e))

    route_coordinates = route_data["geometry"]["coordinates"]
    distance_miles = route_data["distance_miles"]
    
    stations_near_route = fuel_station_service.find_stations_near_route(
        route_coordinates=route_coordinates,
        corridor_miles=settings.ROUTE_CORRIDOR_MILES
    )

    try:
        optimization_result = optimization_service.optimize_fuel_stops(
            total_distance=distance_miles,
            stations_on_route=stations_near_route,
            tank_capacity=settings.TANK_CAPACITY_GALLONS,
            mpg=settings.MPG,
            max_range=settings.MAX_RANGE_MILES
        )
    except RouteOptimizationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    vehicle = Vehicle(
        max_range_miles=settings.MAX_RANGE_MILES,
        mpg=settings.MPG,
        tank_capacity_gallons=settings.TANK_CAPACITY_GALLONS
    )
    
    route_info = RouteInfo(
        distance_miles=distance_miles,
        duration_minutes=route_data["duration_minutes"],
        geometry=RouteGeometry(coordinates=route_coordinates)
    )

    fuel_summary = FuelSummary(
        total_fuel_consumed=distance_miles / settings.MPG,
        total_gallons_purchased=optimization_result["total_gallons_purchased"],
        total_cost=optimization_result["total_cost"],
        initial_fuel_gallons=optimization_result["initial_fuel"],
        ending_fuel_gallons=optimization_result["ending_fuel"]
    )

    fuel_stops = [FuelStop(**stop) for stop in optimization_result["stops"]]

    return RouteResponse(
        start=Location(address=request.start, latitude=start_lat, longitude=start_lng),
        finish=Location(address=request.finish, latitude=finish_lat, longitude=finish_lng),
        vehicle=vehicle,
        route=route_info,
        fuel=fuel_summary,
        fuel_stops=fuel_stops
    )
