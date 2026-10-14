select
    id,
    journal_entry_id,
    account_id,
    entry_type,
    amount::float as amount,
    created_at::timestamp as created_at,
    created_by,
    updated_at::timestamp as updated_at,
    updated_by,
    deleted_at::timestamp as deleted_at
from sare_wallet.ledger_postings