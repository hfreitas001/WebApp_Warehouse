import json
import random
import time

import pandas as pd
import streamlit as st

from WebApp.utils import ler_qr_da_imagem, insert_items_to_bq_load_job


def show_inbound(data):
    compact = st.session_state.get("compact_mode", False)
    if compact:
        st.subheader("📥 Inbound")
    else:
        st.header("📥 Inbound - Bipagem Contínua")
    if "inbound_queue" not in st.session_state:
        st.session_state.inbound_queue = []

    modo = st.radio("Método:", ["Scanner Laser", "Câmera"], horizontal=True)
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
            with st.expander(f"Fila ({n_itens} itens)", expanded=False):
                st.dataframe(df_q, use_container_width=True)
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
                st.success("Estoque Atualizado!")
                st.session_state.inbound_queue = []
                st.rerun()
