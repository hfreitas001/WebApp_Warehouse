# Tabelas BigQuery para o WMS

Resumo das tabelas em uso e **novas tabelas** sugeridas (movimentações, etc.).

---

## Tabelas já em uso (existentes)

| Dataset        | Tabela                                | Uso no app |
|----------------|----------------------------------------|------------|
| `operations`   | `operations_webapp_warehouse_instock`  | Estoque atual: INSERT (Inbound, Depósitos), DELETE/UPDATE (Outbound, saída depósito). |
| `operations_dbt` | `fct_open_transfer_request_lines`   | Só leitura – Pedidos em aberto, filtro por `transfer_type`. |

Essas já estão criadas e em uso no projeto.

---

## Novas tabelas sugeridas

### 1. Movimentações (obrigatória para rastreabilidade)

Registra **cada movimentação** (entrada, saída, transferência, ajuste) com data/hora e contexto. O app passa a gravar uma linha aqui sempre que alterar o estoque.

**Nome:** `tractian-bi.operations.operations_webapp_warehouse_movements`

**Criar pelo projeto (recomendado):**

Na raiz do repositório, com o `service-account.json` configurado:

```bash
python scripts/create_bq_tables.py
```

Isso cria a tabela de movimentações. Para criar também a tabela de contagem (inventário):

```bash
python scripts/create_bq_tables.py --inventory
```

O script usa o mesmo `service-account.json` do app (raiz ou `WebApp/`).

**DDL (referência):**

```sql
CREATE TABLE IF NOT EXISTS `tractian-bi.operations.operations_webapp_warehouse_movements` (
  movement_id     STRING   NOT NULL,
  movement_type   STRING   NOT NULL,
  movement_at     TIMESTAMP NOT NULL,
  item_code       STRING,
  quantity        STRING,
  quantity_before STRING,
  quantity_after  STRING,
  from_address    STRING,
  to_address      STRING,
  box_id          STRING,
  order_id        STRING,
  description     STRING,
  source          STRING,
  user_email      STRING
);
```

A coluna `user_email` registra o e-mail do usuário logado (Google OIDC) quando disponível. Para tabelas já criadas, rode: `python scripts/create_bq_tables.py --migrate`.

**Sugestão de valores para `movement_type` e `source`:**

| movement_type  | Uso |
|----------------|-----|
| `ENTRADA`      | Inbound, entrada manual depósito |
| `SAIDA`        | Outbound, saída manual depósito |
| `TRANSFERENCIA`| Movimento entre endereços/depósitos (futuro) |
| `AJUSTE`       | Inventário/contagem (futuro) |

| source | Uso |
|--------|-----|
| `WEBAPP_INBOUND`   | Módulo Inbound |
| `WEBAPP_OUTBOUND`  | Módulo Outbound |
| `WEBAPP_DEPOSITOS` | Módulo Depósitos (entrada/saída manual) |
| `WEBAPP_AJUSTE`    | Ajuste/inventário (futuro) |

Com essa tabela você consegue:
- Relatórios de movimentação por período, item, tipo.
- Auditoria (quando adicionar usuário/sessão, se quiser).
- KPIs (entradas/saídas por dia, itens mais movimentados).

---

### 2. Contagem / inventário (opcional – para depois)

Para contagem cíclica ou inventário: registro do que foi contado e, se quiser, do ajuste aplicado.

**Nome:** `tractian-bi.operations.operations_webapp_warehouse_inventory_count`

**DDL (sugestão):**

```sql
CREATE TABLE IF NOT EXISTS `tractian-bi.operations.operations_webapp_warehouse_inventory_count` (
  count_id        STRING   NOT NULL,
  count_at        TIMESTAMP NOT NULL,
  address         STRING,
  item_code       STRING,
  quantity_system STRING,   -- Qtd no sistema antes da contagem
  quantity_counted STRING, -- Qtd contada
  quantity_diff   STRING,  -- Diferença (contado - sistema)
  adjusted        BOOL,    -- Se já foi aplicado ajuste no instock
  description     STRING
);
```

Só criar quando for implementar a tela de inventário/contagem.

---

### 3. Resumo – o que criar agora

| Tabela (nova) | Para quê | Quando criar |
|---------------|----------|--------------|
| `operations_webapp_warehouse_movements` | Registrar toda entrada, saída, transferência e ajuste | **Agora** – base para relatórios e auditoria |
| `operations_webapp_warehouse_inventory_count` | Contagem e ajuste de inventário | Quando fizer a tela de inventário |

**Ordem sugerida:** criar só a tabela de **movimentações** e, no app, passar a inserir uma linha nela em cada ação que altera o estoque (Inbound, Outbound, Depósitos). A tabela de contagem pode ser criada quando formos implementar inventário no WMS.

Se quiser, no próximo passo desenhamos juntos onde chamar o “insert em movements” em cada módulo (Inbound, Outbound, Depósitos) e o formato exato dos campos.
