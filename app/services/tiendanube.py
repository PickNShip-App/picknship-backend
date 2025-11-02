import httpx
from fastapi import HTTPException

# Pick'NShip shipping details
PICKNSHIP_NAME = "Pick'NShip: vos elegís cuándo"
PICKNSHIP_DESCRIPTION = "Coordiná día y horario exacto con el repartidor luego de la compra"
PICKNSHIP_PRICE = 10000  # Example fixed price, can be dynamic later
PICKNSHIP_ENABLED = True

# CABA postal codes: 1000–1429 + 'C1000'-'C1429'
CABA_ZIPCODES = [str(z) for z in range(1000, 1430)] + [f"C{z}" for z in range(1000, 1430)]


async def create_picknship_shipping(store_id: int, access_token: str):
    """
    Creates a PickNShip shipping method in the store via TiendaNube API.
    If shipping already exists, it does nothing (idempotent).
    Only available for CABA ZIP codes.
    """

    headers = {
        "Authentication": f"bearer {access_token}",
        "User-Agent": "Pick'NShip (info@picknshipapp.com)",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1️⃣ Fetch existing shipping methods
        resp = await client.get(
            f"https://api.tiendanube.com/v1/{store_id}/shippings",
            headers=headers,
        )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to fetch existing shippings: {resp.text}"
            )

        shippings = resp.json()
        for shipping in shippings:
            if shipping.get("name") == PICKNSHIP_NAME:
                # Already exists, do nothing
                return shipping

        # 2️⃣ Create Pick'NShip shipping method for CABA
        payload = {
            "name": PICKNSHIP_NAME,
            "price": PICKNSHIP_PRICE,
            "enabled": PICKNSHIP_ENABLED,
            "description": PICKNSHIP_DESCRIPTION,
            "delivery_time": None,
            "zip_codes": CABA_ZIPCODES,  # TiendaNube will handle visibility
        }

        create_resp = await client.post(
            f"https://api.tiendanube.com/v1/{store_id}/shippings",
            headers=headers,
            json=payload,
        )

        if create_resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=create_resp.status_code,
                detail=f"Failed to create PickNShip shipping: {create_resp.text}"
            )

        return create_resp.json()