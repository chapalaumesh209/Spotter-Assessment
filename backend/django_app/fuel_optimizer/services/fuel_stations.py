import math
import os
import pandas as pd
from typing import List, Optional
from dataclasses import dataclass
from django.conf import settings

@dataclass
class Station:
    opis_id: int
    name: str
    address: str
    city: str
    state: str
    rack_id: int
    price: float
    latitude: float
    longitude: float

@dataclass
class StationOnRoute:
    station: Station
    route_mile: float
    distance_from_route: float

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

class FuelStationService:
    _instance: Optional['FuelStationService'] = None
    
    def __init__(self):
        self.stations: List[Station] = []
        self._load_default_stations()

    @classmethod
    def get_instance(cls) -> 'FuelStationService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_default_stations(self):
        csv_path = getattr(settings, 'PROCESSED_DATA_PATH', None)
        if csv_path and os.path.exists(csv_path):
            self.load_stations(csv_path)

    def load_stations(self, csv_path: str):
        df = pd.read_csv(csv_path)
        stations = []
        for _, row in df.iterrows():
            if pd.isna(row.get('latitude')) or pd.isna(row.get('longitude')):
                continue
            stations.append(Station(
                opis_id=int(row['OPIS Truckstop ID']),
                name=str(row['Truckstop Name']),
                address=str(row['Address']),
                city=str(row['City']),
                state=str(row['State']),
                rack_id=int(row.get('Rack ID', 0)),
                price=float(row['Retail Price']),
                latitude=float(row['latitude']),
                longitude=float(row['longitude'])
            ))
        self.stations = stations

    def find_stations_near_route(self, route_coordinates: List[List[float]], corridor_miles: float) -> List[StationOnRoute]:
        """
        High-performance sub-10ms spatial filtering & cumulative mileage projection.
        route_coordinates: list of [lng, lat] GeoJSON coordinates.
        """
        if not self.stations or not route_coordinates:
            return []

        n_points = len(route_coordinates)
        cumulative_miles = [0.0] * n_points
        for i in range(n_points - 1):
            ax, ay = route_coordinates[i]
            bx, by = route_coordinates[i + 1]
            seg_len = haversine(ay, ax, by, bx)
            cumulative_miles[i + 1] = cumulative_miles[i] + seg_len

        deg_pad = (corridor_miles / 50.0) + 0.1
        lngs = [c[0] for c in route_coordinates]
        lats = [c[1] for c in route_coordinates]
        min_lng, max_lng = min(lngs) - deg_pad, max(lngs) + deg_pad
        min_lat, max_lat = min(lats) - deg_pad, max(lats) + deg_pad

        filtered_stations = [
            s for s in self.stations 
            if min_lng <= s.longitude <= max_lng and min_lat <= s.latitude <= max_lat
        ]

        seg_boxes = []
        for i in range(n_points - 1):
            ax, ay = route_coordinates[i]
            bx, by = route_coordinates[i + 1]
            s_min_x = min(ax, bx) - deg_pad
            s_max_x = max(ax, bx) + deg_pad
            s_min_y = min(ay, by) - deg_pad
            s_max_y = max(ay, by) + deg_pad
            seg_boxes.append((s_min_x, s_max_x, s_min_y, s_max_y, ax, ay, bx, by, i))

        result = []
        for station in filtered_stations:
            sx, sy = station.longitude, station.latitude
            min_dist = float('inf')
            best_mile = 0.0

            for s_min_x, s_max_x, s_min_y, s_max_y, ax, ay, bx, by, i in seg_boxes:
                if sx < s_min_x or sx > s_max_x or sy < s_min_y or sy > s_max_y:
                    continue

                dx = bx - ax
                dy = by - ay
                l2 = dx * dx + dy * dy
                if l2 == 0:
                    t = 0.0
                    proj_x, proj_y = ax, ay
                else:
                    t = max(0.0, min(1.0, ((sx - ax) * dx + (sy - ay) * dy) / l2))
                    proj_x = ax + t * dx
                    proj_y = ay + t * dy

                dist = haversine(sy, sx, proj_y, proj_x)
                if dist < min_dist:
                    min_dist = dist
                    seg_len = cumulative_miles[i + 1] - cumulative_miles[i]
                    best_mile = cumulative_miles[i] + (t * seg_len)

            if min_dist <= corridor_miles:
                result.append(StationOnRoute(station=station, route_mile=best_mile, distance_from_route=min_dist))

        result.sort(key=lambda x: x.route_mile)
        return result
