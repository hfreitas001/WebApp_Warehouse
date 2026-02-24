"""Inbound (batch) e Outbound (confirmar saída) – equivalente ao WebApp."""
import random
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user

router = APIRouter()


class InboundItem(BaseModel):
    itemCode: str
    quantity: int | str
    uom: str | None = "un"
    BatchId: str | None = None
    description: str | None = None
    expiryDate: str | None = "N/A"


class InboundBatchBody(BaseModel):
    address: str
    order_id: str | None = None  # opcional, para fluxo "Atender pedido"
    items: list[InboundItem]


class PickLine(BaseModel):
    boxId: str
    itemCode: str
    quantity: int | str
    from_address: str | None = None


class OutboundConfirmBody(BaseModel):
    order_id: str | None = None
    picks: list[PickLine]


@router.post("/inbound/batch")
def inbound_batch(body: InboundBatchBody, user=Depends(get_current_user)):
    """Registra lote de entrada (fila de bipagem) no BigQuery e no log de movimentações."""
    from WebApp.core.utils import insert_items_to_bq_load_job, log_movement
    import pandas as pd

    if not body.items:
        raise HTTPException(status_code=400, detail="Envie ao menos um item.")
    email = (user.get("email") or "").strip()
    rows = []
    for it in body.items:
        box_id = f"BOX-{random.randint(1000, 9999)}"
        rows.append({
            "BoxId": box_id,
            "address": body.address,
            "itemCode": str(it.itemCode or "").strip(),
            "quantity": str(it.quantity),
            "uom": it.uom or "un",
            "BatchId": it.BatchId or "N/A",
            "description": it.description or "Entrada WebApp",
            "expiryDate": it.expiryDate or "N/A",
        })
    try:
        df = pd.DataFrame(rows)
        insert_items_to_bq_load_job(df)
        for r in rows:
            try:
                log_movement(
                    "ENTRADA",
                    r["itemCode"],
                    r["quantity"],
                    to_address=body.address,
                    box_id=r["BoxId"],
                    order_id=body.order_id,
                    description=(r["description"] + (f" (pedido {body.order_id})" if body.order_id else "")),
                    source="WEBAPP_INBOUND",
                    user_email=email,
                )
            except Exception:
                pass
        return {"ok": True, "message": f"{len(rows)} item(ns) registrado(s)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outbound/confirm")
def outbound_confirm(body: OutboundConfirmBody, user=Depends(get_current_user)):
    """Confirma saída: remove boxes do BigQuery e registra movimentação."""
    from google.cloud import bigquery
    from WebApp.core.utils import get_bq_client, TABLE_ID, log_movement

    if not body.picks:
        raise HTTPException(status_code=400, detail="Envie ao menos um item no plano de picking.")
    email = (user.get("email") or "").strip()
    client = get_bq_client()
    for p in body.picks:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("bid", "STRING", str(p.boxId))]
        )
        client.query(f"DELETE FROM `{TABLE_ID}` WHERE BoxId = @bid", job_config=job_config).result()
        try:
            log_movement(
                "SAIDA",
                p.itemCode,
                str(p.quantity),
                from_address=p.from_address,
                box_id=p.boxId,
                order_id=body.order_id,
                description="Atendimento pedido" if body.order_id else "Picking FEFO",
                source="WEBAPP_OUTBOUND",
                user_email=email,
            )
        except Exception:
            pass
    return {"ok": True, "message": "Baixa realizada."}
