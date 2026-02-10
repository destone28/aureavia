"""Test the API endpoints via HTTP."""
import asyncio
import httpx


async def test_api():
    base = "http://127.0.0.1:8000"

    async with httpx.AsyncClient() as client:
        print("=== API Tests ===\n")

        # 1. Health check
        r = await client.get(f"{base}/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        print("1. Health check: OK")

        # 2. Login with wrong password
        r = await client.post(f"{base}/api/auth/login", json={
            "email": "admin@aureavia.com",
            "password": "wrong"
        })
        assert r.status_code == 401
        print("2. Wrong password rejected: OK")

        # 3. Login with correct credentials
        r = await client.post(f"{base}/api/auth/login", json={
            "email": "admin@aureavia.com",
            "password": "admin123"
        })
        assert r.status_code == 200
        data = r.json()
        assert "temp_token" in data
        temp_token = data["temp_token"]
        print(f"3. Login successful, got temp_token: OK")

        # 4. We can't easily test verify-2fa via HTTP since the code is printed to server console
        # Instead, test with wrong code
        r = await client.post(f"{base}/api/auth/verify-2fa", json={
            "temp_token": temp_token,
            "code": "000000"
        })
        assert r.status_code == 401
        print("4. Wrong 2FA code rejected: OK")

        # 5. Test invalid temp_token
        r = await client.post(f"{base}/api/auth/verify-2fa", json={
            "temp_token": "invalid_token",
            "code": "123456"
        })
        assert r.status_code == 401
        print("5. Invalid temp_token rejected: OK")

        # 6. Test refresh with invalid token
        r = await client.post(f"{base}/api/auth/refresh", json={
            "refresh_token": "invalid"
        })
        assert r.status_code == 401
        print("6. Invalid refresh token rejected: OK")

        # 7. Swagger docs accessible
        r = await client.get(f"{base}/docs")
        assert r.status_code == 200
        print("7. Swagger docs accessible: OK")

        print("\n✅ All API tests passed!")


if __name__ == "__main__":
    asyncio.run(test_api())
