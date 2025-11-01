from fastapi import APIRouter
from app.core.db import list_stores

router = APIRouter(prefix="/stores")

@router.get("/")
def get_stores():
    return {"stores": list_stores()}
