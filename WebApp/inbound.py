import json
import random
import time

import pandas as pd
import streamlit as st

from WebApp.utils import (
    ler_qr_da_imagem,
    insert_items_to_bq_load_job,
    log_movement,
    load_open_transfer_requests,
    get_fulfilled_by_order,
)

# Colunas da base de pedidos em aberto (open_orders / fct_open_transfer_request_lines)
tipo_col = "transfer_type"
ORDER_ID_COL = "order_id"
ITEM_CODE_COL = "item_code"
OPEN_QTY_COL = "open_quantity"
QTY_COL = "quantity"


def _inbound_atender_pedido(data):
    """Entrada vinculada a um pedido em aberto. Seleção: type → order_id → item (linha)."""
    try:
        df_orders = load_open_transfer_requests()
        df_fulfilled = get_fulfilled_by_order()
    except Exception as e:
        st.error(f"Não foi possível carregar pedidos: {e}")
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
    # Coluna tipo = transfer_type da base open_orders (como em pedidos_abertos)
    if tipo_col not in df_orders.columns:
        df_orders[tipo_col] = "—"
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
        st.info("Nenhuma linha de pedido com quantidade pendente.")
        return

    # 1) Tipo = coluna transfer_type da base open_orders → 2) Pedido (order_id) → 3) Item (linha)
    tipos = sorted(df_orders[tipo_col].dropna().astype(str).unique().tolist())
    tipo_sel = st.selectbox("Tipo", tipos, key="in_type", help="Coluna transfer_type da base de pedidos em aberto.")
    df_orders = df_orders[df_orders[tipo_col].astype(str) == tipo_sel].copy()
    if df_orders.empty:
        st.warning("Nenhuma linha pendente para este tipo.")
        return
    orders_unicos = sorted(df_orders[req_id].dropna().astype(str).unique().tolist())
    order_sel = st.selectbox("Pedido (order_id)", orders_unicos, key="in_order")
    df_order = df_orders[df_orders[req_id].astype(str) == order_sel].copy()
    df_order["_label"] = (
        df_order[req_item].astype(str)
        + " | solicitado: " + df_order["_open_qty"].astype(str)
        + " | atendido: " + df_order["atendido"].astype(str)
        + " | pendente: " + df_order["pendente"].astype(str)
    )
    opcoes = df_order["_label"].tolist()
    idx_map = {opcoes[i]: i for i in range(len(opcoes))}
    sel = st.selectbox("Item (linha do pedido)", opcoes, key="in_item")
    idx = idx_map[sel]
    row = df_order.iloc[idx]
    order_id = str(row[req_id])
    item_code = str(row[req_item])
    pendente = int(row["pendente"])
    with st.form("f_inbound_pedido"):
        st.caption(f"**Pedido** {order_id} · **Item** {item_code} · **Pendente** {pendente}")
        qtd = st.number_input("Quantidade a dar entrada", min_value=1, max_value=pendente, value=min(1, pendente))
        enderecos = data["addr"]["Adress"].unique().tolist() if not data["addr"].empty and "Adress" in data["addr"].columns else ["D1"]
        endereco = st.selectbox("Endereço", enderecos)
        if st.form_submit_button("Registrar entrada (atender pedido)"):
            box_id = f"BOX-{random.randint(1000, 9999)}"
            df_one = pd.DataFrame([{
                "BoxId": box_id, "address": endereco, "itemCode": item_code, "quantity": str(qtd),
                "uom": "un", "BatchId": "N/A", "description": f"Atendimento pedido {order_id}", "expiryDate": "N/A",
            }])
            insert_items_to_bq_load_job(df_one)
            try:
                log_movement("ENTRADA", item_code, str(qtd), to_address=endereco, box_id=box_id, order_id=order_id, description=f"Atendimento pedido {order_id}", source="WEBAPP_INBOUND")
            except Exception:
                pass
            st.success(f"Entrada registrada para o pedido {order_id}. Pendente restante: {pendente - qtd}")
            st.rerun()


def show_inbound(data):
    compact = st.session_state.get("compact_mode", False)
    if compact:
        st.subheader("📥 Inbound")
    else:
        st.header("📥 Inbound - Bipagem Contínua")
    if "inbound_queue" not in st.session_state:
        st.session_state.inbound_queue = []
    if "bipe_counter" not in st.session_state:
        st.session_state.bipe_counter = 0

    fluxo = st.radio("Fluxo:", ["Bipagem livre", "Atender pedido"], horizontal=True)

    # --- Atender pedido: vincula entrada a um pedido em aberto ---
    if fluxo == "Atender pedido":
        _inbound_atender_pedido(data)
        return

    modo = st.radio("Método:", ["Scanner Laser", "Câmera"], horizontal=True)

    # Modo Zebra: form com campo + Adicionar; Enter ou botão → cai na fila e limpa o campo
    if compact and modo == "Scanner Laser":
        with st.form("f_bipe", clear_on_submit=True):
            qr_raw = st.text_input(
                "Bipe o JSON",
                key=f"bipe_{st.session_state.bipe_counter}",
                label_visibility="collapsed",
                placeholder="Bipe o JSON e pressione Enter (ou toque em Adicionar)",
            )
            col1, _ = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button("➕ Adicionar à fila")
        if submitted and qr_raw and qr_raw.strip():
            try:
                js = json.loads(qr_raw.strip())
                if js not in st.session_state.inbound_queue:
                    st.session_state.inbound_queue.append(js)
                st.session_state.bipe_counter += 1
                st.toast("✅ Item na fila – pode bipar o próximo")
                st.rerun()
            except Exception:
                st.error("JSON inválido")
        qr_raw = None  # não processar de novo abaixo
    else:
        text_height = 80 if compact else 120
        qr_raw = st.camera_input("Scanner") if modo == "Câmera" else st.text_area(
            "Bipe o JSON",
            height=text_height,
            placeholder="Bipe o JSON aqui" if compact else None,
            label_visibility="collapsed" if compact else "visible",
        )
        if modo == "Câmera" and qr_raw:
            qr_raw = ler_qr_da_imagem(qr_raw)
        if qr_raw:
            try:
                js = json.loads(qr_raw)
                if js not in st.session_state.inbound_queue:
                    st.session_state.inbound_queue.append(js)
                    st.toast("✅ Item Adicionado!")
                time.sleep(0.1)
            except Exception:
                st.error("JSON Inválido")

    if st.session_state.inbound_queue:
        df_q = pd.DataFrame(st.session_state.inbound_queue)
        n_itens = len(df_q)
        if compact:
            # Zebra: só colunas resumidas para não arrastar; fonte menor no CSS
            cols_show = ["itemCode", "quantity", "BatchId", "expiryDate"]
            df_display = df_q.copy()
            if "materialBatch" in df_display.columns and "BatchId" not in df_display.columns:
                df_display["BatchId"] = df_display["materialBatch"]
            display_cols = [c for c in cols_show if c in df_display.columns]
            if display_cols:
                df_display = df_display[display_cols]
            with st.expander(f"Fila ({n_itens} itens)", expanded=False):
                st.dataframe(df_display, use_container_width=True)
        else:
            st.dataframe(df_q, use_container_width=True)

        with st.form("f_finalizar"):
            enderecos = data["addr"]["Adress"].unique().tolist() if not data["addr"].empty and "Adress" in data["addr"].columns else ["D1"]
            endereco = st.selectbox("Endereço", enderecos)
            btn_label = "🚀 Enviar" if compact else "🚀 Enviar p/ BigQuery"
            if st.form_submit_button(btn_label, type="primary"):
                rows = []
                for i in st.session_state.inbound_queue:
                    rows.append({
                        "BoxId": f"BOX-{random.randint(1000, 9999)}",
                        "address": endereco,
                        "itemCode": i.get("itemCode"),
                        "quantity": str(i.get("quantity")),
                        "uom": i.get("unitMeasure", "un"),
                        "BatchId": i.get("materialBatch"),
                        "description": i.get("description", "Entrada WebApp"),
                        "expiryDate": i.get("expiryDate", "N/A"),
                    })
                insert_items_to_bq_load_job(pd.DataFrame(rows))
                for r in rows:
                    try:
                        log_movement(
                            "ENTRADA",
                            r["itemCode"],
                            r["quantity"],
                            to_address=endereco,
                            box_id=r["BoxId"],
                            description=r.get("description", "Entrada WebApp"),
                            source="WEBAPP_INBOUND",
                        )
                    except Exception:
                        pass
                st.success("Estoque Atualizado!")
                st.session_state.inbound_queue = []
                st.rerun()
