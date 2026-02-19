# 📦 WMS (versão mínima)

App Streamlit para testar fluxo de estoque: **Entrada**, **Saída** e **Estoque**. Tudo em memória (session state).

## Rodar

```bash
pip install -r requirements.txt
streamlit run run_wms.py
```

## O que tem

- **Entrada**: formulário (código do item, quantidade, endereço) → adiciona ao estoque.
- **Saída**: lista o estoque, escolhe um Box e dá baixa.
- **Estoque**: mostra totais e tabela.

Dados só existem na sessão; ao recarregar a página o estoque zera.
