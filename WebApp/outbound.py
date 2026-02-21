import pandas as pd
import streamlit as st
from google.cloud import bigquery

from WebApp.utils import (
    load_stock_from_bq,
    get_bq_client,
    TABLE_ID,
    parse_date_lote,
    log_movement,
    load_open_transfer_requests,
    get_fulfilled_by_order,
)

ORDER_ID_COL = "order_id"
ITEM_CODE_COL = "item_code"
OPEN_QTY_COL = "open_quantity"
QTY_COL = "quantity"


def _outbound_atender_pedido():
    """Saída vinculada a um pedido: seleciona linha do pedido, gera picking com qtd <= pendente, log com order_id."""
    try:
        df_orders = load_open_transfer_requests()
        df_fulfilled = get_fulfilled_by_order()
        df_stock = load_stock_from_bq()
    except Exception as e:
        st.error(f"Não foi possível carregar: {e}")
        return
    if df_stock.empty:
        st.warning("Estoque vazio.")
        return
    if df_orders.empty:
        st.warning("Nenhum pedido em aberto.")
        return
    req_id = ORDER_ID_COL if ORDER_ID_COL in df_orders.columns else None
    req_item = ITEM_CODE_COL if ITEM_CODE_COL in df_orders.columns else None
    req_open = OPEN_QTY_COL if OPEN_QTY_COL in df_orders.columns else (QTY_COL if QTY_COL in df_orders.columns else None)
    if not req_id or not req_item or not req_open:
        st.error("Tabela de pedidos sem order_id, item_code ou open_quantity.")
        return
    df_orders = df_orders.copy()
    df_orders["_open_qty"] = pd.to_numeric(df_orders[req_open], errors="coerce").fillna(0).astype(int)
    if not df_fulfilled.empty and "order_id" in df_fulfilled.columns and "item_code" in df_fulfilled.columns:
        df_fulfilled["quantity_fulfilled"] = df_fulfilled["quantity_fulfilled"].fillna(0).astype(int)
        df_orders = df_orders.merge(
            df_fulfilled[["order_id", "item_code", "quantity_fulfilled"]],
            left_on=[req_id, req_item], right_on=["order_id", "item_code"], how="left",
        )
        df_orders["atendido"] = df_orders["quantity_fulfilled"].fillna(0).astype(int)
    else:
        df_orders["atendido"] = 0
    df_orders["pendente"] = (df_orders["_open_qty"] - df_orders["atendido"]).clip(lower=0).astype(int)
    df_orders = df_orders[df_orders["pendente"] > 0].copy()
    if df_orders.empty:
        st.info("Nenhuma linha com quantidade pendente.")
        return
    df_orders["_label"] = (
        df_orders[req_id].astype(str) + " | " + df_orders[req_item].astype(str)
        + " | solicitado: " + df_orders["_open_qty"].astype(str)
        + " | atendido: " + df_orders["atendido"].astype(str)
        + " | pendente: " + df_orders["pendente"].astype(str)
    )
    opcoes = df_orders["_label"].tolist()
    idx_map = {opcoes[i]: i for i in range(len(opcoes))}
    sel = st.selectbox("Selecione a linha do pedido", opcoes, key="out_sel_order")
    idx = idx_map[sel]
    row = df_orders.iloc[idx]
    order_id = str(row[req_id])
    item_code = str(row[req_item])
    pendente = int(row["pendente"])
    stock_item = df_stock[df_stock["itemCode"].astype(str) == item_code]
    disponivel = pd.to_numeric(stock_item["quantity"], errors="coerce").fillna(0).sum()
    qtd_max = min(pendente, int(disponivel)) if disponivel else 0
    if qtd_max <= 0:
        st.warning(f"Sem estoque suficiente para o item {item_code} (pendente: {pendente}).")
        return
    with st.form("f_outbound_pedido"):
        st.caption(f"**Pedido** {order_id} · **Item** {item_code} · **Pendente** {pendente} · **Disponível** {int(disponivel)}")
        qtd_saida = st.number_input("Quantidade a dar saída", min_value=1, max_value=qtd_max, value=min(1, qtd_max))
        if st.form_submit_button("Gerar plano de picking"):
            stock = stock_item.copy()
            stock["dt_lote"] = stock["BatchId"].apply(parse_date_lote)
            stock = stock.sort_values("dt_lote")
            acum = 0
            pick_rows = []
            for _, r in stock.iterrows():
                if acum >= qtd_saida:
                    break
                q = int(pd.to_numeric(r["quantity"], errors="coerce") or 0)
                if q <= 0:
                    continue
                pick_rows.append(r)
                acum += q
            if pick_rows:
                st.session_state.pick_list = pd.DataFrame(pick_rows)
                st.session_state.pick_list_order_id = order_id
            st.rerun()

    if "pick_list" in st.session_state and "pick_list_order_id" in st.session_state:
        st.dataframe(st.session_state.pick_list, use_container_width=True)
        if st.button("🚀 Confirmar Saída (atender pedido)", type="primary"):
            client = get_bq_client()
            pl = st.session_state.pick_list
            oid = st.session_state.pick_list_order_id
            for _, r in pl.iterrows():
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("bid", "STRING", str(r["BoxId"]))]
                )
                client.query(f"DELETE FROM `{TABLE_ID}` WHERE BoxId = @bid", job_config=job_config).result()
                try:
                    log_movement("SAIDA", r["itemCode"], r["quantity"], from_address=r.get("address"), box_id=r["BoxId"], order_id=oid, description=f"Atendimento pedido {oid}", source="WEBAPP_OUTBOUND")
                except Exception:
                    pass
            st.success("Baixa realizada!")
            del st.session_state.pick_list
            del st.session_state.pick_list_order_id
            st.rerun()


def show_outbound():
    st.header("📤 Outbound - Saída")
    fluxo = st.radio("Fluxo:", ["Picking livre", "Atender pedido"], horizontal=True, key="out_fluxo")
    if fluxo == "Atender pedido":
        _outbound_atender_pedido()
        return

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
            st.session_state.pick_list_order_id = None

    if "pick_list" in st.session_state:
        st.dataframe(st.session_state.pick_list, use_container_width=True)
        if st.button("🚀 Confirmar Saída", type="primary"):
            client = get_bq_client()
            pl = st.session_state.pick_list
            oid = st.session_state.get("pick_list_order_id")
            for _, row in pl.iterrows():
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("bid", "STRING", str(row["BoxId"]))]
                )
                client.query(f"DELETE FROM `{TABLE_ID}` WHERE BoxId = @bid", job_config=job_config).result()
                try:
                    log_movement(
                        "SAIDA",
                        row["itemCode"],
                        row["quantity"],
                        from_address=row.get("address"),
                        box_id=row["BoxId"],
                        order_id=oid if oid else None,
                        description="Picking FEFO",
                        source="WEBAPP_OUTBOUND",
                    )
                except Exception:
                    pass
            st.success("Baixa realizada!")
            del st.session_state.pick_list
            if "pick_list_order_id" in st.session_state:
                del st.session_state.pick_list_order_id
            st.rerun()
