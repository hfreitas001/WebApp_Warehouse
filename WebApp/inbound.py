import json
import random
import time

import pandas as pd
import streamlit as st

from WebApp.utils import ler_qr_da_imagem, insert_items_to_bq_load_job, log_movement


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
