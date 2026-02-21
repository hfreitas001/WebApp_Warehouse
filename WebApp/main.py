import os
import sys

# Garante que a raiz do projeto esteja no path (para streamlit run WebApp/main.py)
_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

import pandas as pd
import streamlit as st

from WebApp.admin_usuarios import show_admin_usuarios
from WebApp.auth import can_access_module, get_session_from_cookie, get_user, logout as auth_logout
from WebApp.login_ui import show_login_or_signup
from WebApp.utils import load_data
from WebApp.inbound import show_inbound
from WebApp.outbound import show_outbound
from WebApp.dashboards import show_dashboards
from WebApp.depositos import show_depositos
from WebApp.pedidos_abertos import show_pedidos_abertos
from WebApp.movimentacoes import show_movimentacoes
from WebApp.lancamentos_manuais import show_lancamentos_manuais

# Mapeamento página (label) -> module_id (controle de acesso)
PAGINA_TO_MODULE = {
    "Inbound": "inbound",
    "Outbound": "outbound",
    "Ajustments": "adjustments",
    "Lançamentos manuais": "lancamentos_manuais",
    "Movimentações": "movimentacoes",
    "Pedidos em aberto": "pedidos_abertos",
    "Visão geral": "dashboard",
    "Admin Usuários": "admin_usuarios",
}

st.set_page_config(page_title="WMS Tractian", layout="wide")

# --- Sessão: cookie 7 dias ou login atual
email_from_cookie = get_session_from_cookie()
if email_from_cookie and (not st.session_state.get("user_email") or st.session_state.user_email != email_from_cookie):
    st.session_state.user_email = email_from_cookie
    user = get_user(email_from_cookie)
    if user is not None:
        st.session_state.user_role = str(user.get("role") or "user")
        st.session_state.user_row = user

# --- Sem sessão válida: tela de login/cadastro
if not st.session_state.get("user_email") or not str(st.session_state.user_email).strip():
    show_login_or_signup()
    st.stop()

# --- Usuário logado mas ainda não aprovado
user_row = st.session_state.get("user_row")
if user_row is not None:
    approved_at = user_row.get("approved_at")
    if approved_at is None or pd.isna(approved_at):
        st.warning("Sua conta está aguardando aprovação do administrador. Você será avisado quando for aprovado.")
        if st.button("Sair"):
            auth_logout()
            st.rerun()
        st.stop()

data = load_data()

# --- Sidebar: Transações, Relatórios, Dashboard, Configurações (com controle de acesso) ---
user_row = st.session_state.get("user_row")

def _pode(pagina_label):
    mid = PAGINA_TO_MODULE.get(pagina_label)
    return mid and can_access_module(user_row, mid)

OPCOES_TRANS_FULL = ["Inbound", "Outbound", "Ajustments", "Lançamentos manuais"]
OPCOES_REL_FULL = ["Movimentações", "Pedidos em aberto"]
OPCOES_DASH_FULL = ["Visão geral"]
OPCOES_CONFIG_FULL = ["Admin Usuários"]
OPCOES_TRANS = [p for p in OPCOES_TRANS_FULL if _pode(p)]
OPCOES_REL = [p for p in OPCOES_REL_FULL if _pode(p)]
OPCOES_CONFIG = [p for p in OPCOES_CONFIG_FULL if _pode(p)]

if "pagina" not in st.session_state:
    st.session_state.pagina = (OPCOES_TRANS[0] if OPCOES_TRANS else (OPCOES_REL[0] if OPCOES_REL else (OPCOES_DASH_FULL[0] if _pode("Visão geral") else (OPCOES_CONFIG[0] if OPCOES_CONFIG else "Visão geral"))))

st.sidebar.title("WMS Tractian")
st.sidebar.caption(f"👤 {st.session_state.user_email}")
if st.sidebar.button("Sair", key="btn_logout", use_container_width=True):
    auth_logout()
    st.rerun()
st.sidebar.markdown("---")

pagina = st.session_state.pagina

def _ao_clicar_trans():
    st.session_state.pagina = st.session_state.nav_trans

def _ao_clicar_rel():
    st.session_state.pagina = st.session_state.nav_rel

def _ao_clicar_config():
    st.session_state.pagina = st.session_state.nav_config
    st.rerun()

if OPCOES_TRANS:
    idx_trans = OPCOES_TRANS.index(pagina) if pagina in OPCOES_TRANS else 0
    label_modulos = f"Módulos · {pagina}" if pagina in OPCOES_TRANS else "Módulos"
    with st.sidebar.expander(label_modulos, expanded=(pagina in OPCOES_TRANS)):
        st.radio("Transações", OPCOES_TRANS, index=idx_trans, key="nav_trans", label_visibility="collapsed", on_change=_ao_clicar_trans)

if OPCOES_REL:
    idx_rel = OPCOES_REL.index(pagina) if pagina in OPCOES_REL else 0
    label_rel = f"Relatórios · {pagina}" if pagina in OPCOES_REL else "Relatórios"
    with st.sidebar.expander(label_rel, expanded=(pagina in OPCOES_REL)):
        st.radio("Relatórios", OPCOES_REL, index=idx_rel, key="nav_rel", label_visibility="collapsed", on_change=_ao_clicar_rel)

if _pode("Visão geral"):
    label_dash = f"Dashboard geral · {pagina}" if pagina == "Visão geral" else "Dashboard geral"
    with st.sidebar.expander(label_dash, expanded=(pagina == "Visão geral")):
        if st.button("Visão geral", key="btn_dash", use_container_width=True):
            st.session_state.pagina = "Visão geral"
            st.rerun()

if OPCOES_CONFIG:
    idx_cfg = OPCOES_CONFIG.index(pagina) if pagina in OPCOES_CONFIG else 0
    label_cfg = f"Configurações · {pagina}" if pagina in OPCOES_CONFIG else "Configurações"
    with st.sidebar.expander(label_cfg, expanded=(pagina in OPCOES_CONFIG)):
        st.radio("Config", OPCOES_CONFIG, index=idx_cfg, key="nav_config", label_visibility="collapsed", on_change=_ao_clicar_config)

pagina = st.session_state.pagina

st.sidebar.markdown("---")
compact = st.sidebar.checkbox(
    "Tela compacta (leitora Zebra)",
    value=st.session_state.get("compact_mode", False),
    key="compact_check",
)
st.session_state.compact_mode = compact

if compact:
    st.markdown("""
    <style>
    .main .block-container { padding: 0.4rem 0.6rem 1rem; max-width: 100%%; }
    .stTextArea textarea { font-size: 12px !important; }
    div[data-testid="stVerticalBlock"] > div { padding: 0.2rem 0 !important; }
    .stDataFrame { font-size: 10px !important; max-width: 100%%; }
    .stDataFrame td, .stDataFrame th { padding: 0.15em 0.3em !important; font-size: 10px !important; }
    .stDataFrame table { width: 100%% !important; table-layout: auto !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Roteamento (com verificação de acesso) ---
if not _pode(pagina):
    st.warning("Você não tem permissão para acessar esta página.")
else:
    if pagina == "Inbound":
        show_inbound(data)
    elif pagina == "Outbound":
        show_outbound()
    elif pagina == "Ajustments":
        show_depositos()
    elif pagina == "Lançamentos manuais":
        show_lancamentos_manuais()
    elif pagina == "Movimentações":
        show_movimentacoes()
    elif pagina == "Pedidos em aberto":
        show_pedidos_abertos()
    elif pagina == "Visão geral":
        show_dashboards(data)
    elif pagina == "Admin Usuários":
        show_admin_usuarios()
    else:
        show_dashboards(data)
