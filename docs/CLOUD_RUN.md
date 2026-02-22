# Deploy da API no Google Cloud Run

A API (FastAPI) pode rodar no **Cloud Run**. O frontend continua onde estiver (Vercel, Netlify, etc.) e aponta `VITE_API_URL` para a URL do Cloud Run.

---

## Pré-requisitos

- Conta no [Google Cloud](https://console.cloud.google.com)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) instalado e logado (`gcloud auth login`)

---

## 1. Criar projeto e ativar APIs

```bash
# Criar projeto (ou use um existente)
gcloud projects create SEU_PROJECT_ID --name="WMS Tractian"

# Ativar Cloud Run e Container Registry
gcloud services enable run.googleapis.com containerregistry.googleapis.com --project=SEU_PROJECT_ID
```

---

## 2. Build e deploy (uma vez)

Na **raiz do repositório** (onde está o `Dockerfile`):

```bash
# Definir projeto
gcloud config set project SEU_PROJECT_ID

# Build da imagem no Google (Artifact Registry / Container Registry)
# e deploy no Cloud Run em um comando:
gcloud run deploy wms-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "CORS_ORIGINS=https://seu-front.vercel.app" \
  --set-env-vars "JWT_SECRET=seu-segredo-forte-aqui"
```

- `--source .` faz o build do Dockerfile na raiz e já faz o deploy.
- Troque `us-central1` pela região que preferir (ex.: `southamerica-east1` para São Paulo).
- Troque `CORS_ORIGINS` pela URL exata do seu frontend.
- Adicione outras variáveis que a API usar (BigQuery, etc.): `--set-env-vars "NOME=valor"` ou use um arquivo depois.

No fim do comando o Cloud Run mostra a **URL do serviço**, tipo:

`https://wms-api-xxxxx-uc.a.run.app`

---

## 3. Configurar o frontend

No frontend (Vercel, Netlify, etc.), defina:

- **Variável de ambiente:** `VITE_API_URL` = `https://wms-api-xxxxx-uc.a.run.app` (a URL que o Cloud Run mostrou).

Se o front já estiver no ar, faça um novo deploy após alterar a variável.

---

## 4. Variáveis de ambiente no console (opcional)

Para não colocar tudo no comando:

1. [Cloud Run](https://console.cloud.google.com/run) → clique no serviço **wms-api**.
2. **Edit & Deploy New Revision** → aba **Variables & Secrets**.
3. Adicione `CORS_ORIGINS`, `JWT_SECRET` e qualquer outra que a API precise (ex.: credenciais BigQuery).
4. **Deploy**.

---

## 5. Custos

Cloud Run tem [free tier](https://cloud.google.com/run/pricing#free-tier): 2 milhões de requisições/mês e um limite de tempo de CPU/memória. Para uso moderado costuma ficar dentro do gratuito.

---

## Resumo

| Onde        | O quê |
|------------|--------|
| Cloud Run  | API (este repo, Dockerfile na raiz) |
| Frontend   | `VITE_API_URL` = URL do Cloud Run |
| API        | `CORS_ORIGINS` = URL do frontend |

Depois de configurado, o link que você compartilha é o do **frontend**; ele já chama a API no Cloud Run sozinho.
