import httpx
from typing import Dict, Any
from app.config import get_settings

class RoutingError(Exception):
    pass

class RoutingService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.settings = get_settings()

    async def get_route(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> Dict[str, Any]:
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false"
        }
        
        base_urls = [self.settings.OSRM_BASE_URL]
        if self.settings.OSRM_BASE_URL.startswith("https://"):
            base_urls.append(self.settings.OSRM_BASE_URL.replace("https://", "http://"))
        elif self.settings.OSRM_BASE_URL.startswith("http://"):
            base_urls.append(self.settings.OSRM_BASE_URL.replace("http://", "https://"))
            
        last_err = None
        for base in base_urls:
            url = f"{base}/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"
            try:
                response = await self.client.get(url, params=params, timeout=12.0)
                if response.status_code != 200:
                    last_err = f"OSRM returned status code {response.status_code}"
                    continue
                    
                data = response.json()
                if data.get("code") != "Ok" or not data.get("routes"):
                    raise RoutingError("OSRM could not find a driving route between these locations.")
                    
                route = data["routes"][0]
                
                # Meters to miles
                distance_miles = route["distance"] * 0.000621371
                # Seconds to minutes
                duration_minutes = route["duration"] / 60.0
                
                return {
                    "distance_miles": round(distance_miles, 2),
                    "duration_minutes": round(duration_minutes, 1),
                    "geometry": route["geometry"]
                }
            except RoutingError:
                raise
            except Exception as e:
                last_err = str(e)
                continue
                
        raise RoutingError(f"Failed to calculate route: {last_err}")
