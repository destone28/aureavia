"""
Seed script for populating the database with demo data.
Run with: python seed.py
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import (
    User, UserRole, UserStatus,
    NCCCompany, CompanyStatus,
    Driver,
    Ride, RideStatus, RouteType,
    Review
)
from app.utils.security import hash_password


async def seed_database():
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding database...")

        # 1. Create admin user
        admin = User(
            email="admin@aureavia.com",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            first_name="Admin",
            last_name="AureaVia",
            phone="+393331234567",
            status=UserStatus.ACTIVE
        )
        db.add(admin)
        print("✓ Created admin user (admin@aureavia.com / admin123)")

        # 2. Create NCC Companies
        companies_data = [
            {
                "name": "Booking.com",
                "partner_type": "booking_platform",
                "contact_email": "ncc@booking.com",
                "contact_phone": "+390212345678"
            },
            {
                "name": "Elite Travel NCC Milano",
                "partner_type": "ncc_partner",
                "contact_person": "Giuseppe Verdi",
                "contact_email": "info@elitetravel.it",
                "contact_phone": "+390223456789"
            },
            {
                "name": "BusinessRide",
                "partner_type": "ncc_partner",
                "contact_person": "Marco Bianchi",
                "contact_email": "contact@businessride.it",
                "contact_phone": "+390234567890"
            },
            {
                "name": "Premium Transfer Services",
                "partner_type": "ncc_partner",
                "contact_person": "Andrea Conti",
                "contact_email": "info@premiumtransfer.it",
                "contact_phone": "+390245678901"
            }
        ]

        companies = []
        for comp_data in companies_data:
            company = NCCCompany(**comp_data, status=CompanyStatus.ACTIVE)
            db.add(company)
            companies.append(company)

        await db.flush()  # Get IDs
        print(f"✓ Created {len(companies)} NCC companies")

        # 3. Create driver users and driver profiles
        drivers_data = [
            {
                "email": "marco.rossi@driver.com",
                "password": "driver123",
                "first_name": "Marco",
                "last_name": "Rossi",
                "phone": "+393334567890",
                "ncc_company_id": companies[1].id,
                "license_number": "DRV-001",
                "vehicle_make": "Mercedes-Benz",
                "vehicle_model": "E-Class",
                "vehicle_plate": "MI123AB",
                "vehicle_year": 2022,
                "vehicle_seats": 4,
                "vehicle_fuel_type": "Diesel",
                "rating_avg": 4.7,
                "total_rides": 142,
                "total_km": 7235.5,
                "total_earnings": 12850.00
            },
            {
                "email": "giuseppe.verdi@driver.com",
                "password": "driver123",
                "first_name": "Giuseppe",
                "last_name": "Verdi",
                "phone": "+393335678901",
                "ncc_company_id": companies[3].id,
                "license_number": "DRV-002",
                "vehicle_make": "BMW",
                "vehicle_model": "5 Series",
                "vehicle_plate": "MI456CD",
                "vehicle_year": 2023,
                "vehicle_seats": 4,
                "vehicle_fuel_type": "Hybrid",
                "rating_avg": 4.9,
                "total_rides": 98,
                "total_km": 5432.0,
                "total_earnings": 9800.00
            },
            {
                "email": "luca.ferrari@driver.com",
                "password": "driver123",
                "first_name": "Luca",
                "last_name": "Ferrari",
                "phone": "+393336789012",
                "ncc_company_id": companies[2].id,
                "license_number": "DRV-003",
                "vehicle_make": "Audi",
                "vehicle_model": "A6",
                "vehicle_plate": "MI789EF",
                "vehicle_year": 2021,
                "vehicle_seats": 4,
                "vehicle_fuel_type": "Diesel",
                "rating_avg": 4.7,
                "total_rides": 156,
                "total_km": 8123.3,
                "total_earnings": 14200.00
            },
            {
                "email": "andrea.bianchi@driver.com",
                "password": "driver123",
                "first_name": "Andrea",
                "last_name": "Bianchi",
                "phone": "+393337890123",
                "ncc_company_id": companies[1].id,
                "license_number": "DRV-004",
                "vehicle_make": "Mercedes-Benz",
                "vehicle_model": "S-Class",
                "vehicle_plate": "MI012GH",
                "vehicle_year": 2023,
                "vehicle_seats": 4,
                "vehicle_fuel_type": "Hybrid",
                "rating_avg": 4.6,
                "total_rides": 87,
                "total_km": 4567.8,
                "total_earnings": 8900.00
            },
            {
                "email": "simone.conti@driver.com",
                "password": "driver123",
                "first_name": "Simone",
                "last_name": "Conti",
                "phone": "+393338901234",
                "ncc_company_id": companies[3].id,
                "license_number": "DRV-007",
                "vehicle_make": "Mercedes-Benz",
                "vehicle_model": "E-Class",
                "vehicle_plate": "MI345IJ",
                "vehicle_year": 2022,
                "vehicle_seats": 4,
                "vehicle_fuel_type": "Diesel",
                "rating_avg": 4.4,
                "total_rides": 71,
                "total_km": 3890.2,
                "total_earnings": 7100.00
            }
        ]

        drivers = []
        for driver_data in drivers_data:
            # Create user
            user = User(
                email=driver_data["email"],
                password_hash=hash_password(driver_data["password"]),
                role=UserRole.DRIVER,
                first_name=driver_data["first_name"],
                last_name=driver_data["last_name"],
                phone=driver_data["phone"],
                status=UserStatus.ACTIVE
            )
            db.add(user)
            await db.flush()

            # Create driver profile
            driver = Driver(
                user_id=user.id,
                ncc_company_id=driver_data["ncc_company_id"],
                license_number=driver_data["license_number"],
                vehicle_make=driver_data["vehicle_make"],
                vehicle_model=driver_data["vehicle_model"],
                vehicle_plate=driver_data["vehicle_plate"],
                vehicle_year=driver_data["vehicle_year"],
                vehicle_seats=driver_data["vehicle_seats"],
                vehicle_fuel_type=driver_data["vehicle_fuel_type"],
                rating_avg=driver_data["rating_avg"],
                total_rides=driver_data["total_rides"],
                total_km=driver_data["total_km"],
                total_earnings=driver_data["total_earnings"]
            )
            db.add(driver)
            drivers.append((user, driver))

        await db.flush()
        print(f"✓ Created {len(drivers)} drivers")

        # 4. Create sample rides
        rides_data = [
            {
                "external_id": "NCC-2024-045",
                "source_platform": "Booking.com",
                "pickup_address": "Milano Centrale Station",
                "dropoff_address": "Malpensa Airport Terminal 1",
                "scheduled_at": datetime.now() + timedelta(hours=4),
                "passenger_name": "John Anderson",
                "passenger_phone": "+14155551234",
                "passenger_count": 1,
                "route_type": RouteType.EXTRA_URBAN,
                "distance_km": 52.0,
                "duration_min": 40,
                "price": 85.00,
                "driver_share": 68.00,
                "status": RideStatus.TO_ASSIGN
            },
            {
                "external_id": "NCC-2024-046",
                "source_platform": "Booking.com",
                "pickup_address": "Via Montenapoleone 12",
                "dropoff_address": "Como City Center",
                "scheduled_at": datetime.now() + timedelta(days=1, hours=2),
                "passenger_name": "Emma Rodriguez",
                "passenger_phone": "+34612345678",
                "passenger_count": 2,
                "route_type": RouteType.EXTRA_URBAN,
                "distance_km": 69.0,
                "duration_min": 55,
                "price": 120.00,
                "driver_share": 96.00,
                "status": RideStatus.TO_ASSIGN
            },
            {
                "external_id": "NCC-2024-047",
                "source_platform": "Elite Travel",
                "pickup_address": "Piazza del Duomo",
                "dropoff_address": "Linate Airport",
                "scheduled_at": datetime.now() - timedelta(hours=2),
                "passenger_name": "Maria Bianchi",
                "passenger_phone": "+393391234567",
                "passenger_count": 1,
                "route_type": RouteType.URBAN,
                "distance_km": 8.5,
                "duration_min": 18,
                "price": 35.00,
                "driver_share": 28.00,
                "status": RideStatus.COMPLETED,
                "driver_id": drivers[0][0].id,
                "completed_at": datetime.now() - timedelta(minutes=20)
            }
        ]

        rides = []
        for ride_data in rides_data:
            ride = Ride(**ride_data)
            db.add(ride)
            rides.append(ride)

        await db.flush()
        print(f"✓ Created {len(rides)} sample rides")

        # 5. Create sample reviews for completed ride
        review = Review(
            ride_id=rides[2].id,
            driver_id=drivers[0][1].id,
            rating=5,
            comment="Excellent service, very professional and punctual!",
            reviewer_name="Maria Bianchi",
            source_platform="Booking.com"
        )
        db.add(review)
        print("✓ Created sample review")

        await db.commit()
        print("\n✅ Database seeded successfully!")
        print("\n📋 Login credentials:")
        print("   Admin: admin@aureavia.com / admin123")
        print("   Driver: marco.rossi@driver.com / driver123")
        print("   (All drivers use password: driver123)")


if __name__ == "__main__":
    asyncio.run(seed_database())
