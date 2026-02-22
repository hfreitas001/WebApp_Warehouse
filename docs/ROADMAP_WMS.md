# 📦 WMS Tractian – Visão e roadmap

Documento de visão do **sistema WMS** da sua operação e evolução do que já está no app.

---

## ✅ O que já está pronto

| Módulo | Função | Estado |
|--------|--------|--------|
| **Inbound** | Recebimento por bipagem (scanner/câmera ou JSON), fila, envio para BigQuery | ✅ |
| **Inbound Zebra** | Modo tela pequena, form com limpar campo, múltiplas bipagens contínuas | ✅ |
| **Outbound** | Picking por SKU, FEFO (lote), confirmar saída (baixa no BQ) | ✅ |
| **Depósitos** | Entrada/saída manual (Storage Andar 2 e Andar 3): item, quantidade, local | ✅ |
| **Pedidos em aberto** | Leitura da `fct_open_transfer_request_lines`, filtro por `transfer_type`, dashboard, export CSV | ✅ |
| **Dashboard** | Métricas de estoque (volumes, qtd total), gráfico por endereço/item | ✅ |
| **BigQuery** | Estoque em `operations_webapp_warehouse_instock`; credenciais por arquivo ou Streamlit Secrets | ✅ |
| **Deploy** | Streamlit Cloud, link compartilhável, modo Zebra na leitora | ✅ |

---

## 🎯 Próximos passos para um WMS “completo” (sugestão)

Priorize conforme sua operação. Dá para ir fazendo por etapas.

### 1. **Inventário / contagem**
- Tela de **contagem cíclica** ou inventário por endereço/item.
- Registrar contagem e (opcional) ajuste automático no BQ (diferença entre sistema x contado).

### 2. **Transferências entre depósitos**
- Usar os **Pedidos em aberto** como origem: criar uma ação “Atender pedido” que gera movimento (saída do `from_whs`, entrada no `to_whs`) e registra no BQ.
- Ou tela de **transferência manual**: origem (Storage 2/3 ou endereço), destino, item, quantidade.

### 3. **Endereçamento e put-away**
- Cadastro de **endereços** (além dos dois storages): corredor, prateleira, nível.
- Regra simples de **put-away** (ex.: “próximo endereço livre” ou por tipo de item) no Inbound.

### 4. **Rastreabilidade**
- Histórico de movimentos (quem, quando, tipo: entrada/saída/transferência/ajuste).
- Pode ser uma tabela no BQ (`operations_webapp_warehouse_movements`) alimentada em cada ação.

### 5. **Relatórios e KPIs**
- Dashboard com: itens mais movimentados, tempo médio em estoque, atrasos (usando `days_until_deadline` / `is_overdue` dos pedidos em aberto).
- Gráficos por período (entradas/saídas por dia ou semana).

### 6. **Integração com pedidos**
- Se a operação “fechar” pedidos quando atender: marcar como processado na origem (quando houver API ou tabela que permita escrita) ou manter apenas o uso atual (leitura + export).

### 7. **Controle de acesso (opcional)**
- Login simples (Streamlit ou OAuth) para saber quem fez cada movimento, se precisar de auditoria.

---

## Como usar este roadmap

- Escolha **1 ou 2 itens** por vez (ex.: inventário + transferências).
- Diga qual prioridade você quer (ex.: “primeiro inventário” ou “primeiro atender pedido de transferência”) e a gente desenha a tela e o fluxo no app atual, sem quebrar o que já existe.

Quando quiser, é só dizer por onde começar (ex.: “vamos fazer o inventário” ou “vamos fazer a transferência entre depósitos”) que eu proponho o desenho das telas e das tabelas no BigQuery.
