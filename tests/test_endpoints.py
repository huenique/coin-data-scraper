import asyncio

import httpx
import websockets

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"
CONTRACTS_URL = f"{BASE_URL}/contracts"
TWITTER_URL = f"{BASE_URL}/twitter/ZDBv9Kb55HvDqJHQD3REhSEsccH9Gdtvmn5JUgBpump"


# ✅ Test HTTP Endpoints
async def test_http_endpoints():
    async with httpx.AsyncClient() as client:
        print("\n🔍 Testing HTTP API Endpoints...\n")

        # Test Contracts API
        try:
            response = await client.get(CONTRACTS_URL)
            print(
                f"✅ [Contracts API] Status: {response.status_code}, Response: {response.json()}"
            )
        except Exception as e:
            print(f"❌ [Contracts API] Failed: {e}")

        # Test Twitter API
        try:
            response = await client.get(TWITTER_URL)
            print(
                f"✅ [Twitter API] Status: {response.status_code}, Response: {response.json()}"
            )
        except Exception as e:
            print(f"❌ [Twitter API] Failed: {e}")


# ✅ Test WebSocket Connection
async def test_websocket():
    print("\n🔍 Testing WebSocket Proxy...\n")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected to WebSocket Proxy!")

            # Listen for messages for 10 seconds
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=10)
                        print(f"✅ [WebSocket] Received: {message}")
                    except asyncio.TimeoutError:
                        print("⏳ [WebSocket] No messages received in 10 seconds.")
                        break
                    print(f"✅ [WebSocket] Received: {message}")
            except asyncio.TimeoutError:
                print("⏳ [WebSocket] No messages received in 10 seconds.")
    except Exception as e:
        print(f"❌ [WebSocket] Connection Failed: {e}")


# ✅ Run all tests
async def run_tests():
    await test_http_endpoints()
    await test_websocket()


# ✅ Start testing
asyncio.run(run_tests())
