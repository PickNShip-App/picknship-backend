from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.core.config import settings
import httpx
from app.core.db import save_store, init_db

router = APIRouter(prefix="/auth")

# Tienda Nube URLs
TIENDANUBE_AUTH_URL = "https://www.tiendanube.com/apps/authorize"
TIENDANUBE_TOKEN_URL = "https://www.tiendanube.com/apps/authorize/token"

init_db()

@router.get("/install")
async def install_app():
    """Redirect store owner to Tienda Nube OAuth install page"""
    params = (
        f"?client_id={settings.TIENDANUBE_CLIENT_ID}"
        f"&redirect_uri={settings.TIENDANUBE_REDIRECT_URI}"
    )
    return RedirectResponse(url=TIENDANUBE_AUTH_URL + params)


@router.get("/callback")
async def auth_callback(code: str = None, error: str = None):
    """Exchange authorization code for access token and save store info"""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"Pick'NShip ({settings.PICKNSHIP_EMAIL})"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            TIENDANUBE_TOKEN_URL,
            json={
                "client_id": settings.TIENDANUBE_CLIENT_ID,
                "client_secret": settings.TIENDANUBE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.TIENDANUBE_REDIRECT_URI
            },
            headers=headers,
            timeout=20.0,
        )

        # Handle non-200 responses
        if response.status_code != 200:
            print("[ERROR] Token request failed")
            print("Status:", response.status_code)
            print("Headers:", response.headers)
            print("Content (first 1000 chars):", response.text[:1000])
            raise HTTPException(
                status_code=response.status_code,
                detail="Token request failed. See logs for details."
            )

        # Parse JSON safely
        try:
            data = response.json()
        except Exception:
            print("[ERROR] Failed to parse JSON from token response")
            print("Response content (first 2000 chars):", response.text[:2000])
            raise HTTPException(
                status_code=500,
                detail="Failed to parse token JSON. Check logs for full response."
            )

    # Extract token & store info
    access_token = data.get("access_token")
    user_id = data.get("user_id") or data.get("store_id") or data.get("store")
    store_name = data.get("store_name") or data.get("shop_name") or ""

    if not access_token or not user_id:
        raise HTTPException(
            status_code=400,
            detail={
                "msg": "Token response missing required fields",
                "raw_response": data
            }
        )

    # Save to DB
    save_store(store_id=user_id, access_token=access_token, store_name=store_name)

    return {"message": "Pick'NShip connected successfully!", "store_id": user_id}
