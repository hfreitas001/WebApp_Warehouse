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

st.set_page_config(page_title="WMS Tractian 2026", layout="wide")

data = load_data()

st.sidebar.title("📦 WMS Menu")
mode = st.sidebar.selectbox("Módulo:", ["Inbound", "Outbound", "Depósitos", "Movimentações", "Pedidos em aberto", "Dashboard"])
compact = st.sidebar.checkbox("Tela pequena (leitora Zebra)", value=st.session_state.get("compact_mode", False), key="compact_check")
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

if mode == "Inbound":
    show_inbound(data)
elif mode == "Outbound":
    show_outbound()
elif mode == "Depósitos":
    show_depositos()
elif mode == "Movimentações":
    show_movimentacoes()
elif mode == "Pedidos em aberto":
    show_pedidos_abertos()
else:
    show_dashboards(data)
