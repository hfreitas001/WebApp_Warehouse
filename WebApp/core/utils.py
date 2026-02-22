import json
import os
import base64
import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
from PIL import Image

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    from pyzbar.pyzbar import decode
except ImportError:
    decode = None

# IDs do BigQuery
PROJECT_ID = "tractian-bi"
DATASET_ID = "operations"
TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.operations_webapp_warehouse_instock"

# Depósitos / Storages para controle manual
STORAGES = ["Storage - Andar 2", "Storage - Andar 3"]

# Pedidos de transferência em aberto (somente leitura)
TABLE_OPEN_TRANSFERS = "tractian-bi.operations_dbt.fct_open_transfer_request_lines"

# Movimentações (log de toda entrada/saída/transferência/ajuste)
TABLE_MOVEMENTS = f"{PROJECT_ID}.{DATASET_ID}.operations_webapp_warehouse_movements"

# Raiz WebApp (um nível acima de core/) para CSVs e service-account
_WEBAPP_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _get_credentials():
    """Carrega credenciais: 1) Streamlit Secrets (deploy), 2) Arquivo local, 3) GOOGLE_APPLICATION_CREDENTIALS."""
    try:
        if hasattr(st, "secrets") and st.secrets.get("GCP_CREDENTIALS_JSON"):
            info = json.loads(st.secrets["GCP_CREDENTIALS_JSON"])
            return service_account.Credentials.from_service_account_info(info)
    except (Exception, KeyError):
        pass
    path_to_json = os.path.join(_WEBAPP_ROOT, "service-account.json")
    if not os.path.exists(path_to_json):
        path_to_json = os.path.join(os.path.dirname(__file__), "service-account.json")
    if os.path.exists(path_to_json) and os.path.getsize(path_to_json) > 50:
        try:
            return service_account.Credentials.from_service_account_file(path_to_json)
        except json.JSONDecodeError:
            pass
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
        return service_account.Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    raise FileNotFoundError(
        "Credenciais do BigQuery não encontradas ou inválidas. "
        "Local: service-account.json ou GOOGLE_APPLICATION_CREDENTIALS. "
        "Deploy: em Streamlit Cloud → Settings → Secrets, adicione GCP_CREDENTIALS_JSON com o conteúdo do JSON."
    )


def get_bq_client():
    credentials = _get_credentials()
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


@st.cache_data(ttl=60)
def load_data():
    """Carrega CSVs de itens/endereços a partir da raiz do WebApp."""
    files = {
        "items": "Warehouse App (1).xlsx - item_registration.csv",
        "addr": "Warehouse App (1).xlsx - adress_registration.csv",
    }
    dfs = {}
    for key, name in files.items():
        path = os.path.join(_WEBAPP_ROOT, name)
        dfs[key] = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
    return dfs


def load_stock_from_bq():
    client = get_bq_client()
    return client.query(f"SELECT * FROM `{TABLE_ID}`").to_dataframe()


@st.cache_data(ttl=120)
def load_open_transfer_requests():
    """Pedidos de transferência em aberto (somente leitura)."""
    client = get_bq_client()
    return client.query(f"SELECT * FROM `{TABLE_OPEN_TRANSFERS}`").to_dataframe()


@st.cache_data(ttl=60)
def load_movements_from_bq():
    """Histórico de movimentações (entrada, saída, etc.)."""
    client = get_bq_client()
    return client.query(f"SELECT * FROM `{TABLE_MOVEMENTS}` ORDER BY movement_at DESC").to_dataframe()


@st.cache_data(ttl=60)
def get_fulfilled_by_order():
    """Quantidade já atendida por (order_id, item_code) a partir das movimentações."""
    client = get_bq_client()
    q = f"""
    SELECT order_id, item_code, SUM(SAFE_CAST(quantity AS INT64)) AS quantity_fulfilled
    FROM `{TABLE_MOVEMENTS}`
    WHERE order_id IS NOT NULL AND TRIM(COALESCE(order_id, '')) != ''
    GROUP BY order_id, item_code
    """
    return client.query(q).to_dataframe()


def insert_items_to_bq_load_job(df_to_insert):
    client = get_bq_client()
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    df_to_insert["quantity"] = df_to_insert["quantity"].astype(str)
    job = client.load_table_from_dataframe(df_to_insert, TABLE_ID, job_config=job_config)
    return job.result()


def get_current_user_email():
    """E-mail do usuário logado (Google OIDC). None se não houver login."""
    try:
        return st.session_state.get("user_email")
    except Exception:
        return None


def log_movement(
    movement_type,
    item_code,
    quantity,
    *,
    from_address=None,
    to_address=None,
    box_id=None,
    order_id=None,
    description=None,
    source=None,
    quantity_before=None,
    quantity_after=None,
    movement_at=None,
    user_email=None,
):
    """Registra uma linha na tabela de movimentações. user_email = quem realizou (login Google)."""
    import uuid
    if user_email is None:
        user_email = get_current_user_email()
    client = get_bq_client()
    now = movement_at or datetime.datetime.utcnow()
    movement_id = f"MOV-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    row = {
        "movement_id": movement_id,
        "movement_type": movement_type,
        "movement_at": now,
        "item_code": str(item_code) if item_code else None,
        "quantity": str(quantity) if quantity is not None else None,
        "quantity_before": str(quantity_before) if quantity_before is not None else None,
        "quantity_after": str(quantity_after) if quantity_after is not None else None,
        "from_address": str(from_address) if from_address else None,
        "to_address": str(to_address) if to_address else None,
        "box_id": str(box_id) if box_id else None,
        "order_id": str(order_id) if order_id else None,
        "description": str(description) if description else None,
        "source": str(source) if source else None,
        "user_email": str(user_email) if user_email else None,
    }
    df = pd.DataFrame([row])
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    client.load_table_from_dataframe(df, TABLE_MOVEMENTS, job_config=job_config).result()


def ler_qr_da_imagem(image_file):
    if decode is None:
        return None
    try:
        img = Image.open(image_file)
        decoded = decode(img)
        return decoded[0].data.decode("utf-8") if decoded else None
    except Exception:
        return None


def gerar_qr_base64(codigo):
    if qrcode is None:
        return None
    qr = qrcode.make(codigo)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def parse_date_lote(batch_str):
    try:
        if isinstance(batch_str, str) and len(batch_str) >= 8 and batch_str[:8].isdigit():
            return datetime.datetime.strptime(batch_str[:8], "%Y%m%d")
    except Exception:
        pass
    return datetime.datetime(2099, 12, 31)


def remove_quantity_from_storage(storage, item_code, quantity_to_remove):
    """
    Remove quantidade de um item em um depósito (FEFO).
    Retorna (True, None) em sucesso ou (False, mensagem de erro).
    """
    df = load_stock_from_bq()
    if df.empty:
        return False, "Estoque vazio."
    mask = (df["address"].astype(str).str.strip() == storage.strip()) & (
        df["itemCode"].astype(str).str.strip() == str(item_code).strip()
    )
    rows = df[mask].copy()
    if rows.empty:
        return False, f"Nenhum item '{item_code}' no depósito '{storage}'."
    rows["_qty"] = pd.to_numeric(rows["quantity"], errors="coerce").fillna(0).astype(int)
    rows["_dt"] = rows["BatchId"].apply(parse_date_lote)
    rows = rows.sort_values("_dt")
    need = int(quantity_to_remove)
    if rows["_qty"].sum() < need:
        return False, f"Quantidade insuficiente. Disponível: {int(rows['_qty'].sum())}."
    client = get_bq_client()
    for _, row in rows.iterrows():
        if need <= 0:
            break
        box_id = row["BoxId"]
        qty = int(row["_qty"])
        if qty <= need:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("bid", "STRING", str(box_id))]
            )
            client.query(f"DELETE FROM `{TABLE_ID}` WHERE BoxId = @bid", job_config=job_config).result()
            need -= qty
        else:
            new_qty = qty - need
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("bid", "STRING", str(box_id)),
                    bigquery.ScalarQueryParameter("new_qty", "STRING", str(new_qty)),
                ]
            )
            client.query(
                f"UPDATE `{TABLE_ID}` SET quantity = @new_qty WHERE BoxId = @bid",
                job_config=job_config,
            ).result()
            need = 0
    return True, None
