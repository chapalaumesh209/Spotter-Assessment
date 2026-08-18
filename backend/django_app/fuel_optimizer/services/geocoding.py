import requests
from typing import Tuple, Optional, Dict
from django.conf import settings

class GeocodingError(Exception):
    pass

class GeocodingService:
    # Class-level cache for instant lookup across requests
    _cache: Dict[str, Tuple[float, float]] = {}

    def __init__(self, timeout: float = 6.0):
        self.timeout = timeout
        self.census_url = getattr(settings, 'CENSUS_GEOCODER_URL', 'https://geocoding.geo.census.gov/geocoder')
        self.nominatim_url = getattr(settings, 'NOMINATIM_URL', 'https://nominatim.openstreetmap.org/search')

    def geocode(self, address: str) -> Tuple[float, float]:
        norm_address = address.strip()
        if norm_address in self._cache:
            return self._cache[norm_address]

        # 1. Try US Census Geocoder first
        result = self._census_geocode(norm_address)
        
        # 2. Fallback to Nominatim if needed
        if not result:
            result = self._nominatim_geocode(norm_address)

        if not result:
            raise GeocodingError(f"Could not geocode address: {address}")

        lat, lng = result
        if not self.validate_usa(lat, lng):
            raise GeocodingError(f"Address is outside USA boundaries: {address}")

        self._cache[norm_address] = result
        return result

    def _census_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        try:
            url = f"{self.census_url}/locations/onelineaddress"
            params = {
                "address": address,
                "benchmark": "Public_AR_Current",
                "format": "json"
            }
            resp = requests.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("result", {}).get("addressMatches", [])
                if matches:
                    coords = matches[0]["coordinates"]
                    return float(coords["y"]), float(coords["x"])
        except Exception:
            pass
        return None

    def _nominatim_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        try:
            params = {
                "q": address,
                "format": "json",
                "countrycodes": "us",
                "limit": "1"
            }
            headers = {"User-Agent": "DjangoFuelRoutePlanner/1.0"}
            resp = requests.get(self.nominatim_url, params=params, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            pass
        return None

    @staticmethod
    def validate_usa(lat: float, lng: float) -> bool:
        # Continental US Bounding Box
        if (24.5 <= lat <= 49.4) and (-124.8 <= lng <= -66.9):
            return True
        # Alaska
        if (51.0 <= lat <= 71.0) and (-180.0 <= lng <= -129.0):
            return True
        # Hawaii
        if (18.0 <= lat <= 23.0) and (-161.0 <= lng <= -154.0):
            return True
        return False
