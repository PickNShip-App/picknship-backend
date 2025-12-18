from fastapi import APIRouter, Request, HTTPException
#from app.services.notifier import notify_order_created
#from app.core.db import save_order_if_new
from app.services.tiendanube import PICKNSHIP_NAME

router = APIRouter(prefix="/webhook")

@router.post("/orders")
async def order_webhook(request: Request):
    payload = await request.json()

    order_id = payload.get("id")
    store_id = payload.get("store_id")
    status = payload.get("status")
    weight = payload.get("weight")
    customer_payload = payload.get("customer") or {}
    customer = {
        "name": customer_payload.get("name"),
        "email": customer_payload.get("email"),
        "phone": customer_payload.get("phone"),
    }
    shipping_address = payload.get("shipping_address")

    #shipping_carrier = payload.get("shipping_carrier")
    #shipping_option = payload.get("shipping_option")
    #shipping_reference = payload.get("shipping_option_reference")

    # 1️⃣ Validaciones mínimas
    if not order_id or not store_id:
        raise HTTPException(status_code=400, detail="Invalid order payload")

    print(f"[INFO] Received order webhook: payload={payload}")
    
    # 2️⃣ Ignorar si no es PickNShip
    #if shipping_carrier != PICKNSHIP_NAME:
        #return {"status": "ignored"}

    # 3️⃣ Guardar orden (idempotente)
    # order_saved = save_order_if_new(
    #     order_id=order_id,
    #     store_id=store_id,
    #     status=status,
    #     payload=payload
    # )

    # if not order_saved:
    #     return {"status": "already_processed"}

    # # 4️⃣ Notificar (Slack)
    # await notify_order_created(payload)

    return {"status": "ok"}