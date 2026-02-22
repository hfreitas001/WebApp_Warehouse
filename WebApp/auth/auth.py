"""
Autenticação WMS: login por email/senha, cookie 7 dias, signup com aprovação admin.
Controle de acesso por role (admin/user) e allowed_modules (JSON, granular).
"""
import base64
import datetime
import hashlib
import hmac
import json
import os
import random
import string

import pandas as pd
import streamlit as st
from google.cloud import bigquery

try:
    import bcrypt
except ImportError:
    bcrypt = None

try:
    import extra_streamlit_components as stx
except ImportError:
    stx = None

TABLE_USERS = "tractian-bi.operations.operations_webapp_warehouse_users_wms"
COOKIE_NAME = "wms_session"
COOKIE_MAX_DAYS = 7

# Módulos para controle fino (allowed_modules é uma lista desses IDs).
MODULE_IDS = [
    "inbound",
    "outbound",
    "adjustments",
    "lancamentos_manuais",
    "movimentacoes",
    "pedidos_abertos",
    "dashboard",
    "config_perfil",
    "config_senha",
    "config_endereco_sku",
    "config_params",
    "admin_usuarios",
]


def _get_bq():
    from WebApp.core.utils import get_bq_client
    return get_bq_client()


def _get_cookie_secret():
    try:
        if hasattr(st, "secrets") and st.secrets.get("COOKIE_SECRET"):
            return st.secrets["COOKIE_SECRET"].encode("utf-8")
    except Exception:
        pass
    return (os.environ.get("WMS_COOKIE_SECRET") or "wms-dev-secret-change-in-production").encode("utf-8")


def _get_cookie_manager():
    if stx is None:
        return None
    try:
        return stx.CookieManager()
    except Exception:
        return None


def _sign_session(email: str) -> str:
    exp = (datetime.datetime.utcnow() + datetime.timedelta(days=COOKIE_MAX_DAYS)).timestamp()
    payload = json.dumps({"email": email, "exp": exp}).encode("utf-8")
    b64 = base64.urlsafe_b64encode(payload).decode("utf-8")
    sig = hmac.new(_get_cookie_secret(), payload, hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"


def _verify_session(token: str):
    if not token or "." not in token:
        return None
    b64, sig = token.rsplit(".", 1)
    try:
        payload = base64.urlsafe_b64decode(b64.encode("utf-8"))
    except Exception:
        return None
    if hmac.new(_get_cookie_secret(), payload, hashlib.sha256).hexdigest() != sig:
        return None
    try:
        data = json.loads(payload.decode("utf-8"))
        if data.get("exp", 0) < datetime.datetime.utcnow().timestamp():
            return None
        return data.get("email")
    except Exception:
        return None


def get_session_from_cookie():
    """Retorna o email da sessão se o cookie for válido, senão None."""
    cm = _get_cookie_manager()
    if cm is None:
        return None
    try:
        val = cm.get(cookie=COOKIE_NAME)
        if val:
            return _verify_session(val)
    except Exception:
        pass
    return None


def set_session_cookie(email: str):
    """Grava cookie de sessão (7 dias)."""
    cm = _get_cookie_manager()
    if cm is None:
        return
    try:
        token = _sign_session(email)
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=COOKIE_MAX_DAYS)
        cm.set(COOKIE_NAME, token, expires_at=expires)
    except Exception:
        pass


def clear_session_cookie():
    """Remove o cookie de sessão."""
    cm = _get_cookie_manager()
    if cm is None:
        return
    try:
        cm.delete(COOKIE_NAME)
    except Exception:
        pass


def hash_password(password: str) -> str:
    if bcrypt is None:
        raise RuntimeError("bcrypt não instalado. Instale: pip install bcrypt")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    if bcrypt is None or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def get_user(email: str):
    """Retorna a linha do usuário (dict-like) ou None."""
    if not email or not str(email).strip():
        return None
    client = _get_bq()
    q = f"""
    SELECT email, password_hash, role, allowed_modules, last_login,
           verification_code, verification_sent_at, approved_at, approved_by, created_at
    FROM `{TABLE_USERS}`
    WHERE LOWER(TRIM(email)) = LOWER(TRIM(@email))
    LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", str(email).strip())]
    )
    df = client.query(q, job_config=job_config).to_dataframe()
    if df.empty:
        return None
    return df.iloc[0]


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Verifica credenciais e se usuário está aprovado.
    Retorna (True, "") em sucesso ou (False, mensagem de erro).
    """
    user = get_user(email)
    if user is None:
        return False, "E-mail não encontrado."
    if not check_password(password, str(user.get("password_hash") or "")):
        return False, "Senha incorreta."
    approved_at = user.get("approved_at")
    if approved_at is None or pd.isna(approved_at):
        return False, "Conta aguardando aprovação do administrador. Você será avisado quando for aprovado."
    set_session_cookie(email)
    # Atualizar last_login
    try:
        client = _get_bq()
        client.query("""
            UPDATE `{table}` SET last_login = CURRENT_TIMESTAMP() WHERE LOWER(TRIM(email)) = LOWER(TRIM(@email))
        """.format(table=TABLE_USERS), job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", str(email).strip())]
        )).result()
    except Exception:
        pass
    return True, ""


def signup(email: str, password: str) -> tuple[bool, str]:
    """
    Cria usuário com verification_code e approved_at = NULL.
    Retorna (True, código_6_dígitos) ou (False, mensagem).
    """
    email = str(email).strip().lower()
    if not email or "@" not in email:
        return False, "E-mail inválido."
    if not password or len(password) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres."
    user = get_user(email)
    if user is not None:
        return False, "E-mail já cadastrado."
    code = "".join(random.choices(string.digits, k=6))
    now = datetime.datetime.utcnow()
    client = _get_bq()
    row = {
        "email": email,
        "password_hash": hash_password(password),
        "role": "user",
        "allowed_modules": json.dumps([]),
        "last_login": None,
        "verification_code": code,
        "verification_sent_at": now,
        "approved_at": None,
        "approved_by": None,
        "created_at": now,
    }
    df = pd.DataFrame([row])
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    try:
        client.load_table_from_dataframe(df, TABLE_USERS, job_config=job_config).result()
    except Exception as e:
        return False, f"Erro ao cadastrar: {e}"
    return True, code


def list_pending_users():
    """Usuários com approved_at IS NULL (para admin aprovar)."""
    client = _get_bq()
    q = f"""
    SELECT email, created_at, verification_sent_at
    FROM `{TABLE_USERS}`
    WHERE approved_at IS NULL
    ORDER BY created_at DESC
    """
    return client.query(q).to_dataframe()


def approve_user(email: str, approved_by: str) -> bool:
    """Define approved_at e approved_by para o usuário."""
    client = _get_bq()
    q = f"""
    UPDATE `{TABLE_USERS}`
    SET approved_at = CURRENT_TIMESTAMP(), approved_by = @approved_by
    WHERE LOWER(TRIM(email)) = LOWER(TRIM(@email))
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("email", "STRING", str(email).strip()),
            bigquery.ScalarQueryParameter("approved_by", "STRING", str(approved_by).strip()),
        ]
    )
    client.query(q, job_config=job_config).result()
    return True


def can_access_module(user, module_id: str) -> bool:
    """Admin tem acesso total; user só aos módulos em allowed_modules (JSON array)."""
    if user is None:
        return False
    role = str(user.get("role") or "").strip().lower()
    if role == "admin":
        return True
    raw = user.get("allowed_modules")
    if raw is None or (isinstance(raw, (int, float)) and pd.isna(raw)):
        return False
    try:
        mods = json.loads(raw) if isinstance(raw, str) else raw
        return module_id in (mods or [])
    except Exception:
        return False


def logout():
    """Limpa cookie e session_state."""
    clear_session_cookie()
    for key in ("user_email", "user_role", "user_row"):
        if key in st.session_state:
            del st.session_state[key]
