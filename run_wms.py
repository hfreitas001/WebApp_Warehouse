"""
WMS Tractian. Execute: streamlit run run_wms.py
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
pagina = st.sidebar.radio("Módulo", ["Inbound", "Outbound", "Dashboard"], label_visibility="collapsed")

if pagina == "Inbound":
    show_inbound(load_data())
elif pagina == "Outbound":
    show_outbound()
else:
    show_dashboards()
