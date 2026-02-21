import os
import sys

# Garante que a raiz do projeto esteja no path (para streamlit run WebApp/main.py)
_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

import streamlit as st

from WebApp.utils import load_data
from WebApp.inbound import show_inbound
from WebApp.outbound import show_outbound
from WebApp.dashboards import show_dashboards
from WebApp.depositos import show_depositos
from WebApp.pedidos_abertos import show_pedidos_abertos
from WebApp.movimentacoes import show_movimentacoes
from WebApp.lancamentos_manuais import show_lancamentos_manuais

st.set_page_config(page_title="WMS Tractian", layout="wide")

data = load_data()

# --- Sidebar: 3 blocos (expanders), cada um com seu dropdown de ferramentas ---
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inbound"

st.sidebar.title("WMS Tractian")
st.sidebar.markdown("---")

OPCOES_TRANS = ["Inbound", "Outbound", "Ajustments", "Lançamentos manuais"]
OPCOES_REL = ["Movimentações", "Pedidos em aberto"]
OPCOES_DASH = ["Visão geral"]
pagina = st.session_state.pagina


def _ao_clicar_trans():
    st.session_state.pagina = st.session_state.nav_trans


def _ao_clicar_rel():
    st.session_state.pagina = st.session_state.nav_rel


def _ao_clicar_dash():
    st.session_state.pagina = st.session_state.nav_dash


# Bloco 1: Módulos (Transações)
idx_trans = OPCOES_TRANS.index(pagina) if pagina in OPCOES_TRANS else 0
label_modulos = f"Módulos · {pagina}" if pagina in OPCOES_TRANS else "Módulos"
with st.sidebar.expander(label_modulos, expanded=(pagina in OPCOES_TRANS)):
    st.radio(
        "Transações",
        OPCOES_TRANS,
        index=idx_trans,
        key="nav_trans",
        label_visibility="collapsed",
        on_change=_ao_clicar_trans,
    )

# Bloco 2: Relatórios
idx_rel = OPCOES_REL.index(pagina) if pagina in OPCOES_REL else 0
label_rel = f"Relatórios · {pagina}" if pagina in OPCOES_REL else "Relatórios"
with st.sidebar.expander(label_rel, expanded=(pagina in OPCOES_REL)):
    st.radio(
        "Relatórios",
        OPCOES_REL,
        index=idx_rel,
        key="nav_rel",
        label_visibility="collapsed",
        on_change=_ao_clicar_rel,
    )

# Bloco 3: Dashboard geral
idx_dash = OPCOES_DASH.index(pagina) if pagina in OPCOES_DASH else 0
label_dash = f"Dashboard geral · {pagina}" if pagina in OPCOES_DASH else "Dashboard geral"
with st.sidebar.expander(label_dash, expanded=(pagina in OPCOES_DASH)):
    st.radio(
        "Dashboard",
        OPCOES_DASH,
        index=idx_dash,
        key="nav_dash",
        label_visibility="collapsed",
        on_change=_ao_clicar_dash,
    )

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

# --- Roteamento ---
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
else:
    show_dashboards(data)
