from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.core.config import settings
import httpx

router = APIRouter(prefix="/auth")

TIENDANUBE_AUTH_URL = "https://www.tiendanube.com/apps/authorize"
TIENDANUBE_TOKEN_URL = "https://www.tiendanube.com/apps/token"

@router.get("/install")
async def install_app():
    """Step 1: Redirect merchant to Tienda Nube authorization screen"""
    params = (
        f"?client_id={settings.TIENDANUBE_CLIENT_ID}"
        f"&redirect_uri={settings.TIENDANUBE_REDIRECT_URI}"
    )
    return RedirectResponse(url=TIENDANUBE_AUTH_URL + params)

@router.get("/callback")
async def auth_callback(code: str):
    """Step 2: Exchange code for access_token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TIENDANUBE_TOKEN_URL,
            json={
                "client_id": settings.TIENDANUBE_CLIENT_ID,
                "client_secret": settings.TIENDANUBE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
            },
        )
    data = response.json()
    access_token = data.get("access_token")

    # TODO: store access_token and store_id in your DB for future use

    return {"message": "Pick'NShip connected successfully!", "token": access_token}
