import httpx
from fastapi import HTTPException
from app.core.config import settings
from typing import Dict, Any

PICKNSHIP_NAME = "Pick'NShip: vos elegís cuándo"
PICKNSHIP_DESCRIPTION = "Coordiná día y horario exacto con el repartidor luego de la compra"

# CABA postal codes: 1000–1429 + 'C1000'-'C1429'
CABA_ZIPCODES = [str(z) for z in range(1000, 1430)] + [f"C{z}" for z in range(1000, 1430)]


async def create_picknship_shipping_method(store_id: int, access_token: str) -> Dict[str, Any]:
    """
    Creates a PickNShip shipping method in the store via TiendaNube API.
    Idempotent: if shipping already exists, returns it.
    Only available for CABA ZIP codes.
    """

    headers = {
        "Authentication": f"bearer {access_token}",
        "User-Agent": f"Pick'NShip ({settings.PICKNSHIP_EMAIL})",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1️⃣ Fetch existing shippings
        try:
            resp = await client.get(f"https://api.tiendanube.com/v1/{store_id}/shipping_carriers", headers=headers)
            if resp.status_code == 404:
                shippings = []  # no shippings yet
            elif resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Failed to fetch existing shippings: {resp.text}"
                )
            else:
                shippings = resp.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to TiendaNube: {str(e)}")

        # 2️⃣ Check if Pick'NShip already exists
        for shipping in shippings:
            if shipping.get("name") == PICKNSHIP_NAME:
                print(f"[INFO] Pick'NShip shipping already exists for store {store_id}")
                return shipping

        # 3️⃣ Create Pick'NShip shipping
        payload = {
            "name": PICKNSHIP_NAME,
            "callback_url": f"{settings.BACKEND_URL}/rates",
            "types": "ship"
        }

        try:
            create_resp = await client.post(f"https://api.tiendanube.com/v1/{store_id}/shipping_carriers",
                                            headers=headers,
                                            json=payload)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error creating shipping: {str(e)}")

        if create_resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=create_resp.status_code,
                detail=f"Failed to create PickNShip shipping: {create_resp.text}"
            )

        print(f"[INFO] Pick'NShip shipping created for store {store_id}")
        return create_resp.json()