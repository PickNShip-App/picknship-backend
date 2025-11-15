from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.db import save_store, init_db, mark_shipping_created, get_store
from app.services import tiendanube
import httpx

router = APIRouter(prefix="/auth")

TIENDANUBE_AUTH_URL = "https://www.tiendanube.com/apps/authorize"
TIENDANUBE_TOKEN_URL = "https://www.tiendanube.com/apps/authorize/token"

# initialize database
init_db()


@router.get("/install")
async def install_app():
    """
    Redirect store owner to Tienda Nube to authorize app installation
    """
    params = (
        f"?client_id={settings.TIENDANUBE_CLIENT_ID}"
        f"&redirect_uri={settings.TIENDANUBE_REDIRECT_URI}"
        f"&scope=scope=read_content,write_content,read_products,write_products,read_customers,write_customers,read_orders,write_orders,write_shipping"
    )
    return RedirectResponse(url=TIENDANUBE_AUTH_URL + params)


@router.get("/callback")
async def auth_callback(code: str = None, error: str = None):
    """
    Exchange OAuth code for access token, persist store,
    and automatically create PickNShip shipping method
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"Pick'NShip ({settings.PICKNSHIP_EMAIL})"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                TIENDANUBE_TOKEN_URL,
                json={
                    "client_id": settings.TIENDANUBE_CLIENT_ID,
                    "client_secret": settings.TIENDANUBE_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.TIENDANUBE_REDIRECT_URI,
                },
                headers=headers,
                timeout=20.0,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Token request failed: {str(e)}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Token request failed. Raw response: {response.text}"
        )

    try:
        data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse token JSON: {str(e)}")

    access_token = data.get("access_token")
    user_id = data.get("user_id") or data.get("store_id") or data.get("store")
    store_name = data.get("store_name") or data.get("shop_name") or ""

    if not access_token or not user_id:
        raise HTTPException(status_code=400, detail={"msg": "Token response missing fields", "raw": data})

    # Persist store in database
    save_store(store_id=user_id, access_token=access_token, store_name=store_name, shipping_created=False)

    # Automatically create PickNShip shipping method
    try:
        await tiendanube.create_picknship_shipping_method(store_id=user_id, access_token=access_token)
        # Mark as shipping created
        mark_shipping_created(user_id)
    except Exception as e:
        print(f"[WARNING] Could not create PickNShip shipping automatically: {str(e)}")

    return {"message": "Pick'NShip connected successfully!", "store_id": user_id}


@router.post("/shipping/retry/{store_id}")
async def retry_shipping(store_id: str):
    """
    Manually retry creating PickNShip shipping method for a store.
    """
    store = get_store(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    try:
        await tiendanube.create_picknship_shipping_method(store_id=store_id, access_token=store["access_token"])
        mark_shipping_created(store_id)
        return {"message": "PickNShip shipping method created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create shipping method: {str(e)}")
