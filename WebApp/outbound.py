import pandas as pd
import streamlit as st
from .utils import get_stock, parse_date_lote, remove_from_stock


def show():
    st.header("📤 Outbound - Saída")
    df = get_stock()
    if df.empty or "itemCode" not in df.columns:
        st.warning("Estoque vazio. Use Inbound para adicionar itens.")
        return

    skus = df["itemCode"].dropna().unique().tolist()
    if not skus:
        st.warning("Estoque vazio.")
        return

    with st.form("out_picking"):
        item = st.selectbox("SKU", skus, key="out_sku")
        qtd = st.number_input("Quantidade", min_value=1, value=1, key="out_qtd")
        if st.form_submit_button("Gerar plano de picking"):
            stock = df[df["itemCode"] == item].copy()
            stock["_dt_lote"] = stock["BatchId"].apply(parse_date_lote)
            stock = stock.sort_values("_dt_lote")
            st.session_state.pick_list = stock.drop(columns=["_dt_lote"])
            st.rerun()

    if "pick_list" in st.session_state:
        pl = st.session_state.pick_list
        st.subheader("Plano de picking (FEFO)")
        st.dataframe(pl, use_container_width=True, hide_index=True)
        if st.button("🚀 Confirmar saída", type="primary", key="out_confirmar"):
            remove_from_stock(pl["BoxId"].tolist())
            del st.session_state.pick_list
            st.success("Baixa realizada.")
            st.rerun()
