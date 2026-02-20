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

st.set_page_config(page_title="WMS Tractian 2026", layout="wide")

data = load_data()

st.sidebar.title("📦 WMS Menu")
mode = st.sidebar.selectbox("Módulo:", ["Inbound", "Outbound", "Dashboard"])

if mode == "Inbound":
    show_inbound(data)
elif mode == "Outbound":
    show_outbound()
else:
    show_dashboards(data)
