import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OSRM_BASE_URL: str = "http://router.project-osrm.org"
    CENSUS_GEOCODER_URL: str = "https://geocoding.geo.census.gov/geocoder"
    ROUTE_CORRIDOR_MILES: float = 25.0
    MAX_RANGE_MILES: float = 500.0
    MPG: float = 10.0
    TANK_CAPACITY_GALLONS: float = 50.0
    FUEL_DATA_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed_fuel_prices.csv")
    ORIGINAL_CSV_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fuel-prices-for-be-assessment.csv")
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org/search"

    model_config = {"env_file": ".env", "extra": "ignore"}

@lru_cache()
def get_settings() -> Settings:
    return Settings()
