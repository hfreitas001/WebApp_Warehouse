# 🌐 Deploy – Link compartilhável (Streamlit Community Cloud)

Siga os passos para publicar o WMS e acessar por um **link público** (ex: `https://seu-app.streamlit.app`).

---

## 1. Subir o código no GitHub

- Crie um repositório no GitHub (ex: `WebApp_Warehouse`).
- **Não** faça commit do arquivo `service-account.json` (ele já está no `.gitignore`).
- Envie o código:

```bash
cd /caminho/para/WebApp_Warehouse
git init
git add .
git commit -m "WMS Tractian 2026"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/WebApp_Warehouse.git
git push -u origin main
```

---

## 2. Deploy no Streamlit Community Cloud

1. Acesse **[share.streamlit.io](https://share.streamlit.io)** e entre com sua conta GitHub.
2. Clique em **"New app"**.
3. Preencha:
   - **Repository**: `SEU_USUARIO/WebApp_Warehouse`
   - **Branch**: `main`
   - **Main file path**: `WebApp/main.py`
4. Clique em **"Advanced settings"** e, em **Secrets**, adicione uma chave:
   - Nome: `GCP_CREDENTIALS_JSON`
   - Valor: o **conteúdo completo** do seu `service-account.json` (copie e cole o JSON inteiro que você baixou do Google Cloud, em uma linha ou mantendo a formatação).
5. Clique em **"Deploy"**.

---

## 3. Seu link

Após o deploy, o Streamlit mostra um link do tipo:

**`https://SEU-USUARIO-WebApp-Warehouse-XXXXX.streamlit.app`**

Use esse link em qualquer lugar (celular, outro computador, etc.). O app roda na nuvem e continua usando o BigQuery do projeto `tractian-bi`.

---

## Resumo

| Onde        | Uso |
|------------|-----|
| **Local**  | `service-account.json` na pasta do projeto (como hoje). |
| **Streamlit Cloud** | Secret `GCP_CREDENTIALS_JSON` com o JSON inteiro (sem commitar o arquivo). |

O código já está preparado: em deploy ele usa o secret; localmente usa o arquivo ou `GOOGLE_APPLICATION_CREDENTIALS`.
