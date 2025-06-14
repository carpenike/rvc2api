#!/usr/bin/env python3
"""
Test WebSocket authentication with different auth modes.

This script tests WebSocket connections under different authentication configurations:
1. Auth disabled (AUTH_MODE=NONE)
2. Single-user mode with valid token
3. Single-user mode with invalid/missing token
4. Token expiry handling
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta

import httpx
import websockets
from websockets.exceptions import WebSocketException


# Test configuration
BASE_URL = "http://localhost:8080"
WS_BASE_URL = "ws://localhost:8080"


async def get_auth_token(username: str = "admin", password: str = "admin") -> str | None:
    """Get authentication token from the API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/admin/login",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                print(f"Login failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting auth token: {e}")
            return None


async def test_websocket_connection(endpoint: str, token: str | None = None, test_name: str = ""):
    """Test a WebSocket connection with optional authentication."""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"Endpoint: {endpoint}")
    print(f"Token: {'Provided' if token else 'None'}")
    print(f"{'='*60}")

    url = f"{WS_BASE_URL}{endpoint}"
    if token:
        url = f"{url}?token={token}"

    try:
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket connected successfully!")

            # Send a test message
            test_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await websocket.send(json.dumps(test_msg))
            print(f"Sent: {test_msg}")

            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("No response received (timeout)")

            # Keep connection open briefly
            await asyncio.sleep(1)

    except WebSocketException as e:
        print(f"❌ WebSocket connection failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


async def test_auth_modes():
    """Test WebSocket authentication in different modes."""

    # Test 1: With authentication enabled (normal mode)
    print("\n" + "="*80)
    print("TESTING WITH AUTHENTICATION ENABLED")
    print("="*80)

    # Get a valid token
    token = await get_auth_token()

    if token:
        # Test with valid token
        await test_websocket_connection(
            "/ws",
            token=token,
            test_name="Valid token - main WebSocket"
        )

        await test_websocket_connection(
            "/ws/logs",
            token=token,
            test_name="Valid token - logs WebSocket (admin only)"
        )

        await test_websocket_connection(
            "/ws/can-sniffer",
            token=token,
            test_name="Valid token - CAN sniffer WebSocket"
        )

    # Test without token
    await test_websocket_connection(
        "/ws",
        token=None,
        test_name="No token - should fail"
    )

    # Test with invalid token
    await test_websocket_connection(
        "/ws",
        token="invalid.token.here",
        test_name="Invalid token - should fail"
    )

    # Test 2: With authentication disabled
    print("\n" + "="*80)
    print("TESTING WITH AUTHENTICATION DISABLED")
    print("(Set COACHIQ_AUTH__ENABLED=false to test this mode)")
    print("="*80)

    # Note: This would require restarting the server with auth disabled
    # Just showing what would be tested
    print("To test auth disabled mode:")
    print("1. Stop the server")
    print("2. Set environment: export COACHIQ_AUTH__ENABLED=false")
    print("3. Restart the server")
    print("4. Run this test again")

    # Test 3: Token expiry
    print("\n" + "="*80)
    print("TESTING TOKEN EXPIRY HANDLING")
    print("="*80)

    if token:
        print("Token expiry test would require:")
        print("1. Modifying JWT_EXPIRE_MINUTES to a very short duration")
        print("2. Waiting for token to expire")
        print("3. Observing automatic disconnection")

    # Test 4: Permission-based access
    print("\n" + "="*80)
    print("TESTING PERMISSION-BASED ACCESS")
    print("="*80)

    # Note: Would need to create a non-admin user to test this properly
    print("Permission tests would require:")
    print("1. Creating a non-admin user")
    print("2. Testing /ws/logs endpoint (should fail for non-admin)")
    print("3. Testing other endpoints (should work for regular users)")


async def main():
    """Run all WebSocket authentication tests."""
    print("WebSocket Authentication Test Suite")
    print("==================================")
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().isoformat()}")

    try:
        await test_auth_modes()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")

    print(f"\n\nTests completed at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
