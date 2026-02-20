import json
import random
import pandas as pd
import streamlit as st
from .utils import add_to_stock, load_data


def show(data=None):
    if data is None:
        data = load_data()
    st.header("📥 Inbound - Entrada")
    if "inbound_queue" not in st.session_state:
        st.session_state.inbound_queue = []

    modo = st.radio("Modo", ["Formulário", "JSON"], horizontal=True, key="in_modo")

    if modo == "Formulário":
        with st.form("in_form"):
            item = st.text_input("Código do item", placeholder="SKU-001", key="in_item")
            qtd = st.number_input("Quantidade", min_value=1, value=1, key="in_qtd")
            enderecos = ["A1", "A2", "B1", "B2", "C1", "D1"]
            endereco = st.selectbox("Endereço", enderecos, key="in_endereco")
            desc = st.text_input("Descrição (opcional)", placeholder="Entrada WebApp", key="in_desc")
            lote = st.text_input("Lote (opcional)", placeholder="20250101", key="in_lote")
            if st.form_submit_button("Adicionar à fila"):
                if item and item.strip():
                    st.session_state.inbound_queue.append({
                        "itemCode": item.strip(), "quantity": qtd, "unitMeasure": "un",
                        "materialBatch": lote.strip() or "N/A", "description": desc.strip() or "Entrada WebApp", "expiryDate": "N/A",
                    })
                    st.success("Item adicionado à fila.")
                    st.rerun()
                else:
                    st.warning("Informe o código do item.")
    else:
        raw = st.text_area("Cole o JSON (objeto ou array)", height=120, key="in_json")
        if st.button("Adicionar à fila", key="in_btn_json"):
            if raw and raw.strip():
                try:
                    js = json.loads(raw)
                    for obj in (js if isinstance(js, list) else [js]):
                        if isinstance(obj, dict) and obj not in st.session_state.inbound_queue:
                            st.session_state.inbound_queue.append(obj)
                    st.success("Itens adicionados à fila.")
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("JSON inválido.")
            else:
                st.warning("Cole um JSON.")

    if st.session_state.inbound_queue:
        st.subheader("Fila de entrada")
        st.dataframe(pd.DataFrame(st.session_state.inbound_queue), use_container_width=True, hide_index=True)
        with st.form("in_finalizar"):
            endereco = st.selectbox("Endereço", ["A1", "A2", "B1", "B2", "C1", "D1"], key="in_endereco_final")
            if st.form_submit_button("🚀 Enviar tudo para o estoque", type="primary"):
                for i in st.session_state.inbound_queue:
                    add_to_stock({
                        "BoxId": f"BOX-{random.randint(1000, 9999)}",
                        "address": endereco,
                        "itemCode": i.get("itemCode", ""),
                        "quantity": str(i.get("quantity", 1)),
                        "uom": i.get("unitMeasure", "un"),
                        "BatchId": i.get("materialBatch", "N/A"),
                        "description": i.get("description", "Entrada WebApp"),
                        "expiryDate": i.get("expiryDate", "N/A"),
                    })
                st.session_state.inbound_queue = []
                st.success("Estoque atualizado.")
                st.rerun()
