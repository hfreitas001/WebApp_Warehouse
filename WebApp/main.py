import streamlit as st
from .inbound import show as show_inbound
from .outbound import show as show_outbound
from .dashboards import show as show_dashboards

st.set_page_config(page_title="WMS", page_icon="📦", layout="wide")
st.sidebar.title("📦 WMS")
pagina = st.sidebar.radio("Página", ["Entrada", "Saída", "Estoque"], label_visibility="collapsed")

if pagina == "Entrada":
    show_inbound()
elif pagina == "Saída":
    show_outbound()
else:
    show_dashboards()
