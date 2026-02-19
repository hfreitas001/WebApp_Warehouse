import pandas as pd
import streamlit as st
import altair as alt
from .utils import get_stock


def show():
    st.header("📊 Dashboard - Estoque")
    df = get_stock()
    if df.empty:
        st.info("Nenhum item em estoque.")
        return

    qtd_num = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    c1, c2 = st.columns(2)
    c1.metric("Volumes (linhas)", len(df))
    c2.metric("Quantidade total", int(qtd_num.sum()))

    if "address" in df.columns and "itemCode" in df.columns and len(df) > 0:
        df_chart = df.copy()
        df_chart["quantity"] = pd.to_numeric(df_chart["quantity"], errors="coerce").fillna(0)
        chart = (
            alt.Chart(df_chart)
            .mark_bar()
            .encode(x="address:N", y="sum(quantity):Q", color="itemCode:N")
            .properties(height=280)
        )
        st.altair_chart(chart, use_container_width=True)

    st.dataframe(df, use_container_width=True, hide_index=True)
