import pandas as pd
import streamlit as st
import altair as alt

from WebApp.core.utils import load_open_transfer_requests, get_fulfilled_by_order


def show_pedidos_abertos():
    st.header("📋 Pedidos de transferência em aberto")
    st.caption("Dados da fct_open_transfer_request_lines (somente leitura – nenhuma alteração). Atendido/pendente a partir dos movimentos.")

    try:
        df = load_open_transfer_requests()
        df_fulfilled = get_fulfilled_by_order()
    except Exception as e:
        st.error(f"Não foi possível carregar os dados: {e}")
        return

    if df.empty:
        st.info("Nenhum pedido em aberto.")
        return

    df = df.copy()
    open_col = "open_quantity" if "open_quantity" in df.columns else ("quantity" if "quantity" in df.columns else None)
    if open_col and "order_id" in df.columns and "item_code" in df.columns and not df_fulfilled.empty:
        df["_solicitado"] = pd.to_numeric(df[open_col], errors="coerce").fillna(0).astype(int)
        df_fulfilled = df_fulfilled.copy()
        df_fulfilled["quantity_fulfilled"] = df_fulfilled["quantity_fulfilled"].fillna(0).astype(int)
        df = df.merge(
            df_fulfilled[["order_id", "item_code", "quantity_fulfilled"]],
            on=["order_id", "item_code"],
            how="left",
        )
        df["atendido"] = df["quantity_fulfilled"].fillna(0).astype(int)
        df["pendente"] = (df["_solicitado"] - df["atendido"]).clip(lower=0).astype(int)
        df = df.drop(columns=["quantity_fulfilled", "_solicitado"], errors="ignore")

    # Coluna transfer_type (se não existir, criar "Todos" só)
    tipo_col = "transfer_type"
    if tipo_col not in df.columns:
        st.warning(f"Coluna '{tipo_col}' não encontrada. Exibindo todos os dados.")
        df[tipo_col] = "—"

    tipos_unicos = ["Todos"] + sorted(df[tipo_col].dropna().astype(str).unique().tolist())

    # --- Dashboard por transfer_type ---
    st.subheader("📊 Dashboard de pedidos")
    order_col = "order_id" if "order_id" in df.columns else df.columns[0]
    count_by_type = (
        df.groupby(tipo_col, as_index=False)
        .agg(linhas=(tipo_col, "count"), pedidos_unicos=(order_col, "nunique"))
        .rename(columns={tipo_col: "tipo"})
        .sort_values("linhas", ascending=False)
    )

    cols = st.columns(min(5, len(count_by_type) + 1))
    for idx, (_, row) in enumerate(count_by_type.iterrows()):
        if idx >= len(cols):
            break
        with cols[idx]:
            st.metric(row["tipo"], int(row["pedidos_unicos"]), f"{int(row['linhas'])} linhas")

    chart_bars = (
        alt.Chart(count_by_type)
        .mark_bar()
        .encode(x=alt.X("tipo:N", sort="-y"), y="pedidos_unicos:Q", color="tipo:N")
        .properties(height=220, title="Pedidos únicos por transfer_type")
    )
    st.altair_chart(chart_bars, use_container_width=True)
    st.dataframe(count_by_type, use_container_width=True, hide_index=True)

    # --- Filtro por transfer_type ---
    st.subheader("🔍 Filtrar por tipo")
    tipo = st.selectbox("Transfer type", tipos_unicos)
    if tipo == "Todos":
        df_filtrado = df.copy()
    else:
        df_filtrado = df[df[tipo_col].astype(str) == tipo].copy()

    # Filtros adicionais
    so_atrasados = False
    from_whs = to_whs = priority = []
    with st.expander("Filtros adicionais (origem, destino, prioridade, atrasados)", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            from_whs = st.multiselect(
                "Origem (from_whs)",
                options=sorted(df_filtrado["from_whs"].dropna().astype(str).unique().tolist()) if "from_whs" in df_filtrado.columns else [],
                default=[],
            )
        with col2:
            to_whs = st.multiselect(
                "Destino (to_whs)",
                options=sorted(df_filtrado["to_whs"].dropna().astype(str).unique().tolist()) if "to_whs" in df_filtrado.columns else [],
                default=[],
            )
        with col3:
            priority = st.multiselect(
                "Prioridade",
                options=sorted(df_filtrado["priority"].dropna().astype(str).unique().tolist()) if "priority" in df_filtrado.columns else [],
                default=[],
            )
        if "is_overdue" in df_filtrado.columns:
            so_atrasados = st.checkbox("Somente atrasados (is_overdue)", value=False)

    if from_whs and "from_whs" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["from_whs"].astype(str).isin(from_whs)]
    if to_whs and "to_whs" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["to_whs"].astype(str).isin(to_whs)]
    if priority and "priority" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["priority"].astype(str).isin(priority)]
    if "is_overdue" in df_filtrado.columns and so_atrasados:
        df_filtrado = df_filtrado[df_filtrado["is_overdue"] == True]

    st.metric("Linhas em aberto (filtrado)", len(df_filtrado))
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")
    nome_arquivo = f"pedidos_{tipo.lower().replace(' ', '_')}.csv" if tipo != "Todos" else "pedidos_todos.csv"
    st.download_button("📥 Exportar CSV", data=csv, file_name=nome_arquivo, mime="text/csv")
