"""
Admin: aprovar usuários pendentes e gerenciar allowed_modules (apenas role=admin).
"""
import json

import pandas as pd
import streamlit as st
from google.cloud import bigquery

from WebApp.auth.auth import (
    TABLE_USERS,
    MODULE_IDS,
    approve_user,
    can_access_module,
    get_user,
)


def _get_bq():
    from WebApp.core.utils import get_bq_client
    return get_bq_client()


def show_admin_usuarios():
    user_row = st.session_state.get("user_row")
    if not can_access_module(user_row, "admin_usuarios"):
        st.warning("Sem permissão para acessar esta página.")
        return

    st.header("Admin · Usuários")
    st.caption("Aprovar cadastros e gerenciar permissões (allowed_modules).")

    client = _get_bq()

    # --- Pendentes (approved_at IS NULL) ---
    st.subheader("Aguardando aprovação")
    q_pending = f"""
    SELECT email, created_at, verification_sent_at
    FROM `{TABLE_USERS}`
    WHERE approved_at IS NULL
    ORDER BY created_at DESC
    """
    try:
        df_pending = client.query(q_pending).to_dataframe()
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return

    if df_pending.empty:
        st.info("Nenhum usuário aguardando aprovação.")
    else:
        for _, row in df_pending.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{row['email']}** — cadastro em {row['created_at']}")
            with col2:
                if st.button("Aprovar", key=f"approve_{row['email']}"):
                    approve_user(str(row["email"]), st.session_state.get("user_email") or "admin")
                    st.success(f"{row['email']} aprovado.")
                    st.rerun()

    st.divider()
    st.subheader("Todos os usuários")
    q_all = f"""
    SELECT email, role, allowed_modules, approved_at, approved_by, last_login
    FROM `{TABLE_USERS}`
    ORDER BY email
    """
    try:
        df_all = client.query(q_all).to_dataframe()
    except Exception as e:
        st.error(f"Erro: {e}")
        return

    if df_all.empty:
        st.info("Nenhum usuário cadastrado.")
        return

    # Editar allowed_modules (admin apenas)
    for idx, row in df_all.iterrows():
        with st.expander(f"{row['email']} — {row['role']}"):
            st.caption(f"Aprovado em: {row['approved_at']} por {row['approved_by']} | Último login: {row['last_login']}")
            try:
                mods = json.loads(row["allowed_modules"] or "[]")
            except Exception:
                mods = []
            new_mods = st.multiselect(
                "Módulos permitidos",
                MODULE_IDS,
                default=[m for m in MODULE_IDS if m in mods],
                key=f"mods_{row['email']}_{idx}",
            )
            if st.button("Salvar permissões", key=f"save_{row['email']}_{idx}"):
                q_update = "UPDATE `{table}` SET allowed_modules = @mods WHERE LOWER(TRIM(email)) = LOWER(TRIM(@email))".format(table=TABLE_USERS)
                client.query(q_update, job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("mods", "STRING", json.dumps(new_mods)),
                        bigquery.ScalarQueryParameter("email", "STRING", str(row["email"])),
                    ]
                )).result()
                st.success("Salvo.")
                st.rerun()
