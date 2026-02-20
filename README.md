# 📦 WMS Tractian

App Streamlit: **Inbound**, **Outbound** e **Dashboard**. Estoque em memória (session state).

## Rodar

```bash
pip install -r requirements.txt
streamlit run run_wms.py
```

## Módulos

- **Inbound** – Formulário ou JSON → fila → Enviar para estoque
- **Outbound** – Escolher SKU → Gerar plano (FEFO) → Confirmar saída
- **Dashboard** – Métricas e gráfico por endereço/item

Dados só na sessão; ao recarregar a página o estoque zera.
