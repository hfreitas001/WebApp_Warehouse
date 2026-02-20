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


def _get_credentials():
    """Carrega credenciais: 1) Streamlit Secrets (deploy), 2) Arquivo local, 3) GOOGLE_APPLICATION_CREDENTIALS."""
    try:
        if hasattr(st, "secrets") and st.secrets.get("GCP_CREDENTIALS_JSON"):
            info = json.loads(st.secrets["GCP_CREDENTIALS_JSON"])
            return service_account.Credentials.from_service_account_info(info)
    except (Exception, KeyError):
        pass
    path_to_json = os.path.join(os.path.dirname(__file__), "..", "service-account.json")
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
    base_dir = os.path.dirname(__file__)
    files = {
        "items": "Warehouse App (1).xlsx - item_registration.csv",
        "addr": "Warehouse App (1).xlsx - adress_registration.csv",
    }
    dfs = {}
    for key, name in files.items():
        path = os.path.join(base_dir, name)
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


def insert_items_to_bq_load_job(df_to_insert):
    client = get_bq_client()
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    df_to_insert["quantity"] = df_to_insert["quantity"].astype(str)
    job = client.load_table_from_dataframe(df_to_insert, TABLE_ID, job_config=job_config)
    return job.result()


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
