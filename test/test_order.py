import httpx
import json

BACKEND_URL = "https://picknship-backend.onrender.com"
STORE_ID = "storeid"  # replace with actual store_id
ACCESS_TOKEN = "access_token"  # replace with stored token

payload = {
    "id": "TEST-ORDER-1234",
    "store_id": STORE_ID,
    "shipping_address": {
        "zip": "C1426",
        "address1": "Av. Falsa 123",
        "city": "CABA",
        "province": "Ciudad Autónoma de Buenos Aires"
    },
    "customer": {
        "name": "Test User",
        "email": "test@example.com"
    },
    "items": [
        {"title": "Test Product", "quantity": 1, "price": 1000}
    ],
    "total": 1100,
    "shipping_cost": 100
}

async def send_order():
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BACKEND_URL}/webhook/orders",
            json=payload
        )
        print("Status:", r.status_code)
        print("Response:", r.json())

import asyncio
asyncio.run(send_order())