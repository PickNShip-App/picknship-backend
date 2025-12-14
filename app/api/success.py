from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.db import get_store
from app.core.config import settings

router = APIRouter()


@router.get("/success", response_class=HTMLResponse)
async def success_page(request: Request, store_id: str | None = None):
    store_url = ""

    if store_id:
        store = get_store(store_id)
        if store:
            store_url = store.get("domain", "")

    return request.app.state.templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "store_url": store_url,
            "logo_url": settings.LOGO_URL
        }
    )