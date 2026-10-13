# Sare Wallet ELT Pipeline

Airflow project that extracts operational data from the Sare Wallet Postgres
database, lands it in S3, loads it into an analytics Postgres instance, and
transforms it into a query-optimized `dwh` schema.

## Pipeline architecture

```
                 EXTRACT                    LOAD                      TRANSFORM
 ┌────────────┐   SQL    ┌──────────┐  parquet  ┌──────────────────┐  SQL  ┌──────────────────┐
 │ wallet_db  │ ───────► │    S3    │ ────────► │ prod_analytics   │ ────► │ prod_analytics   │
 │ (source,   │          │ (staging │           │ sare_wallet.*    │       │ dwh.*            │
 │ Postgres)  │          │  bucket) │           │ (raw, upserted)  │       │ (curated, indexed│
 └────────────┘          └──────────┘           └──────────────────┘       │  for consumption)│
                                                                            └──────────────────┘
   ingest_sare_postgres DAG (@hourly)                                transform_dwh DAG (triggered)
```

The pipeline is split into two DAGs that hand off to each other:

1. **`ingest_sare_postgres`** — per-table Extract-and-Load (EL) from the
   wallet database into a raw mirror schema (`sare_wallet.*`) in the
   analytics database, staging each table as parquet in S3 along the way.
2. **`transform_dwh`** — reads the raw `sare_wallet.*` tables and rebuilds
   the curated `dwh.*` tables from the SQL files in `dags/sqls/dwh/`, then
   indexes them.

## Directory structure

```
dags/
├── ingest_wallet_db.py          # DAG: ingest_sare_postgres (extract + load)
├── transform_dwh.py             # DAG: transform_dwh (transform + index)
├── parquet_to_gcp.py            # Standalone example DAG (parquet -> GCS), unrelated to the wallet pipeline
├── configs/
│   ├── wallet_configs.py        # INGESTION_CONFIGS — one entry per source table
│   └── wallet_transform_config.py  # TRANSFORM_CONFIGS — one entry per dwh table + its indexes
├── libs/
│   └── s3_snapshot_load.py      # Shared helper: load a parquet file from S3 into Postgres
└── sqls/
    └── dwh/*.sql                # One SELECT per dwh table, read and materialized by transform_dwh

config/
└── airflow.cfg                  # Airflow configuration used by the containers

backups/
└── *.backup                     # Snapshots of earlier DAG versions kept for reference

Dockerfile, docker-compose.yaml, .env   # Local Airflow (LocalExecutor + Postgres) via Docker Compose
sare_wallet_db_layout.sql               # Reference schema/DDL for the source wallet database
```

## DAG 1: `ingest_sare_postgres` (extract + load)

File: `dags/ingest_wallet_db.py`
Schedule: `@hourly`, `catchup=False`

Driven by the `INGESTION_CONFIGS` list in `dags/configs/wallet_configs.py`,
one `IngestionConfig` per source table:

| Field | Purpose |
|---|---|
| `source_conn_id` / `source_table` | Where to read from (`wallet_db_test`) |
| `target_conn_id` / `target_table` | Where to load to (`prod_analytics`, `sare_wallet.<table>`) |
| `delta_column` | Column used for incremental extraction; `None` means full-table load |
| `lookback_hours` | Rolling window size for incremental extraction |
| `bucket` / `file_path` | S3 staging location (parquet, partitioned by `dt=`/`ts=`) |
| `primary_keys` | Used to upsert (`ON CONFLICT`) into the target table |

For every config, the DAG builds this dynamic task chain:

```
check_source_data → should_proceed → build_query → extract_to_s3 → upsert
```

- **`check_source_data`** — counts rows in the current window (or the whole
  table for full loads).
- **`should_proceed`** — a short-circuit task; skips the rest of the chain
  for that table when the count is 0, avoiding empty round-trips to
  Postgres/S3.
- **`build_query`** — builds the extraction SQL. Incremental tables use a
  rolling window `[data_interval_start - lookback_hours, data_interval_end)`
  so the window size stays constant regardless of run delay; full-load
  tables (`delta_column=None`) just select everything.
- **`extract_to_s3`** (`SqlToS3Operator`) — runs the query against the
  wallet DB and writes the result as parquet to S3.
- **`upsert`** — calls `upsert_from_s3_to_postgres` (in
  `dags/libs/s3_snapshot_load.py`), which downloads the parquet file,
  creates/alters the target table as needed, and either `TRUNCATE`s +
  inserts (full load) or upserts on the primary key (incremental load) into
  `prod_analytics`.

## DAG 2: `transform_dwh` (transform + index)

File: `dags/transform_dwh.py`
Schedule: `None` (triggered downstream of the ingest DAG rather than on its
own schedule)

Driven by `TRANSFORM_CONFIGS` in `dags/configs/wallet_transform_config.py`,
one `TransformConfig` per curated table:

| Field | Purpose |
|---|---|
| `sql_file` | SQL file under `dags/sqls/dwh/` containing the `SELECT` that defines the table |
| `target_table` | Table name created under the `dwh` schema |
| `depends_on` | Optional list of tables this one depends on, for ordering |
| `indexes` | List of `IndexConfig` entries to create after the table is built |

Task flow:

1. **`create_dwh_schema`** — creates the `dwh` schema if missing.
2. For every independent table (no `depends_on`): **`transform_<table>`**
   builds a `_temp` table from the SQL file, then swaps it in for the live
   table (drop + rename), followed by **`index_<table>`** creating any
   configured indexes.
3. Dependent tables run only after all independent tables' indexes are in
   place, following the same transform → index pattern.
4. **`log_transform_summary`** — logs row counts and index counts for every
   table once everything has finished.

## Supporting modules

- **`dags/libs/s3_snapshot_load.py`** — the only piece of ingestion logic
  shared across all tables: downloads a parquet file from S3, infers/adds
  columns as `TEXT`, and performs either a truncate-and-replace or an
  upsert into the target Postgres table.
- **`dags/configs/wallet_configs.py`** / **`wallet_transform_config.py`** —
  the single source of truth for "which tables exist in this pipeline and
  how are they loaded/transformed." Adding a new source table only
  requires a new `IngestionConfig` (and, if it needs curating, a new SQL
  file plus `TransformConfig`) — no DAG code changes.
- **`dags/parquet_to_gcp.py`** — a standalone sample DAG (dummy data →
  parquet → GCS) not wired into the wallet ELT flow; useful as a reference
  for GCS-based loads.

## Required Airflow connections

| Connection ID | Used for |
|---|---|
| `wallet_db_test` | Source: Sare Wallet Postgres database |
| `prod_analytics` | Target: analytics Postgres database (`sare_wallet.*` and `dwh.*`) |
| `aws_s3-test` | S3 staging bucket for parquet files |

## Running locally

See `docker-compose.yaml` — brings up Postgres (Airflow metadata DB) and the
Airflow API server/scheduler/dag-processor/triggerer with `LocalExecutor`.
`Dockerfile` extends `apache/airflow:3.2.0` with `requirements.txt`. Start
with `docker compose up -d` (after `docker compose up airflow-init` on first
run); UI at `http://localhost:8080`.
