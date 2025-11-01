from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from app.core.config import settings
import httpx
from app.core.db import save_store, init_db

router = APIRouter(prefix="/auth")

TIENDANUBE_AUTH_URL = "https://www.tiendanube.com/apps/authorize"
TIENDANUBE_TOKEN_URL = "https://www.tiendanube.com/apps/token"

init_db()

@router.get("/install")
async def install_app():
    params = (
        f"?client_id={settings.TIENDANUBE_CLIENT_ID}"
        f"&redirect_uri={settings.TIENDANUBE_REDIRECT_URI}"
    )
    return RedirectResponse(url=TIENDANUBE_AUTH_URL + params)

@router.get("/callback")
async def auth_callback(code: str = None, error: str = None):
    """Exchange code for token and persist the store + token"""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            TIENDANUBE_TOKEN_URL,
            json={
                "client_id": settings.TIENDANUBE_CLIENT_ID,
                "client_secret": settings.TIENDANUBE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.TIENDANUBE_REDIRECT_URI  # MUST match dashboard
            },
            timeout=20.0,
        )

        # Check if the response is OK
        if response.status_code != 200:
            # Log raw response for debugging
            print(f"[ERROR] Token request failed with status {response.status_code}")
            print(response.text)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Token request failed. Raw response: {response.text}"
            )

        try:
            data = response.json()
        except Exception as e:
            print("[ERROR] Failed to parse JSON from token response:")
            print(response.text)
            raise HTTPException(status_code=500, detail=f"Failed to parse token JSON: {str(e)}")

    access_token = data.get("access_token")
    user_id = data.get("user_id") or data.get("store_id") or data.get("store")  # flexible field names
    store_name = data.get("store_name") or data.get("shop_name") or ""

    if not access_token or not user_id:
        raise HTTPException(status_code=400, detail={"msg": "Token response missing fields", "raw": data})

    # persist
    save_store(store_id=user_id, access_token=access_token, store_name=store_name)

    return {"message": "Pick'NShip connected successfully!", "store_id": user_id}
