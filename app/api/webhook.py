from fastapi import APIRouter, Request
from app.core.db import save_order, get_store
import json

router = APIRouter(prefix="/webhook")

@router.post("/orders")
async def order_webhook(request: Request):
    payload = await request.json()
    headers = request.headers
    store_id = headers.get("User-Id") or headers.get("X-User-Id") or payload.get("store_id") or payload.get("user_id")
    order_id = payload.get("id") or payload.get("order_id") or payload.get("number")

    raw_payload = json.dumps(payload)
    save_order(order_id=str(order_id or "unknown"), store_id=str(store_id or "unknown"), payload=raw_payload)

    store = get_store(store_id) if store_id else None
    print(f"📦 Order received (order {order_id}) from store {store_id}. Store found: {bool(store)}")
    # TODO: call notifier to send WhatsApp/email

    return {"status": "ok"}