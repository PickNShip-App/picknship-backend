from fastapi import APIRouter, Request
from app.api.utils import is_caba_zipcode

router = APIRouter(prefix="/webhook")

@router.post("/orders")
async def order_webhook(request: Request):
    """Receives order notifications from Tienda Nube"""
    payload = await request.json()
    shipping = payload.get("shipping_address", {})
    zipcode = shipping.get("zip", "")
    store_name = payload.get("store_name", "Unknown Store")
    order_id = payload.get("id")

    if is_caba_zipcode(zipcode):
        # TODO: send email or WhatsApp notification here
        print(f"✅ CABA order received from {store_name}, order {order_id}")
    else:
        print(f"❌ Out of zone order ({zipcode}), ignoring")

    return {"status": "ok"}
