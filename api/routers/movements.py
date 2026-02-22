"""Movimentações: lista (lê) e registra (chama log_movement do WebApp)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user

router = APIRouter()


@router.get("")
def list_movements(user=Depends(get_current_user)):
    from WebApp.core.utils import load_movements_from_bq
    try:
        df = load_movements_from_bq()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LogMovementBody(BaseModel):
    movement_type: str
    item_code: str
    quantity: int | str
    from_address: str | None = None
    to_address: str | None = None
    order_id: str | None = None
    description: str | None = None
    source: str | None = None


@router.post("")
def log_movement(body: LogMovementBody, user=Depends(get_current_user)):
    from WebApp.core.utils import log_movement as do_log
    email = user.get("email") or ""
    try:
        do_log(
            body.movement_type,
            body.item_code,
            str(body.quantity),
            from_address=body.from_address,
            to_address=body.to_address,
            order_id=body.order_id,
            description=body.description,
            source=body.source or "WEBAPP_API",
            user_email=email,
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
