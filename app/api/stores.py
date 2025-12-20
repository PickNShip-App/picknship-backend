from fastapi import APIRouter, Depends
from app.core.security import verify_api_key
from app.core.db import list_stores

router = APIRouter(prefix="/stores", dependencies=[Depends(verify_api_key)])

@router.get("/")
def get_stores():
    """
    List all connected stores, including shipping method status
    """
    return {"stores": list_stores()}
