import streamlit as st
from .utils import load_data
from .inbound import show as show_inbound
from .outbound import show as show_outbound
from .dashboards import show as show_dashboards

st.set_page_config(page_title="WMS Tractian", page_icon="📦", layout="wide")
st.sidebar.title("📦 WMS")
pagina = st.sidebar.radio("Módulo", ["Inbound", "Outbound", "Dashboard"], label_visibility="collapsed")

if pagina == "Inbound":
    show_inbound(load_data())
elif pagina == "Outbound":
    show_outbound()
else:
    show_dashboards()
