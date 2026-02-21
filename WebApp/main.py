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

# --- Sidebar: navegação profissional (Módulos · Relatórios · Dashboard) ---
st.sidebar.title("WMS Tractian")
st.sidebar.markdown("---")
st.sidebar.markdown("**Módulos** · *Transações*")
st.sidebar.caption("Inbound · Outbound · Ajustments · Lançamentos manuais")
st.sidebar.markdown("**Relatórios**")
st.sidebar.caption("Movimentações · Pedidos em aberto")
st.sidebar.markdown("**Dashboard geral**")
st.sidebar.caption("Visão geral")
st.sidebar.markdown("---")

opcoes = [
    "Inbound",
    "Outbound",
    "Ajustments",
    "Lançamentos manuais",
    "Movimentações",
    "Pedidos em aberto",
    "Visão geral",
]
pagina = st.sidebar.selectbox("Página", opcoes, label_visibility="collapsed", key="nav_pagina")

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
