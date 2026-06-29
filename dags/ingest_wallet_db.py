import sys
import os

if "/home/ullah/airflow-dev/dags" not in sys.path and os.path.exists("/home/ullah/airflow-dev/dags"):
    sys.path.insert(0, "/home/ullah/airflow-dev/dags")

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.sdk import Connection, Variables
from airflow.sdk import task
from airflow.providers.amazon.aws.transfers.sql_to_s3 import SqlToS3Operator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from configs.wallet_configs import INGESTION_CONFIGS
from libs.s3_snapshot_load import upsert_from_s3_to_postgres


# ---------------------------------------------------------------------------
# Shared helper — single source of truth for the incremental cutoff.
# Both check_source_data and build_query call this so they always operate
# on exactly the same window.
# ---------------------------------------------------------------------------
def _incremental_cutoff(data_interval_start: datetime, lookback_hours: int) -> datetime:
    """
    Subtract lookback_hours from data_interval_start and snap to midnight UTC.
    E.g. data_interval_start=2024-12-05 14:00, lookback_hours=48
         → 2024-12-03 14:00 → snap → 2024-12-03 00:00:00
    """
    return (data_interval_start - timedelta(hours=lookback_hours)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def _validate_incremental_config(config) -> None:
    """
    Raise early if delta_column is set but lookback_hours is missing.
    Prevents a silent default from hiding a misconfiguration.
    """
    if config.delta_column is not None and not config.lookback_hours:
        raise ValueError(
            f"[{config.source_table}] delta_column='{config.delta_column}' requires "
            "lookback_hours to be set. Either provide lookback_hours or set "
            "delta_column=None to do a full table load."
        )


# ---------------------------------------------------------------------------
# Task 1 — Count rows that will be ingested.
# Uses the exact same cutoff logic as build_query so the count is meaningful.
# ---------------------------------------------------------------------------
@task
def check_source_data(config, **context) -> int:
    _validate_incremental_config(config)

    hook = PostgresHook(postgres_conn_id=config.source_conn_id)
    table = config.source_table

    # Full load: delta_column is None → count everything
    if config.delta_column is None:
        logging.info(f"[{table}] Full load — counting all rows")
        result = hook.get_first(f"SELECT COUNT(*) FROM {table}")
        count = result[0] if result else 0
        logging.info(f"[{table}] {count} total rows found")
        return count

    # Incremental: count within the same window build_query will use
    cutoff = _incremental_cutoff(context["data_interval_start"], config.lookback_hours)
    logging.info(
        f"[{table}] Incremental load — counting rows where "
        f"{config.delta_column} >= {cutoff} "
        f"({config.lookback_hours}h lookback, snapped to midnight)"
    )
    query = (
        f"SELECT COUNT(*) FROM {table} "
        f"WHERE {config.delta_column} >= '{cutoff:%Y-%m-%d %H:%M:%S}'"
    )
    result = hook.get_first(query)
    count = result[0] if result else 0
    logging.info(f"[{table}] {count} rows in window")
    return count


# ---------------------------------------------------------------------------
# Task 2 — Short-circuit: skip everything downstream when nothing to ingest.
# ---------------------------------------------------------------------------
@task.short_circuit
def should_proceed(row_count: int) -> bool:
    if row_count == 0:
        logging.info("Row count is 0 — skipping downstream tasks")
        return False
    logging.info(f"{row_count} rows queued — proceeding with extraction")
    return True


# ---------------------------------------------------------------------------
# Task 3 — Build the extraction SQL for this run.
#   • delta_column is None  → full SELECT (no WHERE clause)
#   • delta_column is set   → incremental SELECT with midnight-snapped cutoff
# The query is pushed to XCom and pulled by SqlToS3Operator via Jinja.
# ---------------------------------------------------------------------------
@task
def build_query(config, **context) -> str:
    _validate_incremental_config(config)

    table = config.source_table

    # Full load
    if config.delta_column is None:
        logging.info(f"[{table}] Building full table query")
        return f"SELECT * FROM {table}"

    # Incremental
    data_interval_start = context.get("data_interval_start")
    if not data_interval_start:
        # Safeguard: data_interval_start should always be present for scheduled runs
        raise RuntimeError(
            f"[{table}] data_interval_start is missing from context. "
            "Ensure the DAG is triggered by the scheduler (not manually without a logical date)."
        )

    cutoff = _incremental_cutoff(data_interval_start, config.lookback_hours)
    logging.info(
        f"[{table}] Building incremental query — "
        f"cutoff={cutoff} ({config.lookback_hours}h lookback, snapped to midnight)"
    )
    return (
        f"SELECT * FROM {table} "
        f"WHERE {config.delta_column} >= '{cutoff:%Y-%m-%d %H:%M:%S}'::timestamptz"
    )
@task
def upsert_data(config, bucket, file_path, batch_size=10000):
    if config.delta_column is None:
        # For full table loads, use replace strategy (truncate and insert)
        logging.info(f"Performing full table load (replace) for {config.target_table}")
        return upsert_from_s3_to_postgres(
            bucket=bucket,
            file_path=file_path,
            target_conn_id=config.target_conn_id,
            target_table=config.target_table,
            primary_keys=config.primary_keys,
            file_format=config.file_format,
            aws_conn_id="aws_s3-test",
            batch_size=batch_size,
            load_strategy="replace"
        )
    else:
        # For incremental loads, use upsert strategy
        logging.info(f"Performing incremental load (upsert) for {config.target_table}")
        return upsert_from_s3_to_postgres(
            bucket=bucket,
            file_path=file_path,
            target_conn_id=config.target_conn_id,
            target_table=config.target_table,
            primary_keys=config.primary_keys,
            file_format=config.file_format,
            aws_conn_id="aws_s3-test",
            batch_size=batch_size,
            load_strategy="upsert"
        )



# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="ingest_sare_postgres",
    start_date=datetime(2024, 12, 1),
    schedule="@hourly",
    catchup=False,
    render_template_as_native_obj=True,
    tags=["sare", "wallet", "ingest"],
) as dag:
    
    all_upsert_tasks = []  # Collect upsert tasks for potential downstream dependencies
    for config in INGESTION_CONFIGS:
        table_name = config.source_table.replace(".", "_")

        # 1. Count rows to be ingested
        check = check_source_data.override(
            task_id=f"check_source_data_{table_name}"
        )(config)

        # 2. Short-circuit if nothing to do (skips build_query + extract)
        gate = should_proceed.override(
            task_id=f"should_proceed_{table_name}"
        )(row_count=check)

        # 3. Build the SQL for this run (result stored in XCom)
        sql = build_query.override(
            task_id=f"build_query_{table_name}"
        )(config)

        # 4. Extract from Postgres → S3
        #    The sql field pulls the query built in step 3 via XCom at runtime.
        #    The S3 key is partitioned by execution hour for easy incremental management.
        extract = SqlToS3Operator(
            task_id=f"extract_to_s3_{table_name}",
            query= sql,  # This will pull the query string from XCom
            s3_bucket=config.bucket,
            s3_key=config.file_path,
            sql_conn_id=config.source_conn_id,
            aws_conn_id= "aws_s3-test",
            replace=True,
            file_format=config.file_format,
        )

        # 5. psert from s3 storage to target postgres table
        upsert = upsert_data.override(
            task_id = f"upsert_{table_name}"
        )(config, config.bucket, config.file_path)

        # Dependency chain:
        # check_source_data → should_proceed → build_query → extract_to_s3
        # (check → gate dependency is implicit via XCom parameter passing)
        check >> gate >> sql >> extract >> upsert
        all_upsert_tasks.append(upsert)