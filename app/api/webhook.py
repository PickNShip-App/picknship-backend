from fastapi import APIRouter, Request
from app.api.utils import is_caba_zipcode
from app.core.db import save_order, get_store
import json

router = APIRouter(prefix="/webhook")

@router.post("/orders")
async def order_webhook(request: Request):
    payload = await request.json()
    # Try different ways to obtain store identification:
    headers = request.headers
    store_id = headers.get("User-Id") or headers.get("X-User-Id") or payload.get("store_id") or payload.get("user_id")
    order_id = payload.get("id") or payload.get("order_id") or payload.get("number")

    # Persist the raw payload as string
    raw_payload = json.dumps(payload)

    # Save order to DB (store_id may be None for some events; still save)
    save_order(order_id=str(order_id or "unknown"), store_id=str(store_id or "unknown"), payload=raw_payload)

    # Determine zipcode for routing
    shipping = payload.get("shipping_address") or {}
    zipcode = shipping.get("zip") or shipping.get("zipcode") or shipping.get("postal_code") or ""

    if is_caba_zipcode(zipcode):
        # find store to see token (later used for richer behavior)
        store = get_store(store_id) if store_id else None
        print(f"✅ CABA order received (order {order_id}) from store {store_id}. Store found: {bool(store)}")
        # TODO: call notifier to send whatsapp/email
    else:
        print(f"❌ Out of zone order ({zipcode}) ignoring for Pick'NShip")

    return {"status": "ok"}
