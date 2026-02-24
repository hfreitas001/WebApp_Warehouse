# Deploy gratuito na Vercel

Na Vercel você sobe o **frontend** (React) de graça. A **API** não roda na Vercel; ela precisa estar em outro lugar (ex.: Render, também grátis).

**Ordem:** primeiro sobe a API no Render e pega a URL → depois coloca essa URL na Vercel no `VITE_API_URL`.

---

## Checklist produção (Vercel + Render)

| Onde | Variável | Valor (exemplo) |
|------|----------|------------------|
| **Vercel** | `VITE_API_URL` | `https://webapp-warehouse.onrender.com` (sem barra no final) |
| **Render** | `CORS_ORIGINS` | `https://web-app-warehouse.vercel.app` (URL do seu front na Vercel) |
| **Render** | `JWT_SECRET` | Uma string longa e secreta |

- **Render:** Health Check Path = `/health`. Após deploy, abra `https://seu-api.onrender.com/health` para “acordar” o serviço antes de testar o login.
- **Vercel:** Root Directory = `frontend`. Após alterar variáveis, faça **Redeploy**.
- Se o front foi deployado sem `VITE_API_URL`, o código usa fallback para a API no Render; mesmo assim é melhor definir a variável e redeployar.

---

## 1. Subir a API no Render (faça isso primeiro)

1. Acesse **[render.com](https://render.com)** e entre com **GitHub**.
2. **New** → **Web Service**.
3. Conecte o repositório **WebApp_Warehouse** (ou o nome do seu repo).
4. Preencha:
   - **Name:** `wms-api` (ou outro nome; a URL será tipo `https://wms-api.onrender.com`).
   - **Region:** escolha o mais próximo (ex.: Oregon).
   - **Root Directory:** deixe **em branco** (raiz do repo).
   - **Runtime:** **Python 3**.
   - **Build Command:** `pip install -r api/requirements.txt`
   - **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** **Free**.
5. Em **Environment** (Environment Variables), clique em **Add Environment Variable** e adicione:
   - **Key:** `JWT_SECRET` → **Value:** qualquer string longa (ex.: `meu-segredo-super-secreto-123`).
   - **Key:** `CORS_ORIGINS` → **Value:** por enquanto pode deixar `https://vercel.app` ou a URL que a Vercel já te deu para o frontend; depois você ajusta para a URL exata do seu projeto.
6. Clique em **Create Web Service**.
7. Espere o deploy terminar. No topo da página do serviço aparece a **URL**, tipo:  
   **`https://wms-api.onrender.com`**  
   **Copie essa URL** — é ela que você vai colocar na Vercel no `VITE_API_URL`.

---

## 2. Deixar o código no GitHub


```bash
git add .
git commit -m "Deploy Vercel"
git push origin main
```

---

## 3. Deploy do frontend na Vercel (grátis)

1. Acesse **[vercel.com](https://vercel.com)** e entre com **GitHub**.
2. **Add New** → **Project**.
3. Importe o repositório **WebApp_Warehouse** (ou o nome do seu repo).
4. **Importante:** use a **sua conta pessoal** no GitHub, não a organização, para não precisar de plano pago.
5. Configure:
   - **Root Directory:** clique em **Edit** e escolha **`frontend`**.
   - **Framework Preset:** Vite (a Vercel detecta).
   - **Build Command:** `npm run build`.
   - **Output Directory:** `dist`.
6. Em **Environment Variables**, adicione:
   - **Name:** `VITE_API_URL`
   - **Value:** a **URL da API** que você copiou do Render (ex.: `https://wms-api.onrender.com`).
   - **Environment:** Production (e Preview se quiser).
7. Clique em **Deploy**.

Quando terminar, a Vercel mostra uma URL tipo: `https://webapp-warehouse.vercel.app`. Esse é o link que você compartilha.

---

## 4. Onde fica a API (referência)

O frontend chama a API. Se a API não estiver no ar, o app abre mas dá erro ao fazer login ou carregar dados.

**Opção gratuita para a API:** **[Render](https://render.com)** — passo a passo no item 1 acima.

Depois que a API estiver no Render, na **Vercel** → seu projeto → **Settings** → **Environment Variables** coloque em **VITE_API_URL** a URL da API. Faça um **Redeploy** (Deployments → ⋮ no último deploy → Redeploy).

No **Render**, confira se `CORS_ORIGINS` está exatamente com a URL do front (com `https://`, sem barra no final) e faça **Manual Deploy** se tiver alterado.

---

## 5. Resumo

| Onde   | O quê        | Custo   |
|--------|--------------|---------|
| Vercel | Frontend     | Grátis  |
| Render | API          | Grátis* |

\* No plano free do Render a API “dorme” após ~15 min sem uso; o primeiro acesso pode demorar ~30 s.

**Link para compartilhar:** a URL do frontend na Vercel.
