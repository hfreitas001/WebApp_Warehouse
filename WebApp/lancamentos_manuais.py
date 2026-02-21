"""
Lançamentos manuais: registro de movimentação apenas em log (sem alterar estoque).
Uso: correções, ajustes de histórico, documentação.
"""
import streamlit as st

from WebApp.utils import log_movement, STORAGES


def show_lancamentos_manuais():
    st.header("📝 Lançamentos manuais")
    st.caption("Registra uma linha no histórico de movimentações (sem alterar estoque). Use para correções ou documentação.")

    with st.form("f_lancamento_manual"):
        col1, col2 = st.columns(2)
        with col1:
            movement_type = st.selectbox("Tipo", ["ENTRADA", "SAIDA"], key="lm_tipo")
            item_code = st.text_input("Item (SKU)", placeholder="Ex: SKU-001")
            quantity = st.number_input("Quantidade", min_value=1, value=1)
        with col2:
            from_address = st.selectbox("Endereço origem", [""] + list(STORAGES), key="lm_from")
            to_address = st.selectbox("Endereço destino", [""] + list(STORAGES), key="lm_to")
            order_id = st.text_input("Order ID (opcional)", placeholder="Ex: ORD-123")
        description = st.text_input("Descrição", placeholder="Ex: Ajuste manual / Correção")
        if st.form_submit_button("Registrar lançamento"):
            if not (item_code and str(item_code).strip()):
                st.error("Informe o item (SKU).")
            else:
                try:
                    log_movement(
                        movement_type,
                        str(item_code).strip(),
                        str(quantity),
                        from_address=from_address or None,
                        to_address=to_address or None,
                        order_id=order_id.strip() or None,
                        description=description.strip() or f"Lançamento manual {movement_type}",
                        source="WEBAPP_LANCAMENTO_MANUAL",
                    )
                    st.success("Lançamento registrado no histórico de movimentações.")
                except Exception as e:
                    st.error(f"Erro ao registrar: {e}")
