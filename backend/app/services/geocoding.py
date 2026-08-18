import httpx
from typing import Tuple, Dict, Optional
from app.config import get_settings

class GeocodingError(Exception):
    pass

class GeocodingService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.settings = get_settings()
        self.cache: Dict[str, Tuple[float, float]] = {}

    async def geocode(self, address: str) -> Tuple[float, float]:
        if address in self.cache:
            return self.cache[address]
        
        # Try Census first
        result = await self._census_geocode(address)
        if not result:
            # Fallback to Nominatim
            result = await self._nominatim_geocode(address)
            
        if not result:
            raise GeocodingError(f"Could not geocode address: {address}")
            
        lat, lng = result
        if not self.validate_usa(lat, lng):
            raise GeocodingError(f"Address is outside USA boundaries: {address}")
            
        self.cache[address] = result
        return result

    async def _census_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        try:
            url = f"{self.settings.CENSUS_GEOCODER_URL}/locations/onelineaddress"
            params = {
                "address": address,
                "benchmark": "Public_AR_Current",
                "format": "json"
            }
            response = await self.client.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                matches = data.get("result", {}).get("addressMatches", [])
                if matches:
                    coords = matches[0]["coordinates"]
                    return coords["y"], coords["x"]
        except Exception:
            pass
        return None

    async def _nominatim_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        try:
            url = self.settings.NOMINATIM_URL
            params = {
                "q": address,
                "format": "json",
                "countrycodes": "us",
                "limit": "1"
            }
            headers = {"User-Agent": "FuelRoutePlanner/1.0"}
            response = await self.client.get(url, params=params, headers=headers, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            pass
        return None

    def validate_usa(self, lat: float, lng: float) -> bool:
        # Continental US
        if (24.5 <= lat <= 49.4) and (-124.8 <= lng <= -66.9):
            return True
        # Alaska
        if (51.0 <= lat <= 71.0) and (-180.0 <= lng <= -129.0):
            return True
        # Hawaii
        if (18.0 <= lat <= 23.0) and (-161.0 <= lng <= -154.0):
            return True
        return False
