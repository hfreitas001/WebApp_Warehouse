import pandas as pd
import streamlit as st

from WebApp.utils import load_open_transfer_requests


def show_pedidos_abertos():
    st.header("📋 Pedidos de transferência em aberto")
    st.caption("Dados da fct_open_transfer_request_lines (somente leitura – nenhuma alteração).")

    try:
        df = load_open_transfer_requests()
    except Exception as e:
        st.error(f"Não foi possível carregar os dados: {e}")
        return

    if df.empty:
        st.info("Nenhum pedido em aberto.")
        return

    # Filtros opcionais
    so_atrasados = False
    with st.expander("🔍 Filtrar", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            from_whs = st.multiselect(
                "Origem (from_whs)",
                options=sorted(df["from_whs"].dropna().unique().tolist()) if "from_whs" in df.columns else [],
                default=[],
            )
        with col2:
            to_whs = st.multiselect(
                "Destino (to_whs)",
                options=sorted(df["to_whs"].dropna().unique().tolist()) if "to_whs" in df.columns else [],
                default=[],
            )
        with col3:
            priority = st.multiselect(
                "Prioridade",
                options=sorted(df["priority"].dropna().unique().tolist()) if "priority" in df.columns else [],
                default=[],
            )
        if "is_overdue" in df.columns:
            so_atrasados = st.checkbox("Somente atrasados (is_overdue)", value=False)

    # Aplicar filtros
    mask = pd.Series(True, index=df.index)
    if from_whs and "from_whs" in df.columns:
        mask &= df["from_whs"].isin(from_whs)
    if to_whs and "to_whs" in df.columns:
        mask &= df["to_whs"].isin(to_whs)
    if priority and "priority" in df.columns:
        mask &= df["priority"].isin(priority)
    if "is_overdue" in df.columns and so_atrasados:
        mask &= df["is_overdue"] == True
    df_filtrado = df[mask].copy()

    st.metric("Linhas em aberto", len(df_filtrado))
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    # Exportar CSV (extrair dados)
    csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Exportar CSV",
        data=csv,
        file_name="pedidos_transferencia_abertos.csv",
        mime="text/csv",
    )
