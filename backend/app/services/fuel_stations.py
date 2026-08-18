import math
import pandas as pd
from typing import List, Optional
from dataclasses import dataclass

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
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def point_to_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    # Uses haversine for small distances
    # A simplified projection is fine for corridor checking
    
    l2 = (bx - ax)**2 + (by - ay)**2
    if l2 == 0:
        return haversine(py, px, ay, ax)
        
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / l2))
    proj_x = ax + t * (bx - ax)
    proj_y = ay + t * (by - ay)
    return haversine(py, px, proj_y, proj_x)

def project_point_on_polyline(px: float, py: float, polyline: List[List[float]]) -> float:
    # polyline is list of [lng, lat]
    min_dist = float('inf')
    best_mile = 0.0
    cumulative_miles = 0.0
    
    for i in range(len(polyline) - 1):
        ax, ay = polyline[i]
        bx, by = polyline[i + 1]
        
        seg_dist = point_to_segment_distance(px, py, ax, ay, bx, by)
        
        if seg_dist < min_dist:
            min_dist = seg_dist
            
            # calculate where it projects
            l2 = (bx - ax)**2 + (by - ay)**2
            if l2 == 0:
                t = 0
            else:
                t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / l2))
            
            segment_length = haversine(ay, ax, by, bx)
            best_mile = cumulative_miles + (t * segment_length)
            
        segment_length = haversine(ay, ax, by, bx)
        cumulative_miles += segment_length
        
    return best_mile

class FuelStationService:
    def __init__(self):
        self.stations: List[Station] = []
        
    def load_stations(self, csv_path: str):
        df = pd.read_csv(csv_path)
        self.stations = []
        for _, row in df.iterrows():
            # Skip if NaN coords
            if pd.isna(row.get('latitude')) or pd.isna(row.get('longitude')):
                continue
                
            self.stations.append(Station(
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

    def find_stations_near_route(self, route_coordinates: List[List[float]], corridor_miles: float) -> List[StationOnRoute]:
        if not self.stations or not route_coordinates:
            return []
            
        # Step 1: Precompute cumulative miles for route polyline
        # route_coordinates is List of [lng, lat]
        n_points = len(route_coordinates)
        cumulative_miles = [0.0] * n_points
        for i in range(n_points - 1):
            ax, ay = route_coordinates[i]
            bx, by = route_coordinates[i + 1]
            seg_len = haversine(ay, ax, by, bx)
            cumulative_miles[i + 1] = cumulative_miles[i] + seg_len
            
        # Step 2: Global bounding box filter (+/- corridor converted to rough degrees)
        # 1 deg latitude ≈ 69 miles; 1 deg longitude at 40N ≈ 53 miles
        deg_pad = (corridor_miles / 50.0) + 0.1
        
        lngs = [c[0] for c in route_coordinates]
        lats = [c[1] for c in route_coordinates]
        min_lng, max_lng = min(lngs) - deg_pad, max(lngs) + deg_pad
        min_lat, max_lat = min(lats) - deg_pad, max(lats) + deg_pad
        
        filtered_stations = [
            s for s in self.stations 
            if min_lng <= s.longitude <= max_lng and min_lat <= s.latitude <= max_lat
        ]
        
        # Step 3: Segment bounding box optimization
        # Subsample segments or check bounding boxes for fast pruning
        # Precompute segment bounding boxes
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
                # Fast AABB rejection
                if sx < s_min_x or sx > s_max_x or sy < s_min_y or sy > s_max_y:
                    continue
                    
                # Projection parameter t
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
