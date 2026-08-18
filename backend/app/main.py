from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router, fuel_station_service
from app.config import get_settings
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if os.path.exists(settings.FUEL_DATA_PATH):
        fuel_station_service.load_stations(settings.FUEL_DATA_PATH)
    else:
        print(f"Warning: Fuel data not found at {settings.FUEL_DATA_PATH}")
    yield
    # Cleanup

app = FastAPI(
    title="Fuel-Optimal Route Planner API",
    description="Calculates optimal routes and fuel stops across the USA",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Fuel-Optimal Route Planner API"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )
