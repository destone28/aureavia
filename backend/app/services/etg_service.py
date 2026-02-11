"""ETG Transfers API business logic.

AureaVia is the SUPPLIER. ETG calls our 4 endpoints:
/search, /book, /status, /cancel.

This service handles pricing, fleet lookup, booking creation, and order management.
Schemas match the ETG Postman test collection (210 tests).
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.ride import Ride, RideStatus
from app.models.user import User, UserRole, UserStatus
from app.schemas.etg import (
    BookRequest,
    BookResponse,
    CancelPenalty,
    CancelResponse,
    DriverInfo,
    CarInfo,
    MeetingInfo,
    OrderStatus,
    PriceObj,
    SearchOffer,
    SearchRequest,
    SearchResponse,
    StatusResponse,
    TransferCategory,
)


class ETGServiceError(Exception):
    """Custom error for ETG service operations."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# --- Pricing Configuration ---

CATEGORY_PRICING: dict[TransferCategory, float] = {
    TransferCategory.MICRO: 0.80,
    TransferCategory.ECONOMY: 1.00,
    TransferCategory.ECONOMY_MPV: 1.20,
    TransferCategory.ECONOMY_VAN: 1.30,
    TransferCategory.STANDARD: 1.30,
    TransferCategory.STANDARD_MPV: 1.50,
    TransferCategory.STANDARD_VAN: 1.60,
    TransferCategory.BUSINESS: 1.80,
    TransferCategory.BUSINESS_MPV: 2.00,
    TransferCategory.BUSINESS_VAN: 2.10,
    TransferCategory.FIRST: 2.50,
    TransferCategory.FIRST_MPV: 2.70,
    TransferCategory.FIRST_VAN: 2.80,
    TransferCategory.LUXURY: 3.50,
    TransferCategory.LUXURY_MPV: 3.70,
    TransferCategory.LUXURY_VAN: 3.80,
    TransferCategory.MINIBUS: 2.00,
    TransferCategory.MINIBUS_LARGE: 2.50,
    TransferCategory.BUS: 3.00,
    TransferCategory.ELECTRO_ECONOMY: 1.10,
    TransferCategory.ELECTRO_STANDARD: 1.40,
    TransferCategory.ELECTRO_BUSINESS: 1.90,
    TransferCategory.ELECTRO_FIRST: 2.60,
    TransferCategory.ELECTRO_LUXURY: 3.60,
    TransferCategory.ELECTRO_MINIBUS: 2.10,
    TransferCategory.ELECTRO_BUS: 3.10,
}

MIN_FARE: dict[TransferCategory, float] = {
    cat: max(15.0, price * 10) for cat, price in CATEGORY_PRICING.items()
}

CHILD_SEAT_PRICE = 5.0


def _classify_vehicle(driver: Driver) -> list[TransferCategory]:
    """Determine which ETG categories a driver's vehicle qualifies for."""
    categories: list[TransferCategory] = []
    seats = driver.vehicle_seats or 4
    make = (driver.vehicle_make or "").lower()
    model = (driver.vehicle_model or "").lower()
    fuel = (driver.vehicle_fuel_type or "").lower()

    is_electric = fuel in ("electric", "ev", "bev", "elettrico")
    is_luxury = any(b in make for b in ("mercedes", "bmw", "audi", "lexus", "jaguar", "porsche", "maserati", "tesla"))
    is_premium = is_luxury or any(b in make for b in ("volvo", "alfa romeo", "alfa", "ds"))
    is_van = any(v in model for v in ("van", "vito", "sprinter", "transporter", "caravelle", "v-class", "classe v"))
    is_mpv = seats >= 6 and not is_van
    is_minibus = seats >= 8

    if is_minibus:
        if is_electric:
            categories.append(TransferCategory.ELECTRO_MINIBUS)
        if seats >= 16:
            categories.append(TransferCategory.MINIBUS_LARGE)
            categories.append(TransferCategory.BUS)
        categories.append(TransferCategory.MINIBUS)
    elif is_van:
        if is_electric:
            categories.append(TransferCategory.ELECTRO_BUSINESS)
        if is_luxury:
            categories.append(TransferCategory.LUXURY_VAN)
            categories.append(TransferCategory.FIRST_VAN)
        if is_premium:
            categories.append(TransferCategory.BUSINESS_VAN)
        categories.append(TransferCategory.STANDARD_VAN)
        categories.append(TransferCategory.ECONOMY_VAN)
    elif is_mpv:
        if is_electric:
            categories.append(TransferCategory.ELECTRO_BUSINESS)
        if is_luxury:
            categories.append(TransferCategory.LUXURY_MPV)
            categories.append(TransferCategory.FIRST_MPV)
        if is_premium:
            categories.append(TransferCategory.BUSINESS_MPV)
        categories.append(TransferCategory.STANDARD_MPV)
        categories.append(TransferCategory.ECONOMY_MPV)
    else:
        if is_electric:
            if is_luxury:
                categories.append(TransferCategory.ELECTRO_LUXURY)
                categories.append(TransferCategory.ELECTRO_FIRST)
            if is_premium:
                categories.append(TransferCategory.ELECTRO_BUSINESS)
            categories.append(TransferCategory.ELECTRO_STANDARD)
            categories.append(TransferCategory.ELECTRO_ECONOMY)
        if is_luxury:
            categories.append(TransferCategory.LUXURY)
            categories.append(TransferCategory.FIRST)
        if is_premium:
            categories.append(TransferCategory.BUSINESS)
        categories.append(TransferCategory.STANDARD)
        categories.append(TransferCategory.ECONOMY)
        if seats <= 3:
            categories.append(TransferCategory.MICRO)

    return categories


def _resolve_point_value(point: dict) -> str:
    """Extract the actual value from a PointRequest dict."""
    if point.get("iata"):
        return point["iata"]
    if point.get("coordinates"):
        return point["coordinates"]
    return point.get("value", "")


def _estimate_distance_km(start_point: dict, end_point: dict) -> float:
    """Estimate distance in km using Haversine formula."""
    import math

    def _parse_coords(point: dict) -> tuple[float, float] | None:
        val = _resolve_point_value(point)
        if val and "," in val:
            parts = val.split(",")
            if len(parts) == 2:
                try:
                    return float(parts[0]), float(parts[1])
                except ValueError:
                    return None
        return None

    start_coords = _parse_coords(start_point)
    end_coords = _parse_coords(end_point)

    if start_coords and end_coords:
        lat1, lon1 = math.radians(start_coords[0]), math.radians(start_coords[1])
        lat2, lon2 = math.radians(end_coords[0]), math.radians(end_coords[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return round(6371 * c * 1.3, 1)

    return 30.0


def _estimate_duration_min(distance_km: float) -> int:
    return max(15, int(distance_km / 40 * 60))


def _calculate_price(category: TransferCategory, distance_km: float, child_seat_count: int) -> float:
    base = CATEGORY_PRICING.get(category, 1.50) * distance_km
    minimum = MIN_FARE.get(category, 15.0)
    price = max(base, minimum)
    price += child_seat_count * CHILD_SEAT_PRICE
    return round(price, 2)


def _generate_offer_id(search_id: str, category: TransferCategory) -> str:
    raw = f"{search_id}:{category.value}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _generate_search_id() -> str:
    return uuid.uuid4().hex[:16]


def _generate_order_id() -> str:
    return f"AV{uuid.uuid4().hex[:13].upper()}"


# In-memory offer cache (search_id -> {offer_id -> offer_data})
_offer_cache: dict[str, dict] = {}


# --- Search ---

async def search_offers(request: SearchRequest, db: AsyncSession) -> SearchResponse:
    """Search available transfer offers based on fleet and pricing."""
    search_id = _generate_search_id()

    distance_km = _estimate_distance_km(
        request.start_point.model_dump(),
        request.end_point.model_dump(),
    )
    duration_min = _estimate_duration_min(distance_km)
    child_seats_total = request.children_seat_0 + request.children_seat_1 + request.children_seat_2 + request.children_seat_3

    # Query available drivers
    result = await db.execute(
        select(Driver)
        .join(User, Driver.user_id == User.id)
        .where(User.status == UserStatus.ACTIVE)
        .where(User.role == UserRole.DRIVER)
    )
    drivers = result.scalars().all()

    category_vehicles: dict[TransferCategory, list[Driver]] = {}
    for driver in drivers:
        if driver.vehicle_seats and driver.vehicle_seats >= request.passengers:
            for cat in _classify_vehicle(driver):
                category_vehicles.setdefault(cat, []).append(driver)

    offers: list[SearchOffer] = []
    free_cancel_dt = datetime.fromisoformat(request.start_date_time.replace("Z", "+00:00")) - timedelta(hours=24)
    free_cancel_str = free_cancel_dt.strftime("%Y-%m-%dT%H:%M:%S")

    offer_data: dict[str, dict] = {}

    for category, cat_drivers in sorted(category_vehicles.items(), key=lambda x: CATEGORY_PRICING.get(x[0], 0)):
        best = cat_drivers[0]
        price = _calculate_price(category, distance_km, child_seats_total)
        offer_id = _generate_offer_id(search_id, category)

        offer = SearchOffer(
            id=offer_id,
            service_type="transfer",
            transfer_category=category,
            car_model=f"{best.vehicle_make or ''} {best.vehicle_model or ''}".strip() or "Standard Vehicle",
            seats=best.vehicle_seats or 4,
            luggage_places=best.vehicle_luggage_capacity or 2,
            price=PriceObj(amount=price, currency="EUR"),
            included_waiting_time_minutes=60,
            tolls_included=True,
            gratuity_included=False,
            free_cancel_until=free_cancel_str,
            estimated_duration_minutes=duration_min,
            distance=distance_km,
        )
        offers.append(offer)

        # Cache offer data for booking
        offer_data[offer_id] = {
            "category": category.value,
            "car_model": offer.car_model,
            "price": price,
            "distance": distance_km,
            "duration": duration_min,
            "free_cancel_until": free_cancel_str,
            "start_date_time": request.start_date_time,
            "start_point": request.start_point.model_dump(),
            "end_point": request.end_point.model_dump(),
            "passengers": request.passengers,
            "seats": offer.seats,
            "luggage_places": offer.luggage_places,
        }

    # Cache for booking validation
    _offer_cache[search_id] = offer_data
    if len(_offer_cache) > 1000:
        oldest = next(iter(_offer_cache))
        del _offer_cache[oldest]

    return SearchResponse(
        start_date_time=request.start_date_time,
        offers=offers,
    )


# --- Book ---

async def book_transfer(request: BookRequest, db: AsyncSession) -> BookResponse:
    """Create a booking from an accepted offer."""
    # Find the offer in cache
    offer_data: dict | None = None
    cached_search_id: str | None = None
    for sid, offers in _offer_cache.items():
        if request.offer_id in offers:
            offer_data = offers[request.offer_id]
            cached_search_id = sid
            break

    if not offer_data:
        raise ETGServiceError("Invalid or expired offer_id. Please search again.", status_code=400)

    order_id = _generate_order_id()
    now = datetime.now(timezone.utc)

    start_dt = offer_data["start_date_time"]
    start_point = request.start_point.model_dump()
    end_point = request.end_point.model_dump()

    # Build addresses from points
    pickup_addr = _resolve_point_value(start_point) or "N/A"
    dropoff_addr = _resolve_point_value(end_point) or "N/A"

    ride = Ride(
        id=uuid.uuid4(),
        external_id=order_id,
        source_platform="etg",
        status=RideStatus.TO_ASSIGN,
        pickup_address=pickup_addr,
        dropoff_address=dropoff_addr,
        scheduled_at=datetime.fromisoformat(start_dt.replace("Z", "+00:00")),
        passenger_name=f"{request.main_passenger.first_name} {request.main_passenger.last_name}",
        passenger_phone=request.main_passenger.phone,
        passenger_count=request.passengers,
        distance_km=offer_data["distance"],
        duration_min=offer_data["duration"],
        price=Decimal(str(offer_data["price"])),
        notes=request.comment or None,
        flight_number=request.flight_number or None,
        booking_reference=order_id,
        booking_raw_payload={
            "offer_id": request.offer_id,
            "category": offer_data["category"],
            "passenger": request.main_passenger.model_dump(),
            "car_model": offer_data["car_model"],
        },
        created_at=now,
        updated_at=now,
    )

    # Parse coordinates if available
    start_val = _resolve_point_value(start_point)
    if start_val and "," in start_val:
        parts = start_val.split(",")
        if len(parts) == 2:
            try:
                ride.pickup_lat = Decimal(parts[0])
                ride.pickup_lng = Decimal(parts[1])
            except Exception:
                pass

    end_val = _resolve_point_value(end_point)
    if end_val and "," in end_val:
        parts = end_val.split(",")
        if len(parts) == 2:
            try:
                ride.dropoff_lat = Decimal(parts[0])
                ride.dropoff_lng = Decimal(parts[1])
            except Exception:
                pass

    db.add(ride)
    await db.flush()

    return BookResponse(
        order_id=order_id,
        supplier_link="",
        start_time=start_dt,
        distance=offer_data["distance"],
        estimated_duration_minutes=offer_data["duration"],
        included_waiting_time_minutes=60,
        passengers=request.passengers,
        luggage_places=request.luggage_places,
        sport_luggage_places=0,
        animals=0,
        wheelchairs_places=0,
        flight_number=request.flight_number,
        shield_text=request.shield_text,
        comment=request.comment,
        price=PriceObj(amount=offer_data["price"], currency="EUR"),
        meeting_instructions="The driver will wait at the meeting point with a name sign.",
        meeting_images=None,
    )


# --- Status ---

async def get_order_status(order_id: str, db: AsyncSession) -> StatusResponse:
    """Get the current status of an order."""
    result = await db.execute(
        select(Ride).where(Ride.external_id == order_id)
    )
    ride = result.scalar_one_or_none()

    if not ride:
        raise ETGServiceError(f"Order {order_id} not found", status_code=404)

    if ride.status in (RideStatus.COMPLETED,):
        etg_status = OrderStatus.COMPLETED
    elif ride.status in (RideStatus.CANCELLED,):
        etg_status = OrderStatus.CANCELLED
    else:
        etg_status = OrderStatus.ACTIVE

    # Build driver/car info if assigned
    driver_info = None
    car_info = None
    if ride.driver_id:
        driver_result = await db.execute(
            select(Driver).join(User, Driver.user_id == User.id).where(User.id == ride.driver_id)
        )
        driver = driver_result.scalar_one_or_none()
        if driver:
            user_result = await db.execute(select(User).where(User.id == ride.driver_id))
            user = user_result.scalar_one_or_none()
            driver_info = DriverInfo(
                name=f"{user.first_name or ''} {user.last_name or ''}".strip() if user else "",
                phone=user.phone or "" if user else "",
            )
            car_info = CarInfo(
                model=f"{driver.vehicle_make or ''} {driver.vehicle_model or ''}".strip(),
                plate_number=driver.vehicle_plate or "",
            )

    meeting_info = MeetingInfo(
        instructions="The driver will wait at the meeting point with a name sign.",
    )

    return StatusResponse(
        status=etg_status,
        order_id=order_id,
        start_time=ride.scheduled_at.isoformat() if ride.scheduled_at else "",
        price=PriceObj(amount=float(ride.price) if ride.price else 0.0, currency="EUR"),
        driver_info=driver_info,
        car_info=car_info,
        meeting_info=meeting_info,
    )


# --- Cancel ---

async def cancel_order(order_id: str, db: AsyncSession) -> CancelResponse:
    """Cancel an order. Returns penalty info."""
    result = await db.execute(
        select(Ride).where(Ride.external_id == order_id)
    )
    ride = result.scalar_one_or_none()

    if not ride:
        raise ETGServiceError(f"Order {order_id} not found", status_code=404)

    if ride.status in (RideStatus.COMPLETED, RideStatus.CANCELLED):
        raise ETGServiceError(
            f"Order {order_id} cannot be cancelled (status: {ride.status.value})",
            status_code=400,
        )

    now = datetime.now(timezone.utc)
    penalty_amount = 0.0
    if ride.scheduled_at:
        hours_before = (ride.scheduled_at - now).total_seconds() / 3600
        if hours_before < 24:
            penalty_amount = float(ride.price) if ride.price else 0.0

    ride.status = RideStatus.CANCELLED
    ride.updated_at = now
    await db.flush()

    return CancelResponse(
        penalty=CancelPenalty(amount=penalty_amount, currency="EUR"),
    )
