import pandas as pd
import streamlit as st
import altair as alt

from WebApp.core.utils import load_stock_from_bq


def show_dashboards(data):
    st.header("📊 Dashboard de Operações")
    df = load_stock_from_bq()
    if not df.empty:
        df = df.copy()
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
        c1, c2 = st.columns(2)
        c1.metric("Volumes em Estoque", len(df))
        c2.metric("Qtd Total Itens", int(df["quantity"].sum()))

        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(x="address:N", y="sum(quantity):Q", color="itemCode:N")
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado em estoque.")
