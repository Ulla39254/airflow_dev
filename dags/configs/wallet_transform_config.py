from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class IndexConfig:
    name: str                       # Index name (will be prefixed with idx_)
    columns: List[str]              # List of columns for the index
    unique: bool = False            # Whether index should be unique
    method: str = "btree"           # Index method (btree, hash, gin, gist, etc.)
    where_clause: Optional[str] = None  # Optional WHERE clause for partial indexes
    description: str = ""           # Optional description of the index purpose


@dataclass
class TransformConfig:
    sql_file: str                    # Path to SQL file (relative to sql/dwh/)
    target_table: str                # Table name in dwh schema
    depends_on: Optional[List[str]] = None  # Optional dependencies for ordering
    indexes: Optional[List[IndexConfig]] = None  # Indexes to create after table creation
    description: str = ""            # Optional description

TRANSFORM_CONFIGS = [
    TransformConfig(
        sql_file="sare_wallet_users.sql",
        target_table="user_wallet",
        description="User table view for sare wallet",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for users table"
            ),
            # IndexConfig(
            #     name="shofco_id",
            #     columns=["shofco_id"],
            #     unique=True,
            #     description="Unique index for shofco_id in users table"
            # ),
            # IndexConfig(
            #     name="phone",
            #     columns=["phone"],
            #     unique=True,
            #     description="Unique index for phone number in users table"
            # )
        ]
    ),
    TransformConfig(
        sql_file="sare_wallet_ledger.sql",
        target_table="ledger_wallet",
        description="Ledger table view for sare wallet",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for ledger table"
            ),
        ]
    ),
]
