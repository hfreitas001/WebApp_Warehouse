"""Depósitos: entrada e saída manual (equivalente a WebApp/pages/depositos.py)."""
import random
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user

router = APIRouter()


class EntradaBody(BaseModel):
    item_code: str
    quantity: int
    address: str


class SaidaBody(BaseModel):
    item_code: str
    quantity: int
    address: str


@router.post("/entrada")
def deposito_entrada(body: EntradaBody, user=Depends(get_current_user)):
    """Registra entrada manual em depósito (Storage Andar 2/3)."""
    from WebApp.core.utils import (
        STORAGES,
        insert_items_to_bq_load_job,
        log_movement,
    )
    import pandas as pd

    item = (body.item_code or "").strip()
    if not item:
        raise HTTPException(status_code=400, detail="Informe o item code.")
    if body.address not in STORAGES:
        raise HTTPException(status_code=400, detail=f"Local deve ser um de: {STORAGES}")
    try:
        box_id = f"DEP-{random.randint(10000, 99999)}"
        df_one = pd.DataFrame([{
            "BoxId": box_id,
            "address": body.address,
            "itemCode": item,
            "quantity": str(body.quantity),
            "uom": "un",
            "BatchId": "N/A",
            "description": "Entrada manual depósito",
            "expiryDate": "N/A",
        }])
        insert_items_to_bq_load_job(df_one)
        log_movement(
            "ENTRADA",
            item,
            str(body.quantity),
            to_address=body.address,
            box_id=box_id,
            description="Entrada manual depósito",
            source="WEBAPP_DEPOSITOS",
        )
        return {"ok": True, "message": f"Entrada registrada: {body.quantity} un. de {item} em {body.address}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/saida")
def deposito_saida(body: SaidaBody, user=Depends(get_current_user)):
    """Registra saída manual de depósito (Storage Andar 2/3)."""
    from WebApp.core.utils import STORAGES, remove_quantity_from_storage, log_movement

    item = (body.item_code or "").strip()
    if not item:
        raise HTTPException(status_code=400, detail="Informe o item code.")
    if body.address not in STORAGES:
        raise HTTPException(status_code=400, detail=f"Local deve ser um de: {STORAGES}")
    ok, err = remove_quantity_from_storage(body.address, item, body.quantity)
    if not ok:
        raise HTTPException(status_code=400, detail=err or "Erro ao registrar saída.")
    try:
        log_movement(
            "SAIDA",
            item,
            body.quantity,
            from_address=body.address,
            description="Saída manual depósito",
            source="WEBAPP_DEPOSITOS",
        )
    except Exception:
        pass
    return {"ok": True, "message": f"Saída registrada: {body.quantity} un. de {item} em {body.address}"}
