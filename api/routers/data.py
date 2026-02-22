"""Dados: lê load_data e estoque do WebApp.core.utils (somente leitura)."""
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user

router = APIRouter()


@router.get("/load")
def data_load(user=Depends(get_current_user)):
    from WebApp.core.utils import load_data
    try:
        dfs = load_data()
        items = dfs.get("items")
        addr = dfs.get("addr")
        return {
            "items": items.to_dict(orient="records") if hasattr(items, "to_dict") else [],
            "addr": addr.to_dict(orient="records") if hasattr(addr, "to_dict") else [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock")
def stock(user=Depends(get_current_user)):
    from WebApp.core.utils import load_stock_from_bq
    try:
        df = load_stock_from_bq()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storages")
def storages(user=Depends(get_current_user)):
    from WebApp.core.utils import STORAGES
    return STORAGES
