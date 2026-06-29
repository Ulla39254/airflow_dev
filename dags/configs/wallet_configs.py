from dataclasses import dataclass
from typing import List, Optional


@dataclass
class IngestionConfig:
    source_conn_id: str
    source_table: str
    target_conn_id: Optional[str]
    target_table: Optional[str]
    delta_column: Optional[str]  # Can be None for full table loads
    bucket: str
    file_path: str
    primary_keys: List[str]
    # lookback window in hours to apply for incremental loads
    lookback_hours: Optional[int] = None
    # using parquet for better performance and data type preservation
    file_format: str = "parquet"


INGESTION_CONFIGS = [
    IngestionConfig(
        source_conn_id="wallet_db_test",
        source_table="public.ledger",
        target_conn_id="prod_analytics",  
        target_table="sare_wallet.ledger",
        delta_column= "updated_at",  # No delta column for full load; adjust if incremental logic is added
        lookback_hours= 48,
        bucket="sare-analytics",
        file_path="ingest/wallet_test/ledger/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
        primary_keys=["id"],
        file_format="parquet"
    ),
    IngestionConfig(
        source_conn_id="wallet_db_test",
        source_table="public.users",
        target_conn_id="prod_analytics",  
        target_table="sare_wallet.users",
        delta_column="updated_at",  # No delta column for full load; adjust if incremental logic is added
        lookback_hours= 48,
        bucket="sare-analytics",
        file_path="ingest/wallet_test/users/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
        primary_keys=["id"],
        file_format="parquet"
    ),
    # IngestionConfig(
    #     source_conn_id="wallet_db_test",
    #     source_table="public.revenue_split_configurations",
    #     target_conn_id="prod_analytics",  
    #     target_table="sare_wallet.revenue_split_configurations",
    #     delta_column=None,  # No delta column for full load; adjust if incremental logic is added
    #     lookback_hours= None,
    #     bucket="sare-analytics",
    #     file_path="ingest/wallet_test/revenue_split_configurations/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
    #     primary_keys=["id"],
    #     file_format="parquet"
    # ),
    # IngestionConfig(
    #     source_conn_id="wallet_db_test",
    #     source_table="public.wallets",
    #     target_conn_id="prod_analytics",  
    #     target_table="sare_wallet.wallets",
    #     delta_column=None,  # No delta column for full load; adjust if incremental logic is added
    #     lookback_hours= None,
    #     bucket="sare-analytics",
    #     file_path="ingest/wallet_test/wallets/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
    #     primary_keys=["id"],
    #     file_format="parquet"
    # ),
    # IngestionConfig(
    #     source_conn_id="wallet_db_test",
    #     source_table="public.mobile_money_transactions",
    #     target_conn_id="prod_analytics",  
    #     target_table="sare_wallet.mobile_money_transactions",
    #     delta_column=None,  # No delta column for full load; adjust if incremental logic is added
    #     lookback_hours= None,
    #     bucket="sare-analytics",
    #     file_path="ingest/wallet_test/mobile_money_transactions/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
    #     primary_keys=["id"],
    #     file_format="parquet"
    # ),
    # IngestionConfig(
    #     source_conn_id="wallet_db_test",
    #     source_table="public.wallet_transactions",
    #     target_conn_id="prod_analytics",  
    #     target_table="sare_wallet.wallet_transactions",
    #     delta_column=None,  # No delta column for full load; adjust if incremental logic is added
    #     lookback_hours= None,
    #     bucket="sare-analytics",
    #     file_path="ingest/wallet_test/wallet_transactions/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
    #     primary_keys=["id"],
    #     file_format="parquet"
    # ),
    # IngestionConfig(
    #     source_conn_id="wallet_db_test",
    #     source_table="public.overdraft_accounts",
    #     target_conn_id="prod_analytics",  
    #     target_table="sare_wallet.overdraft_accounts",
    #     delta_column=None,  # No delta column for full load; adjust if incremental logic is added
    #     lookback_hours= None,
    #     bucket="sare-analytics",
    #     file_path="ingest/wallet_test/overdraft_accounts/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
    #     primary_keys=["id"],
    #     file_format="parquet"
    # ),
    # IngestionConfig(
    #     source_conn_id="wallet_db_test",
    #     source_table="public.overdraft_account_histories",
    #     target_conn_id="prod_analytics",  
    #     target_table="sare_wallet.overdraft_account_histories",
    #     delta_column=None,  # No delta column for full load; adjust if incremental logic is added
    #     lookback_hours= None,
    #     bucket="sare-analytics",
    #     file_path="ingest/wallet_test/overdraft_account_histories/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
    #     primary_keys=["id"],
    #     file_format="parquet"
    # ),
    # IngestionConfig(
    #     source_conn_id="wallet_db_test",
    #     source_table="public.overdraft_guarantors",
    #     target_conn_id="prod_analytics",  
    #     target_table="sare_wallet.overdraft_guarantors",
    #     delta_column=None,  # No delta column for full load; adjust if incremental logic is added
    #     lookback_hours= None,
    #     bucket="sare-analytics",
    #     file_path="ingest/wallet_test/overdraft_guarantors/dt={{ ds }}/ts={{ data_interval_start.strftime('%Y-%m-%dT%H:%M:%S') }}/data.parquet",
    #     primary_keys=["id"],
    #     file_format="parquet"
    # ),
]