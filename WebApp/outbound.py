import pandas as pd
import streamlit as st
from google.cloud import bigquery

from WebApp.utils import load_stock_from_bq, get_bq_client, TABLE_ID, parse_date_lote


def show_outbound():
    st.header("📤 Outbound - Saída")
    df_stock = load_stock_from_bq()
    if df_stock.empty:
        return st.warning("Estoque Vazio.")

    with st.form("f_picking"):
        item_p = st.selectbox("SKU", df_stock["itemCode"].unique())
        qtd_p = st.number_input("Qtd", min_value=1)
        if st.form_submit_button("Gerar Plano"):
            stock = df_stock[df_stock["itemCode"] == item_p].copy()
            stock["dt_lote"] = stock["BatchId"].apply(parse_date_lote)
            st.session_state.pick_list = stock.sort_values(by="dt_lote")

    if "pick_list" in st.session_state:
        st.dataframe(st.session_state.pick_list, use_container_width=True)
        if st.button("🚀 Confirmar Saída", type="primary"):
            client = get_bq_client()
            for bid in st.session_state.pick_list["BoxId"]:
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("bid", "STRING", str(bid))]
                )
                client.query(f"DELETE FROM `{TABLE_ID}` WHERE BoxId = @bid", job_config=job_config).result()
            st.success("Baixa realizada!")
            del st.session_state.pick_list
            st.rerun()
