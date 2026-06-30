import sys
import os

if "/home/ullah/airflow-dev/dags" not in sys.path and os.path.exists("/home/ullah/airflow-dev/dags"):
    sys.path.insert(0, "/home/ullah/airflow-dev/dags")

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.sdk import task
from airflow.providers.amazon.aws.transfers.sql_to_s3 import SqlToS3Operator
from airflow.providers.postgres.hooks.postgres import PostgresHook
# from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

from configs.wallet_configs import INGESTION_CONFIGS
from libs.s3_snapshot_load import upsert_from_s3_to_postgres


# ---------------------------------------------------------------------------
# Shared helper — single source of truth for the incremental cutoff.
# Both check_source_data and build_query call this so they always operate
# on exactly the same window.
#
# FRESHNESS FIX: the previous version snapped the cutoff to midnight UTC.
# That was a no-op under @daily (data_interval_start is already midnight),
# but under @hourly it froze the cutoff for 24 runs in a row and then jumped
# it a full day at once — meaning the window queried by each hourly run grew
# steadily larger throughout the day instead of moving forward by an hour
# each time. This is now a true rolling cutoff: it moves with every run,
# so window size stays constant regardless of schedule frequency.
# ---------------------------------------------------------------------------
def _incremental_cutoff(data_interval_start: datetime, lookback_hours: int) -> datetime:
    """
    Subtract lookback_hours from data_interval_start. No snapping —
    the cutoff moves forward by exactly one schedule interval on every run.
    E.g. data_interval_start=2024-12-05 14:00, lookback_hours=2
         → 2024-12-05 12:00
    """
    return data_interval_start - timedelta(hours=lookback_hours)


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


def _require_data_interval_bounds(context: dict, table: str) -> tuple[datetime, datetime]:
    """
    BUG FIX (#6) + FRESHNESS FIX: both check_source_data and build_query need
    data_interval_start (for the cutoff) and data_interval_end (for the new
    upper bound below). Centralized here so both tasks fail the same,
    readable way on manual triggers without a logical date, instead of a
    raw KeyError.
    """
    data_interval_start = context.get("data_interval_start")
    data_interval_end = context.get("data_interval_end")
    if not data_interval_start or not data_interval_end:
        raise RuntimeError(
            f"[{table}] data_interval_start/data_interval_end missing from context. "
            "Ensure the DAG is triggered by the scheduler (not manually without a logical date)."
        )
    return data_interval_start, data_interval_end


# ---------------------------------------------------------------------------
# Task 1 — Count rows that will be ingested.
# Same cutoff logic as build_query so the count is meaningful.
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

    # Incremental: count within the same window build_query will use.
    # FRESHNESS FIX: added an upper bound (data_interval_end) alongside the
    # lower bound. Previously the query was open-ended ("cutoff and later"),
    # so a run that executed late, or any run under the old midnight-snapped
    # cutoff, would silently scan more data the later it ran. Bounding both
    # ends gives every run a fixed-size window regardless of execution delay.
    data_interval_start, data_interval_end = _require_data_interval_bounds(context, table)
    cutoff = _incremental_cutoff(data_interval_start, config.lookback_hours)
    logging.info(
        f"[{table}] Incremental load — counting rows where "
        f"{config.delta_column} >= {cutoff} AND < {data_interval_end} "
        f"({config.lookback_hours}h lookback, rolling)"
    )
    query = (
        f"SELECT COUNT(*) FROM {table} "
        f"WHERE {config.delta_column} >= '{cutoff:%Y-%m-%d %H:%M:%S}' "
        f"AND {config.delta_column} < '{data_interval_end:%Y-%m-%d %H:%M:%S}'"
    )
    result = hook.get_first(query)
    count = result[0] if result else 0
    logging.info(f"[{table}] {count} rows in window")
    return count


# ---------------------------------------------------------------------------
# Task 2 — Short-circuit: skip everything downstream when nothing to ingest.
#
# BUG FIX (#1): this was commented out in the original DAG, which meant
# every run extracted and upserted even when check_source_data found 0 rows —
# wasted Postgres/S3 round-trips on every empty-window run.
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
#   • delta_column is set   → incremental SELECT bounded to
#                             [rolling cutoff, data_interval_end)
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
    data_interval_start, data_interval_end = _require_data_interval_bounds(context, table)
    cutoff = _incremental_cutoff(data_interval_start, config.lookback_hours)
    logging.info(
        f"[{table}] Building incremental query — "
        f"cutoff={cutoff}, upper_bound={data_interval_end} "
        f"({config.lookback_hours}h lookback, rolling)"
    )
    return (
        f"SELECT * FROM {table} "
        f"WHERE {config.delta_column} >= '{cutoff:%Y-%m-%d %H:%M:%S}'::timestamptz "
        f"AND {config.delta_column} < '{data_interval_end:%Y-%m-%d %H:%M:%S}'::timestamptz"
    )


@task
def upsert_data(config, bucket, file_path, batch_size=10000):
    # BUG FIX (#7): load_strategy is now passed explicitly in both branches
    # rather than relying on the function default for the incremental case —
    # makes the intent visible at the call site and avoids surprises if the
    # default in upsert_from_s3_to_postgres ever changes.
    if config.delta_column is None:
        logging.info(f"Performing full table load (replace) for {config.target_table}")
        load_strategy = "replace"
    else:
        logging.info(f"Performing incremental load (upsert) for {config.target_table}")
        load_strategy = "upsert"

    return upsert_from_s3_to_postgres(
        bucket=bucket,
        file_path=file_path,
        target_conn_id=config.target_conn_id,
        target_table=config.target_table,
        primary_keys=config.primary_keys,
        file_format=config.file_format,
        aws_conn_id="aws_s3-test",
        batch_size=batch_size,
        load_strategy=load_strategy,
    )


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="ingest_sare_postgres",
    start_date=datetime(2024, 12, 1),
    # FRESHNESS FIX: moved from @daily to @hourly. The rolling cutoff +
    # bounded window above only pay off at sub-daily cadence — at @daily
    # they behave identically to the old code.
    #
    # CAUTION: this schedule applies to every config in INGESTION_CONFIGS,
    # including any with delta_column=None (full table loads). Those will
    # now TRUNCATE + re-insert the entire source table every hour instead
    # of once a day. If you have full-load tables of meaningful size,
    # consider splitting them into a separate, less-frequent DAG rather
    # than letting them ride along on this @hourly schedule.
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

        # 2. Short-circuit if nothing to do (skips build_query + extract + upsert)
        gate = should_proceed.override(
            task_id=f"should_proceed_{table_name}"
        )(row_count=check)

        # 3. Build the SQL for this run (result stored in XCom)
        sql = build_query.override(
            task_id=f"build_query_{table_name}"
        )(config)

        # 4. Extract from Postgres → S3
        #    The sql field pulls the query built in step 3 via XCom at runtime.
        extract = SqlToS3Operator(
            task_id=f"extract_to_s3_{table_name}",
            query=sql,  # This will pull the query string from XCom
            s3_bucket=config.bucket,
            s3_key=config.file_path,
            sql_conn_id=config.source_conn_id,
            aws_conn_id="aws_s3-test",
            replace=True,
            file_format=config.file_format,
        )

        # 5. Upsert from S3 storage into target postgres table
        upsert = upsert_data.override(
            task_id=f"upsert_{table_name}"
        )(config, config.bucket, config.file_path)

        # BUG FIX (#2): the original chain was `check >> sql >> extract >> upsert`,
        # which never actually included `gate` in the graph — the short-circuit
        # task existed but had no edges, so it could never skip anything.
        # Correct dependency chain:
        #   check_source_data → should_proceed → build_query → extract_to_s3 → upsert
        check >> gate >> sql >> extract >> upsert
        all_upsert_tasks.append(upsert)