from fastapi import APIRouter, Request
from datetime import datetime, timedelta
import json

router = APIRouter()

CABA_ZIPCODES = [str(z) for z in range(1000, 1430)] + [f"C{z}" for z in range(1000, 1430)]

def is_caba(postal_code: str) -> bool:
    if not postal_code:
        return False
    p = postal_code.strip().upper()
    return p in CABA_ZIPCODES

@router.post("/rates")
async def calculate_rates(request: Request):
    body = await request.json()
    destination = body.get("destination", {})
    postal_code = destination.get("postal_code", "")

    if not is_caba(postal_code):
        return {"rates": []}

    price = 10000
    currency = body.get("currency", "ARS")

    now = datetime.now()
    min_delivery = (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S-0300")
    max_delivery = (now + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S-0300")

    response = {
        "rates": [
            {
                "name": "Pick'NShip: coordiná día y horario",
                "code": "picknship_standard",
                "price": price,
                "price_merchant": price,
                "currency": currency,
                "type": "ship",
                "min_delivery_date": min_delivery,
                "max_delivery_date": max_delivery,
                "phone_required": True,
                "reference": "picknship_rate_v1"
            }
        ]
    }

    return response