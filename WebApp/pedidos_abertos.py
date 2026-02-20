import pandas as pd
import streamlit as st
import altair as alt

from WebApp.utils import load_open_transfer_requests


def _str_whs(s):
    """Normaliza valor de warehouse para comparação (1.01 == '1.01')."""
    if pd.isna(s):
        return ""
    return str(s).strip()


def _mask_picking(df):
    """(from_whs in [1.01, 1.15]) OR (to_whs == 1.05)."""
    if "from_whs" not in df.columns or "to_whs" not in df.columns:
        return pd.Series(False, index=df.index)
    f = df["from_whs"].apply(_str_whs)
    t = df["to_whs"].apply(_str_whs)
    return (f.isin(["1.01", "1.15"])) | (t == "1.05")


def _mask_inbound(df):
    """(to_whs == 1.01) AND (from_whs != 1.06)."""
    if "from_whs" not in df.columns or "to_whs" not in df.columns:
        return pd.Series(False, index=df.index)
    f = df["from_whs"].apply(_str_whs)
    t = df["to_whs"].apply(_str_whs)
    return (t == "1.01") & (f != "1.06")


def _mask_rma(df):
    """from_whs == 1.16."""
    if "from_whs" not in df.columns:
        return pd.Series(False, index=df.index)
    f = df["from_whs"].apply(_str_whs)
    return f == "1.16"


def _mask_others(df):
    """NOT Picking AND NOT Inbound AND NOT RMA."""
    return ~_mask_picking(df) & ~_mask_inbound(df) & ~_mask_rma(df)


def _tipo_linha(df):
    """Atribui tipo a cada linha: Picking, Inbound, RMA, Others."""
    out = pd.Series("Others", index=df.index)
    out[_mask_picking(df)] = "Picking"
    out[_mask_inbound(df)] = "Inbound"
    out[_mask_rma(df)] = "RMA"
    return out


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

    df = df.copy()
    df["_tipo"] = _tipo_linha(df)

    # --- Dashboard de pedidos ---
    st.subheader("📊 Dashboard de pedidos")
    order_col = "order_id" if "order_id" in df.columns else df.columns[0]
    count_by_type = df.groupby("_tipo", as_index=False).agg(
        linhas=("_tipo", "count"),
        pedidos_unicos=(order_col, "nunique"),
    ).rename(columns={"_tipo": "tipo"})
    count_by_type = count_by_type.sort_values("linhas", ascending=False)

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
        .properties(height=220, title="Pedidos únicos por tipo")
    )
    st.altair_chart(chart_bars, use_container_width=True)

    st.dataframe(count_by_type, use_container_width=True, hide_index=True)

    # --- Filtro por tipo (estrutura da fórmula) ---
    st.subheader("🔍 Filtrar por tipo")
    tipo = st.selectbox(
        "Tipo de pedido",
        ["Todos", "Picking", "Inbound", "RMA", "Others"],
        help="Picking: (origem 1.01/1.15) ou destino 1.05 | Inbound: destino 1.01 e origem ≠1.06 | RMA: origem 1.16 | Others: demais",
    )
    mask_tipo = pd.Series(True, index=df.index)
    if tipo != "Todos":
        mask_tipo = df["_tipo"] == tipo
    df_filtrado = df[mask_tipo].copy()

    # Filtros adicionais
    so_atrasados = False
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

    # Remover coluna auxiliar na exibição
    df_show = df_filtrado.drop(columns=["_tipo"], errors="ignore")

    st.metric("Linhas em aberto (filtrado)", len(df_show))
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    csv = df_show.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Exportar CSV",
        data=csv,
        file_name=f"pedidos_transferencia_{tipo.lower() if tipo != 'Todos' else 'todos'}.csv",
        mime="text/csv",
    )
