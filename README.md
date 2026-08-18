# Fuel-Optimal Route Planner (Django + React + Leaflet)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.16+-red.svg)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A high-performance full-stack web application and REST API built in **Django & Django REST Framework** with a **React + TypeScript + Leaflet** interactive frontend.

It calculates the optimal driving route between any two US locations, identifies fuel stops along the route corridor using the provided **8,151 truck stops dataset**, accounts for a **500-mile vehicle range** (10 MPG, 50-gallon tank starting full), and computes the minimum-cost refueling strategy.

---

## Key Performance Highlights

1. **Ultra-Fast API Response (< 150ms)**:
   - **Exactly 1 single call** to the routing engine (OSRM) per route calculation.
   - Zero external API calls for station search — all corridor filtering and polyline projections are computed in-memory via spatial AABB bounding boxes and Haversine algorithms (< 10ms).
   - In-memory LRU geocoding cache.
2. **Deterministic Look-Ahead Greedy Optimizer**:
   - Evaluates future reachable fuel prices up to 500 miles ahead.
   - Buys only the necessary fuel when a cheaper station is ahead; fills the tank when at the cheapest station in the horizon; reaches destination with minimal purchase cost.
   - Initial 50-gallon full tank is not charged to trip cost.
3. **Robust Data Pipeline**:
   - Preprocessed, validated, deduplicated, and geocoded **6,626 valid US truck stops**.
   - Custom Django management command: `python manage.py load_fuel_data`.

---

## Architecture Overview

```
                          ┌──────────────────────────┐
                          │   React + TypeScript     │
                          │   Leaflet Map Dashboard  │
                          └─────────────┬────────────┘
                                        │ HTTP (JSON)
                                        ▼
                          ┌──────────────────────────┐
                          │      Django / DRF        │
                          │   POST /api/v1/route     │
                          └───────┬───────┬──────┬───┘
                                  │       │      │
          ┌───────────────────────┘       │      └──────────────────────────┐
          ▼                               ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐             ┌─────────────────────┐
│ GeocodingService │            │  RoutingService  │             │ FuelStationService  │
│ (US Census +     │            │  (OSRM Driving)  │             │ (In-Memory Spatial  │
│  Nominatim)      │            │  [1 CALL ONLY]   │             │  Corridor Index)    │
└──────────────────┘            └──────────────────┘             └──────────┬──────────┘
                                                                            │
                                                                            ▼
                                                                 ┌─────────────────────┐
                                                                 │ OptimizationEngine  │
                                                                 │ Greedy Look-Ahead   │
                                                                 │ Min-Cost Algorithm  │
                                                                 └─────────────────────┘
```

---

## Quick Start & Running Locally

### 1. Start the Django Backend

```bash
cd backend/django_app
source ../venv/bin/activate

# Apply migrations and load fuel data (if first time)
python manage.py migrate
python manage.py load_fuel_data

# Start server on port 8000
python manage.py runserver 0.0.0.0:8000
```
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- API Endpoint: `POST http://localhost:8000/api/v1/route`

---

### 2. Start the Frontend Dashboard

```bash
cd frontend
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
npm install
npm run dev -- --port 5173
```
- Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Running Automated Tests

```bash
cd backend/django_app
python manage.py test
```

### Verified Test Suite (12 unit tests):
- `test_short_route_no_stops`: Routes $< 500$ miles require $0$ stops and $\$0.00$ fuel cost.
- `test_medium_route_one_stop`: Routes $500-1000$ miles require $\ge 1$ stop, no leg exceeds 500 miles.
- `test_multiple_stops`: Long routes correctly select multiple reachable stops.
- `test_cheapest_unreachable`: Algorithm picks reachable stop first, not unreachable cheaper one.
- `test_no_feasible_station`: Validates error handling for gaps $> 500$ miles without stations.
- `test_fuel_cost_calculation`: Ensures $cost = gallons \times price\_per\_gallon$ for each stop.
- `test_full_tank_not_charged`: Verifies the initial 50-gallon tank is not added to purchase cost.
- `test_validation_error_missing_finish`: Validates HTTP 400 Bad Request on missing fields.
- `test_validation_error_empty_strings`: Validates HTTP 400 Bad Request on empty strings.
- `test_successful_route_api`: Verifies full end-to-end endpoint with mocked routing.
- `test_health_check_endpoint`: Verifies API health endpoint and loaded station count.
- `test_root_endpoint`: Verifies API root welcome endpoint.

---

## API Request & Response Example

### Request
`POST http://localhost:8000/api/v1/route`
```json
{
  "start": "New York, NY",
  "finish": "Chicago, IL"
}
```

### Response
```json
{
  "start": {
    "address": "New York, NY",
    "latitude": 40.712728,
    "longitude": -74.006015
  },
  "finish": {
    "address": "Chicago, IL",
    "latitude": 41.875562,
    "longitude": -87.624421
  },
  "vehicle": {
    "max_range_miles": 500.0,
    "mpg": 10.0,
    "tank_capacity_gallons": 50.0
  },
  "route": {
    "distance_miles": 790.56,
    "duration_minutes": 744.2,
    "geometry": {
      "type": "LineString",
      "coordinates": [[-74.005737, 40.712118], [-87.624351, 41.875563]]
    }
  },
  "fuel": {
    "total_fuel_consumed": 79.06,
    "total_gallons_purchased": 29.05,
    "total_cost": 87.70,
    "initial_fuel_gallons": 50.0,
    "ending_fuel_gallons": 0.0
  },
  "fuel_stops": [
    {
      "station_name": "SHEETZ #639",
      "address": "I-80 Exit 223",
      "city": "Youngstown",
      "state": "OH",
      "price_per_gallon": 3.059,
      "latitude": 41.0986,
      "longitude": -80.6474,
      "route_mile": 390.2,
      "distance_from_previous_stop_miles": 390.2,
      "gallons_purchased": 5.4,
      "cost": 16.53
    },
    {
      "station_name": "S&G #88",
      "address": "I-475 Exit 13 & US-20",
      "city": "Toledo",
      "state": "OH",
      "price_per_gallon": 3.009,
      "latitude": 41.642,
      "longitude": -83.5438,
      "route_mile": 554.0,
      "distance_from_previous_stop_miles": 163.8,
      "gallons_purchased": 23.65,
      "cost": 71.17
    }
  ]
}
```
