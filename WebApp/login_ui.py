"""
Tela de Login e Sign Up (cadastro). Usado quando não há sessão válida no cookie.
Se a tabela de usuários estiver vazia, exibe formulário para criar o primeiro admin.
"""
import datetime

import pandas as pd
import streamlit as st
from google.cloud import bigquery

from WebApp.auth import (
    TABLE_USERS,
    get_user,
    hash_password,
    login as auth_login,
    signup as auth_signup,
)


def _users_table_empty():
    try:
        from WebApp.utils import get_bq_client
        client = get_bq_client()
        df = client.query("SELECT 1 FROM `{table}` LIMIT 1".format(table=TABLE_USERS)).to_dataframe()
        return df.empty
    except Exception:
        return True


def show_login_or_signup():
    """Exibe abas Login e Sign Up; ao logar com sucesso, preenche session_state e faz rerun."""
    # Primeiro acesso: tabela vazia -> criar administrador inicial
    if _users_table_empty():
        st.title("WMS Tractian — Primeiro acesso")
        st.markdown("Crie o usuário administrador inicial.")
        with st.form("bootstrap_admin"):
            email = st.text_input("E-mail do administrador", placeholder="admin@empresa.com")
            password = st.text_input("Senha (mín. 6 caracteres)", type="password")
            if st.form_submit_button("Criar administrador"):
                if email and str(email).strip() and password and len(password) >= 6:
                    now = datetime.datetime.utcnow()
                    df = pd.DataFrame([{
                        "email": str(email).strip().lower(),
                        "password_hash": hash_password(password),
                        "role": "admin",
                        "allowed_modules": "[]",
                        "last_login": None,
                        "verification_code": None,
                        "verification_sent_at": None,
                        "approved_at": now,
                        "approved_by": "system",
                        "created_at": now,
                    }])
                    from WebApp.utils import get_bq_client
                    client = get_bq_client()
                    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
                    client.load_table_from_dataframe(df, TABLE_USERS, job_config=job_config).result()
                    st.success("Administrador criado. Faça login na aba Entrar.")
                    st.rerun()
                else:
                    st.warning("Preencha e-mail e senha (mín. 6 caracteres).")
        return

    st.title("WMS Tractian")
    tab_login, tab_signup = st.tabs(["Entrar", "Cadastrar"])

    with tab_login:
        with st.form("form_login"):
            email = st.text_input("E-mail", placeholder="seu.email@empresa.com", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            if st.form_submit_button("Entrar"):
                if not email or not str(email).strip():
                    st.warning("Digite o e-mail.")
                elif not password:
                    st.warning("Digite a senha.")
                else:
                    ok, msg = auth_login(str(email).strip(), password)
                    if ok:
                        st.session_state.user_email = str(email).strip().lower()
                        user = get_user(st.session_state.user_email)
                        if user is not None:
                            st.session_state.user_role = str(user.get("role") or "user")
                            st.session_state.user_row = user
                        st.rerun()
                    else:
                        st.error(msg)

    with tab_signup:
        with st.form("form_signup"):
            email_s = st.text_input("E-mail", placeholder="seu.email@empresa.com", key="signup_email")
            password_s = st.text_input("Senha (mín. 6 caracteres)", type="password", key="signup_password")
            if st.form_submit_button("Cadastrar"):
                if not email_s or not str(email_s).strip():
                    st.warning("Digite o e-mail.")
                elif not password_s or len(password_s) < 6:
                    st.warning("Senha deve ter no mínimo 6 caracteres.")
                else:
                    ok, out = auth_signup(str(email_s).strip(), password_s)
                    if ok:
                        st.success("Cadastro realizado. Aguarde a aprovação do administrador.")
                        st.info(f"Código de verificação (simulado): **{out}** — use apenas para conferência.")
                    else:
                        st.error(out)

    return False
