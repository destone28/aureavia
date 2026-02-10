"""Quick test for the auth flow."""
import asyncio
from app.database import AsyncSessionLocal
from app.services.auth_service import authenticate_user, initiate_2fa, verify_2fa_code


async def test_auth_flow():
    async with AsyncSessionLocal() as db:
        print("=== TEST: Auth Flow ===\n")

        # 1. Authenticate
        user = await authenticate_user(db, "admin@aureavia.com", "admin123")
        assert user is not None, "Authentication failed!"
        print(f"1. Login OK: {user.email} ({user.role})")

        # 2. Initiate 2FA - get raw code before hashing
        import random, string
        from app.utils.security import hash_password, verify_password
        from datetime import datetime, timedelta, timezone

        code = ''.join(random.choices(string.digits, k=6))
        user.two_factor_code = hash_password(code)
        user.two_factor_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        await db.flush()
        print(f"2. 2FA code generated: {code}")

        # 3. Verify 2FA
        is_valid = await verify_2fa_code(db, user, code)
        assert is_valid, "2FA verification failed!"
        print(f"3. 2FA verification OK")

        # 4. Verify tokens can be created
        from app.utils.security import create_access_token, create_refresh_token, decode_access_token
        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        decoded = decode_access_token(access)
        assert decoded is not None, "Token decode failed!"
        assert decoded["sub"] == str(user.id), "Token user mismatch!"
        print(f"4. JWT tokens OK (access + refresh)")

        # 5. Test wrong password
        bad_user = await authenticate_user(db, "admin@aureavia.com", "wrong")
        assert bad_user is None, "Wrong password should fail!"
        print(f"5. Wrong password correctly rejected")

        # 6. Test wrong 2FA code
        user2 = await authenticate_user(db, "marco.rossi@driver.com", "driver123")
        assert user2 is not None, "Driver auth failed!"
        code2 = ''.join(random.choices(string.digits, k=6))
        user2.two_factor_code = hash_password(code2)
        user2.two_factor_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        await db.flush()
        bad_verify = await verify_2fa_code(db, user2, "000000")
        assert not bad_verify, "Wrong 2FA code should fail!"
        print(f"6. Wrong 2FA code correctly rejected")

        # 7. Test driver login
        good_verify = await verify_2fa_code(db, user2, code2)
        assert good_verify, "Driver 2FA should succeed!"
        print(f"7. Driver login + 2FA OK ({user2.email})")

        await db.commit()
        print("\n✅ All auth tests passed!")


if __name__ == "__main__":
    asyncio.run(test_auth_flow())
