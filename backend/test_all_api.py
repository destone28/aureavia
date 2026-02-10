"""Test all API endpoints via HTTP."""
import asyncio
import httpx
import uuid as uuid_mod

BASE = "http://127.0.0.1:8000"
TEST_RUN_ID = uuid_mod.uuid4().hex[:8]  # Unique per test run


async def get_auth_token(client: httpx.AsyncClient, email: str, password: str) -> str:
    """Full login + 2FA flow. Returns access_token."""
    # Step 1: Login
    r = await client.post(f"{BASE}/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    temp_token = r.json()["temp_token"]

    # Step 2: We need to get the 2FA code from the server console.
    # For testing, we'll use the direct DB approach.
    # Instead, let's use a helper that reads the code from the user model.
    import sys
    sys.path.insert(0, ".")
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.utils.security import verify_password
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()

        # Try codes 000000-999999 would be slow; instead generate a fresh code
        from app.services.auth_service import generate_2fa_code, initiate_2fa
        code = generate_2fa_code()
        from app.utils.security import hash_password
        user.two_factor_code = hash_password(code)
        from datetime import datetime, timedelta, timezone
        user.two_factor_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        await session.commit()

    # Step 3: Verify 2FA
    r = await client.post(f"{BASE}/api/auth/verify-2fa", json={
        "temp_token": temp_token,
        "code": code,
    })
    assert r.status_code == 200, f"2FA failed: {r.text}"
    return r.json()["access_token"]


async def test_all():
    async with httpx.AsyncClient() as client:
        print("=== Full API Tests ===\n")

        # ---------------------------------------------------------------
        # 1. Health check
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/health")
        assert r.status_code == 200
        print("1. Health check: OK")

        # ---------------------------------------------------------------
        # 2. Auth: Get admin token
        # ---------------------------------------------------------------
        admin_token = await get_auth_token(client, "admin@aureavia.com", "admin123")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("2. Admin auth (login + 2FA): OK")

        # ---------------------------------------------------------------
        # 3. Auth: Get driver token
        # ---------------------------------------------------------------
        driver_token = await get_auth_token(client, "marco.rossi@driver.com", "driver123")
        driver_headers = {"Authorization": f"Bearer {driver_token}"}
        print("3. Driver auth (login + 2FA): OK")

        # ---------------------------------------------------------------
        # 4. Webhook: Create a ride via external booking
        # ---------------------------------------------------------------
        r = await client.post(f"{BASE}/api/webhook/booking", json={
            "external_id": f"BK-TEST-{TEST_RUN_ID}",
            "source_platform": "booking.com",
            "pickup_address": "Milano Malpensa Airport",
            "pickup_lat": 45.6306,
            "pickup_lng": 8.7281,
            "dropoff_address": "Hotel Duomo, Milano",
            "dropoff_lat": 45.4642,
            "dropoff_lng": 9.1900,
            "scheduled_at": "2026-02-15T10:00:00Z",
            "passenger_name": "John Smith",
            "passenger_phone": "+1234567890",
            "passenger_count": 2,
            "route_type": "extra_urban",
            "distance_km": 52.0,
            "duration_min": 45,
            "price": 85.00,
            "notes": "Business traveler, 2 large suitcases",
        })
        assert r.status_code == 201, f"Webhook failed: {r.text}"
        webhook_ride = r.json()
        webhook_ride_id = webhook_ride["id"]
        assert webhook_ride["status"] == "to_assign"
        print(f"4. Webhook booking created (ride_id={webhook_ride_id[:8]}...): OK")

        # ---------------------------------------------------------------
        # 5. Webhook: Duplicate rejected
        # ---------------------------------------------------------------
        r = await client.post(f"{BASE}/api/webhook/booking", json={
            "external_id": f"BK-TEST-{TEST_RUN_ID}",
            "source_platform": "booking.com",
            "pickup_address": "Test",
            "dropoff_address": "Test",
            "scheduled_at": "2026-02-15T10:00:00Z",
        })
        assert r.status_code == 409
        print("5. Webhook duplicate rejected: OK")

        # ---------------------------------------------------------------
        # 6. Rides: List (admin)
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/rides/", headers=admin_headers)
        assert r.status_code == 200
        rides_data = r.json()
        assert "rides" in rides_data
        assert rides_data["total"] > 0
        print(f"6. Admin list rides ({rides_data['total']} total): OK")

        # ---------------------------------------------------------------
        # 7. Rides: Get single ride (admin)
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/rides/{webhook_ride_id}", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["id"] == webhook_ride_id
        print("7. Admin get single ride: OK")

        # ---------------------------------------------------------------
        # 8. Rides: Create ride (admin)
        # ---------------------------------------------------------------
        r = await client.post(f"{BASE}/api/rides/", headers=admin_headers, json={
            "pickup_address": "Stazione Centrale, Milano",
            "dropoff_address": "Fiera Milano Rho",
            "scheduled_at": "2026-02-16T14:00:00Z",
            "passenger_name": "Maria Verdi",
            "passenger_count": 1,
            "source_platform": "manual",
            "price": 45.00,
            "driver_share": 35.00,
        })
        assert r.status_code == 201, f"Create ride failed: {r.text}"
        admin_ride_id = r.json()["id"]
        print(f"8. Admin create ride: OK")

        # ---------------------------------------------------------------
        # 9. Rides: Assign ride to driver
        # ---------------------------------------------------------------
        # Get driver's user_id (marco.rossi)
        from app.database import AsyncSessionLocal
        from app.models.user import User
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == "marco.rossi@driver.com")
            )
            driver_user = result.scalar_one()
            driver_user_id = str(driver_user.id)

        r = await client.put(
            f"{BASE}/api/rides/{webhook_ride_id}/assign",
            headers=admin_headers,
            json={"driver_id": driver_user_id},
        )
        assert r.status_code == 200, f"Assign failed: {r.text}"
        assert r.json()["driver_id"] == driver_user_id
        print("9. Admin assign ride to driver: OK")

        # ---------------------------------------------------------------
        # 10. Rides: Driver accepts ride
        # ---------------------------------------------------------------
        r = await client.put(
            f"{BASE}/api/rides/{webhook_ride_id}/accept",
            headers=driver_headers,
        )
        assert r.status_code == 200, f"Accept failed: {r.text}"
        assert r.json()["status"] == "booked"
        print("10. Driver accept ride: OK")

        # ---------------------------------------------------------------
        # 11. Rides: Driver starts ride
        # ---------------------------------------------------------------
        r = await client.put(
            f"{BASE}/api/rides/{webhook_ride_id}/start",
            headers=driver_headers,
        )
        assert r.status_code == 200, f"Start failed: {r.text}"
        assert r.json()["status"] == "in_progress"
        print("11. Driver start ride: OK")

        # ---------------------------------------------------------------
        # 12. Rides: Driver completes ride
        # ---------------------------------------------------------------
        r = await client.put(
            f"{BASE}/api/rides/{webhook_ride_id}/complete",
            headers=driver_headers,
        )
        assert r.status_code == 200, f"Complete failed: {r.text}"
        assert r.json()["status"] == "completed"
        print("12. Driver complete ride: OK")

        # ---------------------------------------------------------------
        # 13. Rides: Cancel ride (admin)
        # ---------------------------------------------------------------
        r = await client.put(
            f"{BASE}/api/rides/{admin_ride_id}/cancel",
            headers=admin_headers,
            json={"notes": "Client cancelled"},
        )
        assert r.status_code == 200, f"Cancel failed: {r.text}"
        assert r.json()["status"] == "cancelled"
        print("13. Admin cancel ride: OK")

        # ---------------------------------------------------------------
        # 14. Drivers: List (admin)
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/drivers/", headers=admin_headers)
        assert r.status_code == 200
        drivers_list = r.json()
        assert len(drivers_list) >= 5
        print(f"14. Admin list drivers ({len(drivers_list)} drivers): OK")

        # ---------------------------------------------------------------
        # 15. Drivers: Get single driver
        # ---------------------------------------------------------------
        first_driver_id = drivers_list[0]["id"]
        r = await client.get(f"{BASE}/api/drivers/{first_driver_id}", headers=admin_headers)
        assert r.status_code == 200
        print("15. Admin get single driver: OK")

        # ---------------------------------------------------------------
        # 16. Drivers: Get driver stats
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/drivers/{first_driver_id}/stats", headers=admin_headers)
        assert r.status_code == 200
        stats = r.json()
        assert "total_rides" in stats
        print(f"16. Driver stats (total_rides={stats['total_rides']}): OK")

        # ---------------------------------------------------------------
        # 17. Drivers: Get driver reviews
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/drivers/{first_driver_id}/reviews", headers=admin_headers)
        assert r.status_code == 200
        print(f"17. Driver reviews ({len(r.json())} reviews): OK")

        # ---------------------------------------------------------------
        # 18. Companies: List (admin)
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/companies/", headers=admin_headers)
        assert r.status_code == 200
        companies = r.json()
        assert len(companies) >= 4
        print(f"18. Admin list companies ({len(companies)}): OK")

        # ---------------------------------------------------------------
        # 19. Companies: Create (admin)
        # ---------------------------------------------------------------
        r = await client.post(f"{BASE}/api/companies/", headers=admin_headers, json={
            "name": "Test NCC Company",
            "contact_email": "test@ncc.com",
            "contact_person": "Test Manager",
            "contact_phone": "+39111222333",
        })
        assert r.status_code == 201, f"Create company failed: {r.text}"
        new_company_id = r.json()["id"]
        print("19. Admin create company: OK")

        # ---------------------------------------------------------------
        # 20. Companies: Update (admin)
        # ---------------------------------------------------------------
        r = await client.put(
            f"{BASE}/api/companies/{new_company_id}",
            headers=admin_headers,
            json={"name": "Updated NCC Company"},
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Updated NCC Company"
        print("20. Admin update company: OK")

        # ---------------------------------------------------------------
        # 21. Reports: Dashboard KPIs (admin)
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/reports/dashboard", headers=admin_headers)
        assert r.status_code == 200
        kpis = r.json()
        assert "total_rides" in kpis
        assert "total_revenue" in kpis
        print(f"21. Dashboard KPIs (rides={kpis['total_rides']}, revenue={kpis['total_revenue']}): OK")

        # ---------------------------------------------------------------
        # 22. Reports: Earnings (admin)
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/reports/earnings?granularity=daily", headers=admin_headers)
        assert r.status_code == 200
        earnings = r.json()
        assert earnings["granularity"] == "daily"
        print(f"22. Earnings report ({len(earnings['data'])} data points): OK")

        # ---------------------------------------------------------------
        # 23. Notifications: List (driver)
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/notifications/", headers=driver_headers)
        assert r.status_code == 200
        notifs = r.json()
        print(f"23. Driver notifications ({len(notifs)} total): OK")

        # ---------------------------------------------------------------
        # 24. Notifications: Unread count
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/notifications/unread-count", headers=driver_headers)
        assert r.status_code == 200
        assert "unread_count" in r.json()
        print(f"24. Unread notifications ({r.json()['unread_count']}): OK")

        # ---------------------------------------------------------------
        # 25. Notifications: Mark as read
        # ---------------------------------------------------------------
        if notifs:
            notif_id = notifs[0]["id"]
            r = await client.put(
                f"{BASE}/api/notifications/{notif_id}/read",
                headers=driver_headers,
            )
            assert r.status_code == 200
            assert r.json()["read_at"] is not None
            print("25. Mark notification as read: OK")
        else:
            print("25. Mark notification as read: SKIPPED (no notifications)")

        # ---------------------------------------------------------------
        # 26. Rides: Driver list (sees own + unassigned)
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/rides/", headers=driver_headers)
        assert r.status_code == 200
        print(f"26. Driver list rides ({r.json()['total']} visible): OK")

        # ---------------------------------------------------------------
        # 27. Unauthorized access rejected
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/api/rides/")
        assert r.status_code == 403 or r.status_code == 401
        print("27. Unauthorized access rejected: OK")

        # ---------------------------------------------------------------
        # 28. Swagger docs accessible
        # ---------------------------------------------------------------
        r = await client.get(f"{BASE}/docs")
        assert r.status_code == 200
        print("28. Swagger docs accessible: OK")

        print(f"\n✅ All {28} API tests passed!")


if __name__ == "__main__":
    asyncio.run(test_all())
