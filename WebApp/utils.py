import os
import datetime
import pandas as pd
import streamlit as st

COLUNAS = [
    "BoxId", "address", "itemCode", "quantity", "uom",
    "BatchId", "description", "expiryDate",
]


def get_stock():
    if "stock" not in st.session_state:
        st.session_state.stock = pd.DataFrame(columns=COLUNAS)
    df = st.session_state.stock
    if not all(c in df.columns for c in COLUNAS):
        st.session_state.stock = pd.DataFrame(columns=COLUNAS)
    return st.session_state.stock.copy()


def add_to_stock(linhas):
    """linhas: dict (uma linha) ou DataFrame (várias)."""
    if "stock" not in st.session_state:
        st.session_state.stock = pd.DataFrame(columns=COLUNAS)
    df = pd.DataFrame([linhas]) if isinstance(linhas, dict) else linhas.copy()
    for c in COLUNAS:
        if c not in df.columns:
            df[c] = "" if c != "quantity" else 0
    df["quantity"] = df["quantity"].astype(str)
    df = df[COLUNAS]
    st.session_state.stock = pd.concat(
        [st.session_state.stock, df], ignore_index=True
    )


def remove_from_stock(box_ids):
    """box_ids: string (um BoxId) ou lista."""
    if "stock" not in st.session_state:
        return
    ids = [box_ids] if isinstance(box_ids, str) else box_ids
    if not ids:
        return
    st.session_state.stock = st.session_state.stock[
        ~st.session_state.stock["BoxId"].isin(ids)
    ].reset_index(drop=True)


def parse_date_lote(batch_str):
    """Data do lote (YYYYMMDD) para ordenação FEFO."""
    try:
        if isinstance(batch_str, str) and len(batch_str) >= 8 and batch_str[:8].isdigit():
            return datetime.datetime.strptime(batch_str[:8], "%Y%m%d")
    except Exception:
        pass
    return datetime.datetime(2099, 12, 31)


@st.cache_data(ttl=60)
def load_data():
    """CSV de endereços/itens (opcional). Retorna dict com chaves items e addr."""
    base = os.path.dirname(os.path.abspath(__file__))
    files = {
        "items": "Warehouse App (1).xlsx - item_registration.csv",
        "addr": "Warehouse App (1).xlsx - adress_registration.csv",
    }
    out = {}
    for key, name in files.items():
        path = os.path.join(base, name)
        try:
            out[key] = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
        except Exception:
            out[key] = pd.DataFrame()
    return out
