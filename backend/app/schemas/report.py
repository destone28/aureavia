from pydantic import BaseModel
from datetime import datetime


class DashboardKPIs(BaseModel):
    total_rides: int
    active_drivers: int
    total_revenue: float
    avg_rating: float
    rides_today: int = 0
    rides_change_pct: float = 0.0
    revenue_change_pct: float = 0.0


class EarningsDataPoint(BaseModel):
    date: str
    amount: float


class EarningsReport(BaseModel):
    granularity: str  # daily, weekly, monthly
    data: list[EarningsDataPoint]


class RideExportRow(BaseModel):
    ride_id: str
    external_id: str | None
    date: str
    time: str
    pickup: str
    dropoff: str
    driver_name: str | None
    passenger_name: str | None
    distance_km: float | None
    duration_min: int | None
    price: float | None
    driver_share: float | None
    status: str
    source_platform: str
