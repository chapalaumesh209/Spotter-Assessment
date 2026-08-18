from typing import List, Optional
from pydantic import BaseModel, Field

class RouteRequest(BaseModel):
    start: str = Field(..., description="Start location address")
    finish: str = Field(..., description="Finish location address")

class Location(BaseModel):
    address: str
    latitude: float
    longitude: float

class Vehicle(BaseModel):
    max_range_miles: float
    mpg: float
    tank_capacity_gallons: float

class RouteGeometry(BaseModel):
    type: str = "LineString"
    coordinates: List[List[float]]

class RouteInfo(BaseModel):
    distance_miles: float
    duration_minutes: float
    geometry: RouteGeometry

class FuelSummary(BaseModel):
    total_fuel_consumed: float
    total_gallons_purchased: float
    total_cost: float
    initial_fuel_gallons: float
    ending_fuel_gallons: float

class FuelStop(BaseModel):
    station_name: str
    address: str
    city: str
    state: str
    price_per_gallon: float
    latitude: float
    longitude: float
    route_mile: float
    distance_from_previous_stop_miles: float
    gallons_purchased: float
    cost: float

class RouteResponse(BaseModel):
    start: Location
    finish: Location
    vehicle: Vehicle
    route: RouteInfo
    fuel: FuelSummary
    fuel_stops: List[FuelStop]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
