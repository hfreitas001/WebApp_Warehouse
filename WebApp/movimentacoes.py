import pandas as pd
import streamlit as st

# Tabela de movimentações (evita depender de load_movements_from_bq no utils em deploys antigos)
TABLE_MOVEMENTS = "tractian-bi.operations.operations_webapp_warehouse_movements"


def show_movimentacoes():
    st.header("📜 Histórico de movimentações")
    st.caption("Registro de entradas, saídas e movimentações (tabela operations_webapp_warehouse_movements).")

    try:
        from WebApp.utils import get_bq_client
        client = get_bq_client()
        df = client.query(f"SELECT * FROM `{TABLE_MOVEMENTS}` ORDER BY movement_at DESC").to_dataframe()
    except Exception as e:
        st.error(f"Não foi possível carregar: {e}")
        return

    if df.empty:
        st.info("Nenhuma movimentação registrada ainda.")
        return

    df = df.copy()
    if "movement_at" in df.columns:
        df["movement_at"] = pd.to_datetime(df["movement_at"], errors="coerce")

    # Filtros
    with st.expander("🔍 Filtrar", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            tipo = st.multiselect(
                "Tipo",
                options=sorted(df["movement_type"].dropna().unique().tolist()) if "movement_type" in df.columns else [],
                default=[],
            )
        with c2:
            source = st.multiselect(
                "Origem (source)",
                options=sorted(df["source"].dropna().unique().tolist()) if "source" in df.columns else [],
                default=[],
            )
        with c3:
            item = st.text_input("Item (item_code)", placeholder="Ex: SKU-001")

    mask = pd.Series(True, index=df.index)
    if tipo and "movement_type" in df.columns:
        mask &= df["movement_type"].isin(tipo)
    if source and "source" in df.columns:
        mask &= df["source"].isin(source)
    if item and item.strip() and "item_code" in df.columns:
        mask &= df["item_code"].astype(str).str.contains(item.strip(), case=False, na=False)
    df_filtrado = df[mask].copy()

    st.metric("Registros", len(df_filtrado))
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Exportar CSV", data=csv, file_name="movimentacoes.csv", mime="text/csv")
