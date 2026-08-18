export interface RouteResponse {
  start: Location;
  finish: Location;
  vehicle: Vehicle;
  route: RouteInfo;
  fuel: FuelSummary;
  fuel_stops: FuelStop[];
}

export interface Location {
  address: string;
  latitude: number;
  longitude: number;
}

export interface Vehicle {
  max_range_miles: number;
  mpg: number;
  tank_capacity_gallons: number;
}

export interface RouteInfo {
  distance_miles: number;
  duration_minutes: number;
  geometry: { type: string; coordinates: number[][] };
}

export interface FuelSummary {
  total_fuel_consumed: number;
  total_gallons_purchased: number;
  total_cost: number;
  initial_fuel_gallons: number;
  ending_fuel_gallons: number;
}

export interface FuelStop {
  station_name: string;
  address: string;
  city: string;
  state: string;
  price_per_gallon: number;
  latitude: number;
  longitude: number;
  route_mile: number;
  distance_from_previous_stop_miles: number;
  gallons_purchased: number;
  cost: number;
}
