import random

import pandas as pd
import streamlit as st

from WebApp.utils import (
    STORAGES,
    insert_items_to_bq_load_job,
    load_stock_from_bq,
    log_movement,
    remove_quantity_from_storage,
)


def show_depositos():
    st.header("🏢 Depósitos – Controle manual")
    st.caption("Storage Andar 2 e Andar 3: entrada e saída manual por item, quantidade e local.")

    tab_entrada, tab_saida = st.tabs(["📥 Entrada manual", "📤 Saída manual"])

    with tab_entrada:
        with st.form("dep_entrada"):
            item_code = st.text_input("Item code", placeholder="Ex: SKU-001")
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
            local = st.selectbox("Local (depósito)", STORAGES)
            if st.form_submit_button("Registrar entrada"):
                if not (item_code and str(item_code).strip()):
                    st.error("Informe o item code.")
                else:
                    try:
                        df_one = pd.DataFrame(
                            [
                                {
                                    "BoxId": f"DEP-{random.randint(10000, 99999)}",
                                    "address": local,
                                    "itemCode": str(item_code).strip(),
                                    "quantity": str(quantidade),
                                    "uom": "un",
                                    "BatchId": "N/A",
                                    "description": "Entrada manual depósito",
                                    "expiryDate": "N/A",
                                }
                            ]
                        )
                        insert_items_to_bq_load_job(df_one)
                        try:
                            log_movement(
                                "ENTRADA",
                                str(item_code).strip(),
                                str(quantidade),
                                to_address=local,
                                box_id=df_one.iloc[0]["BoxId"],
                                description="Entrada manual depósito",
                                source="WEBAPP_DEPOSITOS",
                            )
                        except Exception:
                            pass
                        st.success(f"✅ Entrada registrada: {quantidade} un. de {item_code} em {local}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar: {e}")

    with tab_saida:
        with st.form("dep_saida"):
            item_code_s = st.text_input("Item code", placeholder="Ex: SKU-001", key="dep_item_saida")
            quantidade_s = st.number_input("Quantidade", min_value=1, value=1, key="dep_qtd_saida")
            local_s = st.selectbox("Local (depósito)", STORAGES, key="dep_local_saida")
            if st.form_submit_button("Registrar saída"):
                if not (item_code_s and str(item_code_s).strip()):
                    st.error("Informe o item code.")
                else:
                    ok, err = remove_quantity_from_storage(local_s, str(item_code_s).strip(), quantidade_s)
                    if ok:
                        try:
                            log_movement(
                                "SAIDA",
                                str(item_code_s).strip(),
                                quantidade_s,
                                from_address=local_s,
                                description="Saída manual depósito",
                                source="WEBAPP_DEPOSITOS",
                            )
                        except Exception:
                            pass
                        st.success(f"✅ Saída registrada: {quantidade_s} un. de {item_code_s} em {local_s}")
                        st.rerun()
                    else:
                        st.error(err)

    # Resumo por depósito
    st.subheader("Estoque por depósito")
    try:
        df = load_stock_from_bq()
        if df.empty:
            st.info("Nenhum registro em estoque.")
        else:
            df = df[df["address"].isin(STORAGES)]
            if df.empty:
                st.info("Nenhum registro nos depósitos Storage Andar 2/3.")
            else:
                df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
                resumo = df.groupby(["address", "itemCode"], as_index=False)["quantity"].sum()
                for storage in STORAGES:
                    sub = resumo[resumo["address"] == storage]
                    if sub.empty:
                        st.caption(f"**{storage}**: vazio")
                    else:
                        st.caption(f"**{storage}**")
                        st.dataframe(sub, use_container_width=True, hide_index=True)
    except Exception:
        st.warning("Não foi possível carregar o estoque.")
