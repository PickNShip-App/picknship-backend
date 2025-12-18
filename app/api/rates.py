from fastapi import APIRouter, Request
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.config import settings
import httpx
import urllib.parse

router = APIRouter()

# Google Maps configuration
GOOGLE_MAPS_API_KEY = settings.GOOGLE_MAPS_API_KEY

# Price tiers (ARS)
PRICE_TIER_LT_3KM = 3000
PRICE_TIER_3_TO_5KM = 5000
PRICE_TIER_5_TO_10KM = 10000

# --- ZIP code fallback for quick check before full addresses ---
CABA_ZIPCODES = [str(z) for z in range(1000, 1430)] + [f"C{z}" for z in range(1000, 1430)]
def is_caba(postal_code: str) -> bool:
    if not postal_code:
        return False
    return postal_code.strip().upper() in CABA_ZIPCODES


def build_address_str(addr: Dict[str, Any]) -> str:
    """Build a readable address string for Google Maps API."""
    parts = []
    for key in ["address", "number", "floor", "locality", "city", "province", "postal_code", "country"]:
        if addr.get(key):
            parts.append(str(addr.get(key)))
    return ", ".join(parts)

async def get_distance_km(origin: Dict[str, Any], destination: Dict[str, Any]) -> Optional[float]:
    """Call Google Distance Matrix API and return distance in km."""
    if not GOOGLE_MAPS_API_KEY or not origin or not destination:
        return None

    origin_str = build_address_str(origin)
    print(f"[DEBUG] Origin address string: {origin_str}")
    destination_str = build_address_str(destination)
    print(f"[DEBUG] Destination address string: {destination_str}")
    if not origin_str or not destination_str:
        return None

    params = {
        "origins": origin_str,
        "destinations": destination_str,
        "key": GOOGLE_MAPS_API_KEY,
        "units": "metric"
    }
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?" + urllib.parse.urlencode(params, safe=",")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
        data = resp.json()
        if data.get("status") != "OK":
            return None
        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return None
        meters = element["distance"]["value"]
        return meters / 1000.0
    except Exception:
        return None

@router.post("/rates")
async def calculate_rates(request: Request):
    """
    TiendaNube calls here to request rates.
    - First: fallback by ZIP code if no full addresses
    - Then: calculate distance if origin/destination present
    - Return price according to tiers
    """
    payload = await request.json()
    origin = payload.get("origin", {}) or {}
    destination = payload.get("destination", {}) or {}
    postal_code = destination.get("postal_code", "")
    currency = payload.get("currency", "ARS")

    price = None

    # --- Distance-based pricing if we have full addresses ---
    distance_km = await get_distance_km(origin, destination)
    print(f"[DEBUG] Destination: {destination}")
    print(f"[INFO] Calculated distance: {distance_km} km")
    if distance_km is not None:
        if distance_km < 3.0:
            price = PRICE_TIER_LT_3KM
        elif 3.0 <= distance_km < 5.0:
            price = PRICE_TIER_3_TO_5KM
        elif 5.0 <= distance_km <= 10.0:
            price = PRICE_TIER_5_TO_10KM
    else:
        if is_caba(postal_code):
            price = PRICE_TIER_5_TO_10KM
    
    if price is None:
        return {"rates": []}

    rate = {
        "name": "Pick'NShip: coordinamos dia y horario por whatsapp",
        "code": "picknship_dynamic",
        "price": price,
        "price_merchant": price,
        "currency": currency,
        "type": "ship",
        "phone_required": True,
        "id_required": False,
        "accepts_cod": False,
        "reference": f"picknship_rate_{'lt_5' if distance_km and distance_km < 5.0 else '5_10' if distance_km and 5.0 <= distance_km < 10.0 else '10_20' if distance_km and 10.0 <= distance_km <= 20.0 else 'zip'}",
    }

    return {"rates": [rate]}
