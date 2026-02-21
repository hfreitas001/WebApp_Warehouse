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
  source          STRING
)
"""

# Migrações: adicionar/remover colunas SEM perder dados da tabela.
# - ADD COLUMN: seguro; dados existentes mantidos, nova coluna fica NULL.
# - DROP COLUMN: remove coluna e seus dados (BigQuery suporta desde ~2023).
# - Alterar tipo: BigQuery não tem ALTER COLUMN TYPE; usar nova coluna + backfill + drop antiga.
MIGRATIONS_MOVEMENTS = [
    # Exemplo: adicionar coluna (descomente, rode uma vez com --migrate, depois comente de novo)
    # f"ALTER TABLE {TABLE_MOVEMENTS} ADD COLUMN minha_coluna STRING;",
    # Exemplo: remover coluna (perde os dados dessa coluna)
    # f"ALTER TABLE {TABLE_MOVEMENTS} DROP COLUMN coluna_antiga;",
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
    parser.add_argument("--migrate", action="store_true", help="Executa também as migrações (ALTER TABLE) listadas em MIGRATIONS_MOVEMENTS")
    args = parser.parse_args()

    print("Conectando ao BigQuery...")
    client = get_client()

    print("Criando operations_webapp_warehouse_movements...")
    client.query(DDL_MOVEMENTS).result()
    print("  OK: operations_webapp_warehouse_movements")

    print("Criando operations_webapp_warehouse_inventory_count...")
    client.query(DDL_INVENTORY_COUNT).result()
    print("  OK: operations_webapp_warehouse_inventory_count")

    if args.migrate and MIGRATIONS_MOVEMENTS:
        print("Executando migrações (ADD/DROP COLUMN)...")
        for sql in MIGRATIONS_MOVEMENTS:
            sql = sql.strip()
            if not sql or sql.startswith("#"):
                continue
            client.query(sql).result()
            print("  OK:", sql[:60] + "..." if len(sql) > 60 else sql)
    elif args.migrate:
        print("Nenhuma migração definida em MIGRATIONS_MOVEMENTS.")

    print("Concluído.")


if __name__ == "__main__":
    main()
    sys.exit(0)
