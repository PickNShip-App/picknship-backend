from fastapi import APIRouter, Request
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx
import urllib.parse
import os

router = APIRouter()

# --- (commented) previous CABA logic kept for quick revert ---
# CABA_ZIPCODES = [str(z) for z in range(1000, 1430)] + [f"C{z}" for z in range(1000, 1430)]
# def is_caba(postal_code: str) -> bool:
#     if not postal_code:
#         return False
#     p = postal_code.strip().upper()
#     return p in CABA_ZIPCODES

# Google Maps configuration — set GOOGLE_MAPS_API_KEY in your environment or settings
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # required

# Price tiers (ARS)
PRICE_TIER_LT_5KM = 3000
PRICE_TIER_5_TO_10KM = 5000
PRICE_TIER_10_TO_20KM = 10000

# Helper to build a readable address string for Maps API
def build_address_str(addr: Dict[str, Any]) -> str:
    # Use available fields to construct a best-effort address
    parts = []
    if addr.get("address"):
        parts.append(addr.get("address"))
    if addr.get("number"):
        parts.append(str(addr.get("number")))
    if addr.get("floor"):
        parts.append(f"Floor {addr.get('floor')}")
    if addr.get("locality"):
        parts.append(addr.get("locality"))
    if addr.get("city"):
        parts.append(addr.get("city"))
    if addr.get("province"):
        parts.append(addr.get("province"))
    if addr.get("postal_code"):
        parts.append(str(addr.get("postal_code")))
    if addr.get("country"):
        parts.append(addr.get("country"))
    return ", ".join([p for p in parts if p])

async def get_distance_km(origin: Dict[str, Any], destination: Dict[str, Any]) -> Optional[float]:
    """
    Calls Google Distance Matrix API and returns distance in kilometers (float).
    Returns None on error or if distance cannot be calculated.
    """
    if not GOOGLE_MAPS_API_KEY:
        # No API key configured
        return None

    origin_str = build_address_str(origin)
    destination_str = build_address_str(destination)
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
    except Exception:
        return None

    if resp.status_code != 200:
        return None

    data = resp.json()
    # Check overall status
    if data.get("status") != "OK":
        return None

    # Expect rows -> elements structure
    try:
        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return None
        meters = element["distance"]["value"]
        km = meters / 1000.0
        return float(km)
    except Exception:
        return None


@router.post("/rates")
async def calculate_rates(request: Request):
    """
    TiendaNube calls here to request rates for a checkout.
    We will:
      - read origin and destination from the payload
      - call Google Distance Matrix to compute distance (km)
      - return a rate according to the tiers:
          <5km -> 3000
          5-10km -> 5000
          10-20km -> 10000
          >20km -> no rate (we don't serve)
    """

    payload = await request.json()

    origin = payload.get("origin", {}) or {}
    destination = payload.get("destination", {}) or {}
    currency = payload.get("currency", "ARS")

    # Optionally: quick fallback if no Google key or address (commented)
    # postal_code = destination.get("postal_code", "")
    # if not is_caba(postal_code):
    #     return {"rates": []}

    # Compute distance using Google
    distance_km = await get_distance_km(origin, destination)

    # If distance couldn't be computed, hide our option (safe default)
    if distance_km is None:
        return {"rates": []}

    # Determine price tier
    price = None
    if distance_km < 5.0:
        price = PRICE_TIER_LT_5KM
    elif 5.0 <= distance_km < 10.0:
        price = PRICE_TIER_5_TO_10KM
    elif 10.0 <= distance_km <= 20.0:
        price = PRICE_TIER_10_TO_20KM
    else:
        # > 20 km not served
        return {"rates": []}

    now = datetime.now()
    #min_delivery = (now + timedelta(days=0)).strftime("%Y-%m-%dT%H:%M:%S-0300")
    #max_delivery = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S-0300")

    rate = {
        "name": "Pick'NShip: coordiná día y horario",
        "code": "picknship_dynamic",
        "price": price,
        "price_merchant": price,
        "currency": currency,
        "type": "ship",
        "phone_required": True,
        "id_required": False,
        "accepts_cod": False,
        "reference": f"picknship_km_{int(distance_km*1000)}m"
    }

    return {"rates": [rate]}