# Frontend WMS Tractian (React + Vite)

Interface em React que consome a API do WMS. Nao altera arquivos do WebApp/Streamlit.

## Rodar

1. Subir a API (na raiz do projeto):
   ```bash
   pip install -r api/requirements.txt
   uvicorn api.main:app --reload --port 8000
   ```
2. Subir o frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Abre em http://localhost:5173.

A API importa apenas do WebApp (auth, core.utils) para ler dados e registrar movimentacoes; nenhum arquivo do Streamlit e modificado.

## Estrutura

- `src/api.js` — cliente HTTP (auth, data, movements, orders, admin)
- `src/AuthContext.jsx` — login, usuario, permissoes (can)
- `src/Layout.jsx` — sidebar por modulo, rotas aninhadas
- `src/pages/` — Login, Dashboard, Inbound, Outbound, Ajustments, LancamentosManuais, Movimentacoes, PedidosAbertos, AdminUsuarios

## Variavel de ambiente

- `VITE_API_URL` — URL da API (padrao: http://localhost:8000)
