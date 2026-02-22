# API WMS Tractian - Google Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema (se precisar de libs extras no futuro)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cópia do projeto (api + WebApp, a API importa do WebApp)
COPY api/ ./api/
COPY WebApp/ ./WebApp/

# Instala dependências da API
RUN pip install --no-cache-dir -r api/requirements.txt

# Cloud Run injeta PORT (ex.: 8080)
ENV PORT=8080
EXPOSE 8080

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
