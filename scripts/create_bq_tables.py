#!/usr/bin/env python3
"""
Cria as tabelas do WMS no BigQuery (movimentações e inventário/contagem).
Usa o mesmo service-account.json do app. Rode na raiz do projeto:

  python scripts/create_bq_tables.py
"""
import os
import sys

# Credenciais: mesmo path do app
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_JSON = os.path.join(ROOT, "service-account.json")
if not os.path.exists(PATH_JSON):
    PATH_JSON = os.path.join(ROOT, "WebApp", "service-account.json")

PROJECT_ID = "tractian-bi"
DATASET_ID = "operations"


def get_client():
    from google.cloud import bigquery
    from google.oauth2 import service_account
    if not os.path.exists(PATH_JSON) or os.path.getsize(PATH_JSON) < 50:
        raise FileNotFoundError(f"Coloque o service-account.json em {ROOT} ou em WebApp/")
    creds = service_account.Credentials.from_service_account_file(PATH_JSON)
    return bigquery.Client(credentials=creds, project=PROJECT_ID)


TABLE_MOVEMENTS = "`tractian-bi.operations.operations_webapp_warehouse_movements`"
TABLE_INSTOCK = "`tractian-bi.operations.operations_webapp_warehouse_instock`"

# --- users_wms: autenticação e aprovação (tudo pelo app, nada direto no BQ) ---
DDL_USERS_WMS = """
CREATE TABLE IF NOT EXISTS `tractian-bi.operations.operations_webapp_warehouse_users_wms` (
  email              STRING   NOT NULL,
  password_hash      STRING   NOT NULL,
  role               STRING   NOT NULL,
  allowed_modules    STRING,
  last_login         TIMESTAMP,
  verification_code  STRING,
  verification_sent_at TIMESTAMP,
  approved_at        TIMESTAMP,
  approved_by        STRING,
  created_at         TIMESTAMP
)
"""

# --- enderecamentos: depósito (dropdown) + address_code (opções por depósito) ---
DDL_ENDERECAMENTOS = """
CREATE TABLE IF NOT EXISTS `tractian-bi.operations.operations_webapp_warehouse_enderecamentos` (
  warehouse_name   STRING   NOT NULL,
  address_code     STRING   NOT NULL,
  created_at      TIMESTAMP
)
"""

# --- mapeamento endereço × SKU (configuração no app) ---
DDL_ADDRESS_SKU = """
CREATE TABLE IF NOT EXISTS `tractian-bi.operations.operations_webapp_warehouse_address_sku` (
  address_code   STRING   NOT NULL,
  item_code      STRING   NOT NULL,
  created_at     TIMESTAMP
)
"""

# --- reserva de pedido (qual user está atendendo; aviso se outro user já reservou) ---
DDL_ORDER_RESERVATIONS = """
CREATE TABLE IF NOT EXISTS `tractian-bi.operations.operations_webapp_warehouse_order_reservations` (
  order_id      STRING   NOT NULL,
  user_email    STRING   NOT NULL,
  reserved_at   TIMESTAMP NOT NULL
)
"""

# --- parâmetros do sistema (tempo de reserva, etc.) ---
DDL_PARAMS = """
CREATE TABLE IF NOT EXISTS `tractian-bi.operations.operations_webapp_warehouse_params` (
  param_key    STRING   NOT NULL,
  param_value  STRING,
  updated_at   TIMESTAMP
)
"""

DDL_MOVEMENTS = f"""
CREATE TABLE IF NOT EXISTS {TABLE_MOVEMENTS} (
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
  user_email      STRING,
  photo_base64   STRING
)
"""

# Migrações: rodar com --migrate. Se a coluna já existir, o script ignora o erro.
MIGRATIONS_MOVEMENTS = [
    f"ALTER TABLE {TABLE_MOVEMENTS} ADD COLUMN user_email STRING;",
    f"ALTER TABLE {TABLE_MOVEMENTS} ADD COLUMN photo_base64 STRING;",
]

# Instock: qty_total e qty_reserved (disponível = qty_total - qty_reserved). Migrar: qty_total = quantity, qty_reserved = 0.
MIGRATIONS_INSTOCK = [
    f"ALTER TABLE {TABLE_INSTOCK} ADD COLUMN qty_total INT64;",
    f"ALTER TABLE {TABLE_INSTOCK} ADD COLUMN qty_reserved INT64;",
    f"UPDATE {TABLE_INSTOCK} SET qty_total = SAFE_CAST(quantity AS INT64), qty_reserved = 0 WHERE qty_total IS NULL AND quantity IS NOT NULL;",
]

DDL_INVENTORY_COUNT = """
CREATE TABLE IF NOT EXISTS `tractian-bi.operations.operations_webapp_warehouse_inventory_count` (
  count_id         STRING   NOT NULL,
  count_at         TIMESTAMP NOT NULL,
  address          STRING,
  item_code        STRING,
  quantity_system  STRING,
  quantity_counted STRING,
  quantity_diff    STRING,
  adjusted         BOOL,
  description      STRING
)
"""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cria tabelas WMS no BigQuery")
    parser.add_argument("--migrate", action="store_true", help="Executa migrações (instock, movements, etc.)")
    args = parser.parse_args()

    print("Conectando ao BigQuery...")
    client = get_client()

    for name, ddl in [
        ("operations_webapp_warehouse_users_wms", DDL_USERS_WMS),
        ("operations_webapp_warehouse_enderecamentos", DDL_ENDERECAMENTOS),
        ("operations_webapp_warehouse_address_sku", DDL_ADDRESS_SKU),
        ("operations_webapp_warehouse_order_reservations", DDL_ORDER_RESERVATIONS),
        ("operations_webapp_warehouse_params", DDL_PARAMS),
        ("operations_webapp_warehouse_movements", DDL_MOVEMENTS),
        ("operations_webapp_warehouse_inventory_count", DDL_INVENTORY_COUNT),
    ]:
        print(f"Criando {name}...")
        client.query(ddl).result()
        print(f"  OK: {name}")

    if args.migrate:
        for label, migrations in [
            ("movements", MIGRATIONS_MOVEMENTS),
            ("instock", MIGRATIONS_INSTOCK),
        ]:
            if not migrations:
                continue
            print(f"Executando migrações ({label})...")
            for sql in migrations:
                sql = sql.strip()
                if not sql or sql.startswith("#"):
                    continue
                try:
                    client.query(sql).result()
                    print("  OK:", sql[:70] + "..." if len(sql) > 70 else sql)
                except Exception as e:
                    print("  AVISO (pode já estar aplicado):", str(e)[:80])

    print("Concluído.")


if __name__ == "__main__":
    main()
    sys.exit(0)
