"""
App WMS. Execute: streamlit run run_wms.py
O código abaixo precisa rodar a cada interação; por isso está aqui e não só no import.
"""
import os
import sys

_raiz = os.path.dirname(os.path.abspath(__file__))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

import streamlit as st
from WebApp.utils import load_data
from WebApp.inbound import show as show_inbound
from WebApp.outbound import show as show_outbound
from WebApp.dashboards import show as show_dashboards

st.set_page_config(page_title="WMS Tractian", page_icon="📦", layout="wide")
st.sidebar.title("📦 WMS")
pagina = st.sidebar.radio(
    "Módulo",
    ["Inbound", "Outbound", "Dashboard"],
    label_visibility="collapsed",
)

if pagina == "Inbound":
    data = load_data()
    show_inbound(data)
elif pagina == "Outbound":
    show_outbound()
else:
    show_dashboards()
