# 📦 WMS Tractian

Sistema WMS em Streamlit para a operação: recebimento, separação, depósitos, pedidos em aberto e dashboards. Estoque no **BigQuery** (`tractian-bi.operations`).

## Rodar

```bash
pip install -r requirements.txt
streamlit run WebApp/main.py
```

(Alternativa: `streamlit run run_wms.py` na raiz.)

## Módulos

| Módulo | Descrição |
|--------|------------|
| **Inbound** | Bipagem contínua (scanner/câmera ou JSON), fila → envio para BigQuery; modo Zebra (tela pequena) |
| **Outbound** | Picking por SKU, FEFO → confirmar saída (baixa no BQ) |
| **Depósitos** | Entrada/saída manual para Storage Andar 2 e Andar 3 |
| **Pedidos em aberto** | Leitura e filtro por `transfer_type`, dashboard, export CSV |
| **Dashboard** | Métricas de estoque e gráfico por endereço/item |

## Configuração

- **BigQuery**: `service-account.json` na raiz ou em `WebApp/`, ou variável `GOOGLE_APPLICATION_CREDENTIALS`. Em deploy (Streamlit Cloud), use o secret `GCP_CREDENTIALS_JSON`.
- Ver **DEPLOY.md** para link compartilhável.
- Ver **ROADMAP_WMS.md** para visão do WMS e próximos passos.
