import requests
from typing import Dict, Any
from django.conf import settings

class RoutingError(Exception):
    pass

class RoutingService:
    """
    Connects to OSRM (Open Source Routing Machine) driving API.
    Makes EXACTLY ONE single HTTP call per route calculation.
    """
    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        self.base_url = getattr(settings, 'OSRM_BASE_URL', 'http://router.project-osrm.org')

    def get_route(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> Dict[str, Any]:
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false"
        }
        
        base_urls = [self.base_url]
        if self.base_url.startswith("https://"):
            base_urls.append(self.base_url.replace("https://", "http://"))
        elif self.base_url.startswith("http://"):
            base_urls.append(self.base_url.replace("http://", "https://"))

        last_error = None
        for base in base_urls:
            url = f"{base}/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code != 200:
                    last_error = f"OSRM returned status {resp.status_code}"
                    continue

                data = resp.json()
                if data.get("code") != "Ok" or not data.get("routes"):
                    raise RoutingError("OSRM could not find a driving route between these locations.")

                route = data["routes"][0]
                distance_miles = route["distance"] * 0.000621371
                duration_minutes = route["duration"] / 60.0

                return {
                    "distance_miles": round(distance_miles, 2),
                    "duration_minutes": round(duration_minutes, 1),
                    "geometry": route["geometry"]
                }
            except RoutingError:
                raise
            except Exception as e:
                last_error = str(e)
                continue

        raise RoutingError(f"Failed to calculate route from routing engine: {last_error}")
