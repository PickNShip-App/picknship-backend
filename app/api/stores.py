from fastapi import APIRouter
from app.core.db import list_stores

router = APIRouter(prefix="/stores")

@router.get("/")
def get_stores():
    """
    List all connected stores, including shipping method status
    """
    return {"stores": list_stores()}
