from fastapi import APIRouter, Request, HTTPException
from app.core.db import get_store, save_order_if_new, get_order
from app.services.tiendanube import get_order, PICKNSHIP_NAME
from app.services.notifier import notify_order_created, notify_order_updated

router = APIRouter(prefix="/webhook")

@router.post("/orders")
async def order_webhook(request: Request):
    payload = await request.json()
    print(f"[WEBHOOK] Received payload: {payload}")
    store_id = payload.get("store_id")
    order_id = payload.get("id")
    event = payload.get("event", "order/created")

    if not store_id or not order_id:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    store = get_store(store_id)
    if not store:
        return {"status": "store_not_found"}

    access_token = store["access_token"]

    # 1️⃣ Fetch full order
    order = await get_order(store_id=store_id, order_id=order_id, access_token=access_token)

    shipping_method_name = order.get("shipping_carrier_name") or order.get("shipping_option") or ""
    if PICKNSHIP_NAME not in shipping_method_name:
        print(f"[INFO] Ignored order {order_id}: not PickNShip")
        return {"status": "ignored"}

    # 2️⃣ Preparar datos para DB
    order_data = {
        "order_id": order_id,
        "store_id": store_id,
        "customer_name": order.get("customer", {}).get("name", ""),
        "customer_email": order.get("customer", {}).get("email", ""),
        "customer_phone": order.get("customer", {}).get("phone", ""),
        "total": float(order.get("total", 0.0)),
        "currency": order.get("currency", "ARS"),
        "status": order.get("status", ""),
        "shipping_method": shipping_method_name,
        "shipping_option": order.get("shipping_option_code") or "",
        "shipping_address": order.get("shipping_address", {}),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at")
    }
    print(f"[WEBHOOK] Processed order data: {order_data}")
    # 3️⃣ Guardar orden
    is_new = save_order_if_new(order_data)
    print(f"[WEBHOOK] Order {order_id} saved. New: {is_new}")
    # 4️⃣ Notificaciones
    if is_new:
        await notify_order_created(order_data)
    else:
        # comparar cambios
        previous = get_order(order_id, store_id)
        changes = {}
        for k in ["customer_name", "customer_email", "customer_phone", "total", "status",
                  "shipping_method", "shipping_option", "shipping_address"]:
            old = previous.get(k)
            new = order_data.get(k)
            if old != new:
                changes[k] = {"old": old, "new": new}
        
        if changes:
            order_diff = {
                "order_id": order_id,
                "store_id": store_id,
                "changes": changes
            }
            await notify_order_updated(order_diff)

    return {"status": "ok"}