"""Pedidos: lê open e fulfilled do WebApp.core.utils."""
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user

router = APIRouter()


@router.get("/open")
def open_orders(user=Depends(get_current_user)):
    from WebApp.core.utils import load_open_transfer_requests
    try:
        df = load_open_transfer_requests()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fulfilled")
def fulfilled(user=Depends(get_current_user)):
    from WebApp.core.utils import get_fulfilled_by_order
    try:
        df = get_fulfilled_by_order()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
