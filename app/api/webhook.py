from fastapi import APIRouter, Request, HTTPException
#from app.services.notifier import notify_order_created
from app.core.db import get_store
from app.services.tiendanube import get_order, PICKNSHIP_NAME

router = APIRouter(prefix="/webhook")

@router.post("/orders")
async def order_webhook(request: Request):
    payload = await request.json()

    store_id = payload.get("store_id")
    order_id = payload.get("id")

    if not store_id or not order_id:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    store = get_store(store_id)
    if not store:
        return {"status": "store_not_found"}

    access_token = store["access_token"]

    # 1️⃣ Fetch full order
    order = await get_order(
        store_id=store_id,
        order_id=order_id,
        access_token=access_token
    )

    print(f"[INFO] Full order fetched: {order}")

    return {"status": "ok"}