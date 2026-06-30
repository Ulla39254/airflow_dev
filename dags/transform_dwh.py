import sys
import os
# sys.path.insert(0, '/home/ubuntu/airflow/dags')

# Only add path fix for production server (not Docker)
if '/home/ubuntu/airflow/dags' not in sys.path and os.path.exists('/home/ubuntu/airflow/dags'):
   sys.path.insert(0, '/home/ubuntu/airflow/dags')

import logging
from datetime import datetime
from pathlib import Path
from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from configs.wallet_transform_config import TRANSFORM_CONFIGS, IndexConfig

def read_sql_file(sql_file_path):
    """Read SQL file content"""
    try:
        with open(sql_file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")


def create_index_sql(table_name: str, index_config: IndexConfig) -> str:
    """Generate CREATE INDEX SQL statement from IndexConfig"""
    index_name = f"idx_{table_name}_{index_config.name}"
    columns_str = ", ".join(index_config.columns)
    
    # Build the basic CREATE INDEX statement
    unique_clause = "UNIQUE " if index_config.unique else ""
    method_clause = f" USING {index_config.method}" if index_config.method != "btree" else ""
    where_clause = f" WHERE {index_config.where_clause}" if index_config.where_clause else ""
    
    sql = f"CREATE {unique_clause}INDEX IF NOT EXISTS {index_name} ON dwh.{table_name} {method_clause}({columns_str}){where_clause};"
    
    return sql


@task
def create_table_indexes(config):
    """Create indexes for a table based on its configuration"""
    if not config.indexes:
        logging.info(f"No indexes configured for {config.target_table}")
        return {"table": config.target_table, "indexes_created": 0, "status": "success"}
    
    hook = PostgresHook(postgres_conn_id="prod_analytics")
    table_name = config.target_table
    indexes_created = 0
    
    logging.info(f"Creating {len(config.indexes)} indexes for {table_name}")
    
    try:
        for index_config in config.indexes:
            index_sql = create_index_sql(table_name, index_config)
            
            logging.info(f"Creating index: idx_{table_name}_{index_config.name}")
            logging.debug(f"Index SQL: {index_sql}")
            
            # Execute index creation
            hook.run(index_sql)
            indexes_created += 1
            
            # Log index purpose if provided
            if index_config.description:
                logging.info(f"  Purpose: {index_config.description}")
        
        logging.info(f"Successfully created {indexes_created} indexes for {table_name}")
        return {
            "table": table_name, 
            "indexes_created": indexes_created, 
            "status": "success"
        }
        
    except Exception as e:
        logging.error(f"Failed to create indexes for {table_name}: {str(e)}")
        raise


@task
def create_dwh_schema():
    """Create the dwh schema if it doesn't exist"""
    hook = PostgresHook(postgres_conn_id="prod_analytics")
    
    sql = """
    CREATE SCHEMA IF NOT EXISTS dwh;
    
    -- Grant permissions (adjust as needed)
    GRANT USAGE ON SCHEMA dwh TO PUBLIC;
    GRANT CREATE ON SCHEMA dwh TO PUBLIC;
    """
    
    hook.run(sql)
    logging.info("DWH schema created/verified")


@task
def transform_table(config, sql_base_path="sqls/dwh"):
    """
    Transform a single table: drop, create, and populate
    """
    hook = PostgresHook(postgres_conn_id="prod_analytics")
    
    # Read SQL file - use path relative to DAGs directory
    if not sql_base_path.startswith('/'):
        # Relative path - construct from current file location
        current_dir = Path(__file__).parent
        sql_file_path = current_dir / sql_base_path / config.sql_file
    else:
        # Absolute path (for Docker deployment)
        sql_file_path = Path(sql_base_path) / config.sql_file
    transform_sql = read_sql_file(sql_file_path)
    
    # Full table replacement approach
    temp_table = f"dwh.{config.target_table}_temp"
    final_table = f"dwh.{config.target_table}"
    
    logging.info(f"Starting transformation for {config.target_table}")
    
    try:
        # Step 1: Drop temp table if exists
        hook.run(f"DROP TABLE IF EXISTS {temp_table} CASCADE;")
        
        # Step 2: Create temp table with data
        create_temp_sql = f"""
        CREATE TABLE {temp_table} AS
        {transform_sql}
        """
        hook.run(create_temp_sql)
        
        # Step 3: Get row count for logging
        count_result = hook.get_first(f"SELECT COUNT(*) FROM {temp_table}")
        row_count = count_result[0] if count_result else 0
        
        # Step 4: Drop old table and rename temp
        hook.run(f"DROP TABLE IF EXISTS {final_table} CASCADE;")
        hook.run(f"ALTER TABLE {temp_table} RENAME TO {config.target_table};")
        
        logging.info(f"Successfully created {final_table} with {row_count:,} rows")
        return {"table": config.target_table, "rows": row_count, "status": "success"}
        
    except Exception as e:
        # Cleanup on failure
        hook.run(f"DROP TABLE IF EXISTS {temp_table} CASCADE;")
        logging.error(f"Failed to transform {config.target_table}: {str(e)}")
        raise


@task 
def log_transform_summary(transform_results, index_results):
    """Log summary of all transformations and indexing"""
    total_tables = len(transform_results)
    successful_tables = len([r for r in transform_results if r['status'] == 'success'])
    total_rows = sum(r['rows'] for r in transform_results if r['status'] == 'success')
    
    total_indexes = sum(r['indexes_created'] for r in index_results if r['status'] == 'success')
    
    logging.info(f"Transform Summary:")
    logging.info(f"  - Tables processed: {total_tables}")
    logging.info(f"  - Successful: {successful_tables}")
    logging.info(f"  - Total rows created: {total_rows:,}")
    logging.info(f"  - Total indexes created: {total_indexes}")
    
    for i, result in enumerate(transform_results):
        status_icon = "✅" if result['status'] == 'success' else "❌"
        index_info = ""
        if i < len(index_results) and index_results[i]['status'] == 'success':
            index_count = index_results[i]['indexes_created']
            index_info = f" [{index_count} indexes]"
        
        logging.info(f"  {status_icon} {result['table']}: {result['rows']:,} rows{index_info}")
    
    # Log performance recommendations
    # logging.info(f"Performance Tips:")
    # logging.info(f"  - Analyze tables: ANALYZE dwh.table_name;")
    # logging.info(f"  - Check index usage: SELECT * FROM pg_stat_user_indexes WHERE schemaname='dwh';")
    # logging.info(f"  - Monitor query performance with EXPLAIN ANALYZE")


with DAG(
    dag_id="transform_dwh",
    start_date=datetime(2024, 12, 1),
    schedule=None,  # Changed from "@hourly" - now triggered by SAP HANA DAG
    catchup=False,
    render_template_as_native_obj=True,
    tags=["transform", "dwh", "sare"],
    description="Transform raw data into user-facing DWH tables with optimized indexes"
) as dag:

    # Create schema first
    create_schema = create_dwh_schema()
    
    # Group configurations by dependencies
    independent_configs = [c for c in TRANSFORM_CONFIGS if not c.depends_on]
    dependent_configs = [c for c in TRANSFORM_CONFIGS if c.depends_on]
    
    # Transform independent tables first (dimensions)
    independent_transform_tasks = []
    independent_index_tasks = []
    
    for config in independent_configs:
        # Create table transformation task
        transform_task = transform_table.override(
            task_id=f"transform_{config.target_table}"
        )(config)
        
        # Create index task
        index_task = create_table_indexes.override(
            task_id=f"index_{config.target_table}"
        )(config)
        
        # Set dependencies
        create_schema >> transform_task >> index_task
        
        independent_transform_tasks.append(transform_task)
        independent_index_tasks.append(index_task)
    
    # Transform dependent tables (facts and aggregations)
    dependent_transform_tasks = []
    dependent_index_tasks = []
    
    for config in dependent_configs:
        # Create table transformation task
        transform_task = transform_table.override(
            task_id=f"transform_{config.target_table}"
        )(config)
        
        # Create index task
        index_task = create_table_indexes.override(
            task_id=f"index_{config.target_table}"
        )(config)
        
        # Set dependencies - wait for all independent indexes to complete
        for independent_index_task in independent_index_tasks:
            independent_index_task >> transform_task
        
        # Index creation happens after table transformation
        transform_task >> index_task
        
        dependent_transform_tasks.append(transform_task)
        dependent_index_tasks.append(index_task)
    
    # Summary task - wait for all transform and index tasks
    all_transform_tasks = independent_transform_tasks + dependent_transform_tasks
    all_index_tasks = independent_index_tasks + dependent_index_tasks
    
    summary = log_transform_summary(all_transform_tasks, all_index_tasks)
    
    # Set final dependencies - summary runs after all indexes are created
    for index_task in all_index_tasks:
        index_task >> summary 
