# Deploy do WMS Tractian (frontend + API) para outras pessoas usarem

O app tem duas partes que precisam estar no ar:

1. **API** (FastAPI) — backend que o frontend chama  
2. **Frontend** (React/Vite) — interface que as pessoas abrem no navegador  

Segue uma forma simples usando **Render** (API) e **Vercel** (frontend), com plano gratuito.

---

## 1. Deixar o código no GitHub

Garanta que o repositório está no GitHub e atualizado:

```bash
git add .
git commit -m "Preparar deploy"
git push origin main
```

---

## 2. Deploy da API (Render)

1. Acesse [render.com](https://render.com) e crie conta (ou use GitHub login).
2. **New** → **Web Service**.
3. Conecte o repositório do projeto e escolha o mesmo repo.
4. Configure:
   - **Name:** `wms-tractian-api` (ou outro)
   - **Root Directory:** `api`
   - **Runtime:** `Python 3`
   - **Build Command:**  
     `pip install -r requirements.txt`
   - **Start Command:**  
     `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

5. Em **Environment** (variáveis de ambiente), adicione pelo menos:
   - `CORS_ORIGINS` = `https://seu-frontend.vercel.app`  
     (substitua pela URL do frontend que você vai criar no passo 3; pode adicionar depois e fazer redeploy)
   - As que a API já usa (ex.: `JWT_SECRET`, banco, etc. — veja `api/` e `.env` se tiver).

6. Clique em **Create Web Service**.  
   Render vai dar uma URL tipo: `https://wms-tractian-api.onrender.com`.  
   **Guarde essa URL** — é a URL da API.

7. Depois que o frontend estiver no ar, volte aqui, coloque em `CORS_ORIGINS` a URL exata do front (ex. `https://wms-tractian.vercel.app`) e faça **Manual Deploy** de novo.

---

## 3. Deploy do Frontend (Vercel)

1. Acesse [vercel.com](https://vercel.com) e crie conta (ou use GitHub login).
2. **Add New** → **Project** e importe o mesmo repositório.
3. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build` (já vem assim)
   - **Output Directory:** `dist` (já vem assim)

4. Em **Environment Variables**:
   - **Name:** `VITE_API_URL`  
   - **Value:** a URL da API do Render (ex.: `https://wms-tractian-api.onrender.com`)  
   - **Environment:** Production (e Preview se quiser)

5. Clique em **Deploy**.  
   A Vercel vai dar uma URL tipo: `https://wms-tractian.vercel.app`.

6. **Importante:** Volte no Render, em **Environment**, e defina:
   - `CORS_ORIGINS` = `https://wms-tractian.vercel.app`  
   (use exatamente a URL que a Vercel mostrou).  
   Depois faça **Manual Deploy** da API.

---

## 4. Testar

- Abra a URL do frontend (Vercel).  
- Faça login; o frontend vai chamar a API no Render.  
- Se der erro de CORS, confira se `CORS_ORIGINS` tem exatamente a URL do front (com `https://`, sem barra no final).

---

## 5. Resumo das variáveis

| Onde   | Variável       | Exemplo / Uso |
|--------|----------------|----------------|
| Render (API) | `CORS_ORIGINS` | `https://seu-app.vercel.app` |
| Render (API) | Outras (JWT, DB, etc.) | Conforme sua `api/` |
| Vercel (Front) | `VITE_API_URL` | `https://sua-api.onrender.com` |

---

## Alternativas

- **Só Render:** dá para hospedar frontend e API no Render (dois serviços: um Static Site para o `frontend` e um Web Service para a `api`). Aí você não usa Vercel.
- **Railway / Fly.io:** em vez do Render, você sobe a API em um deles e usa a URL da API no `VITE_API_URL` da mesma forma.
- **Streamlit (WebApp):** se quiser que outras pessoas usem a parte Streamlit, use [Streamlit Community Cloud](https://streamlit.io/cloud) apontando para a pasta do WebApp (é um deploy separado do front React).

Com isso, qualquer pessoa com o link do frontend (Vercel) consegue usar o app.
