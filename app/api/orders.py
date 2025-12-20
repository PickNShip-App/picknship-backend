from fastapi import APIRouter, Depends
from app.core.security import verify_api_key
from app.core.db import list_orders

router = APIRouter(
    prefix="/orders",
    dependencies=[Depends(verify_api_key)]
)

@router.get("")
def get_orders():
    return list_orders()