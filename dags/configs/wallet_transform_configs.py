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
    TransformConfig(
        sql_file="ledger_accounts.sql",
        target_table="ledger_accounts",
        description="Table view for sare wallet ledger accounts",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for ledger accounts table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="overdraft_repayments.sql",
        target_table="overdraft_repayments",
        description="Table view for sare wallet overdraft repayments, tracks repayments for overdraft loans",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for overdraft repayments table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="overdraft_rollovers.sql",
        target_table="overdraft_rollovers",
        description="Table view for sare wallet overdraft rollovers, tracks rollovers for overdraft loans",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for overdraft rollovers table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="overdraft_draws.sql",
        target_table="overdraft_draws",
        description="Table view for sare wallet overdraft draws",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for overdraft draws table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="overdraft_guarantors.sql",
        target_table="overdraft_guarantors",
        description="Table view for sare wallet overdraft guarantors, shows gurantors for overdraft accounts",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for overdraft guarantors table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="overdraft_account_histories.sql",
        target_table="overdraft_account_histories",
        description="Shows history of overdraft accounts, including status changes and other relevant events",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for overdraft account histories table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="overdraft_accounts.sql",
        target_table="overdraft_accounts",
        description="Table view for sare wallet overdraft accounts, shows all overdraft accounts and their current status",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for overdraft accounts table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="wallet_transactions.sql",
        target_table="wallet_transactions",
        description="shows all wallet transactions and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for wallet transactions table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="mobile_money_transactions.sql",
        target_table="mobile_money_transactions",
        description="shows all mobile money transactions and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for mobile money transactions table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="wallets.sql",
        target_table="wallets",
        description="shows all wallets and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for wallets table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="revenue_split_configuration.sql",
        target_table="revenue_split_configurations",
        description="shows all revenue split configurations between sare and partner organizations",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for revenue split configurations table"
            ),
        ]
    ),
    # TransformConfig(
    #     sql_file="agent_transactions.sql",
    #     target_table="agent_transactions",
    #     description="shows all agent transactions and their details",
    #     indexes=[
    #         IndexConfig(
    #             name="id",
    #             columns=["id"],
    #             unique=True,
    #             description="Primary key index for agent transactions table"
    #         ),
    #     ]
    # ),
    # TransformConfig(
    #     sql_file="areas.sql",
    #     target_table="areas",
    #     description="shows all areas and their details",
    #     indexes=[
    #         IndexConfig(
    #             name="id",
    #             columns=["id"],
    #             unique=True,
    #             description="Primary key index for areas table"
    #         ),
    #     ]
    # ),
    TransformConfig(
        sql_file="bank_transactions.sql",
        target_table="bank_transactions",
        description="shows all bank transactions and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for bank transactions table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="banks.sql",
        target_table="banks",
        description="shows all banks and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for banks table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="bill_accounts.sql",
        target_table="bill_accounts",
        description="shows all bill accounts and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for bill accounts table"
            ),
        ]
    ),
    # TransformConfig(
    #     sql_file="bill_payment_transactions.sql",
    #     target_table="bill_payment_transactions",
    #     description="shows all bill payment transactions and their details",
    #     indexes=[
    #         IndexConfig(
    #             name="id",
    #             columns=["id"],
    #             unique=True,
    #             description="Primary key index for bill payment transactions table"
    #         ),
    #     ]
    # ),
    TransformConfig(
        sql_file="business_profiles.sql",
        target_table="business_profiles",
        description="shows all business profiles for business wallets and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for business profiles table"
            ),
        ]
    ),
    # TransformConfig(
    #     sql_file="c2b_mpesa_transactions.sql",
    #     target_table="c2b_mpesa_transactions",
    #     description="shows all customer to business mpesa transactions and their details",
    #     indexes=[
    #         IndexConfig(
    #             name="id",
    #             columns=["id"],
    #             unique=True,
    #             description="Primary key index for c2b mpesa transactions table"
    #         ),
    #     ]
    # ),
    TransformConfig(
        sql_file="ledger_postings.sql",
        target_table="ledger_postings",
        description="shows all ledger postings and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for ledger postings table"
            ),
        ]
    ),
    TransformConfig(
        sql_file="sw_journal_entries.sql",
        target_table="journal_entries",
        description="shows all journal entries and their details",
        indexes=[
            IndexConfig(
                name="id",
                columns=["id"],
                unique=True,
                description="Primary key index for journal entries table"
            ),
        ]
    ),
]
