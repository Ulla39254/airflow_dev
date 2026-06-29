import os
import tempfile
import logging
from psycopg2.extras import execute_values

def _to_sql_value(val):
    """Convert pandas/NumPy scalars and missing values into SQL/psycopg2 safe Python types.
    - pd.NA/NaN -> None
    - numpy scalars -> native python scalars via .item()
    - pandas Timestamp -> python datetime
    - leave other python-native types as-is
    """
    # Import heavy numeric/pandas libs lazily to avoid slowing DAG imports
    import pandas as pd
    import numpy as np

    if val is None:
        return None
    # Handle pandas NA/NaN for various dtypes; guard for non-scalar types
    try:
        if pd.isna(val):
            return None
    except TypeError:
        # Some objects raise on isna; ignore and continue
        pass
    # Convert numpy scalar types to native python
    if isinstance(val, np.generic):
        return val.item()
    # Convert pandas Timestamp to python datetime
    if isinstance(val, pd.Timestamp):
        return val.to_pydatetime()
    return val

def upsert_from_s3_to_postgres(
    bucket: str,
    file_path: str,
    target_conn_id: str,
    target_table: str,
    primary_keys: list,
    file_format: str = "parquet",
    aws_conn_id: str = "aws_em_test",
    batch_size: int = 10000,
    load_strategy: str = "upsert"  # "upsert" or "replace"
):
    """
    Generalized upsert from S3 to Postgres.
    - Creates table if missing.
    - Adds new columns if present in source.
    - Ignores missing columns in source.
    - Upserts using ON CONFLICT or replaces data based on load_strategy.
    
    Args:
        load_strategy: "upsert" for incremental loads, "replace" for full table loads
    """
    logging.info(f"Starting {load_strategy} from S3 bucket '{bucket}' file '{file_path}' to table '{target_table}'")

    # Import heavy libraries/hooks lazily so DAG parsing doesn't pay their import cost
    from airflow.providers.amazon.aws.hooks.s3 import S3Hook
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    import pandas as pd

    s3_hook = S3Hook(aws_conn_id=aws_conn_id)
    postgres_hook = PostgresHook(postgres_conn_id=target_conn_id)

    # Create temp directory if it doesn't exist
    os.makedirs('/tmp', exist_ok=True)
    
    # Generate a unique temporary file path
    tmp_file = os.path.join('/tmp', f'airflow_tmp_{next(tempfile._get_candidate_names())}.{file_format}')
    logging.info(f"Created temporary file: {tmp_file}")
    df = None

    try:
        # Get the S3 object and download it directly
        logging.info(f"Attempting to get S3 object: s3://{bucket}/{file_path}")
        s3_object = s3_hook.get_key(
            key=file_path,
            bucket_name=bucket
        )
        
        if not s3_object:
            raise FileNotFoundError(f"File not found in S3: s3://{bucket}/{file_path}")
            
        logging.info("Downloading S3 file...")
        s3_object.download_file(tmp_file)
        logging.info("Download complete")
        
        # Load data from parquet file
        if file_format != "parquet":
            raise ValueError("Only parquet format is supported")

        logging.info("Reading parquet file...")
        df = pd.read_parquet(tmp_file)
        logging.info(f"Loaded DataFrame with {len(df)} rows and columns: {df.columns.tolist()}")
        
        if df.empty:
            logging.warning("Warning: DataFrame is empty!")
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

    if df is None or df.empty:
        if df is None:
            logging.warning("No dataframe was loaded from S3 (df is None)")
        else:
            logging.warning("Warning: DataFrame is empty!")
        return

    conn = postgres_hook.get_conn()
    cursor = conn.cursor()

    columns = df.columns.tolist()
    columns_str = ', '.join([f'"{col}"' for col in columns])
    pk_str = ', '.join([f'"{pk}"' for pk in primary_keys])

    # Create table if not exists
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {target_table} (
        {', '.join([f'"{col}" TEXT' for col in columns])},
        PRIMARY KEY ({pk_str})
    );
    """
    logging.info(f"Creating table if not exists: {target_table}")
    cursor.execute(create_table_sql)

    # Get existing columns
    schema_name = target_table.split('.')[0]
    table_name = target_table.split('.')[-1]
    logging.info(f"Checking existing columns in {schema_name}.{table_name}")
    cursor.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = '{table_name}'
        AND table_schema = '{schema_name}'
    """)
    existing_columns = set([row[0] for row in cursor.fetchall()])

    # Add new columns
    for col in columns:
        if col not in existing_columns:
            logging.info(f"Adding new column: {col}")
            cursor.execute(f'ALTER TABLE {target_table} ADD COLUMN "{col}" TEXT;')

    # Normalize nulls for DB insertion: ensure pd.NA/NaN are converted to None 
    # astype(object) ensures extension dtypes (Int64, boolean, string[pyarrow], etc.) become object so None can be stored
    df = df.astype(object).where(pd.notnull(df), None)

    # Handle different load strategies
    if load_strategy == "replace":
        # For full table loads, truncate table first
        logging.info(f"Truncating table {target_table} for full load")
        cursor.execute(f"TRUNCATE TABLE {target_table};")
        
        # Simple insert for replace strategy
        insert_sql = f"INSERT INTO {target_table} ({columns_str}) VALUES %s;"
        logging.info("Using REPLACE strategy - will truncate and insert all data")
    else:
        # Build upsert SQL for incremental loads
        update_str = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in columns if col not in primary_keys])
        insert_sql = f"INSERT INTO {target_table} ({columns_str}) VALUES %s ON CONFLICT ({pk_str}) DO UPDATE SET {update_str};"
        logging.info("Using UPSERT strategy - will update existing rows and insert new ones")

    # Prepare data rows as tuples
    def row_generator():
        for row in df[columns].itertuples(index=False, name=None):
            yield tuple(_to_sql_value(v) for v in row)

    # Execute in batches to reduce round-trips
    total = len(df)
    operation = "replace" if load_strategy == "replace" else "upsert"
    logging.info(f"Starting batched {operation} of {total} rows (batch_size={batch_size})")
    batch = []
    processed = 0
    for tpl in row_generator():
        batch.append(tpl)
        if len(batch) >= batch_size:
            execute_values(cursor, insert_sql, batch, page_size=len(batch))
            processed += len(batch)
            logging.info(f"Processed {processed} rows...")
            batch.clear()
    if batch:
        execute_values(cursor, insert_sql, batch, page_size=len(batch))
        processed += len(batch)
        logging.info(f"Processed {processed} rows total.")

    conn.commit()
    cursor.close()
    conn.close()
    logging.info(f"{operation.capitalize()} completed successfully")
