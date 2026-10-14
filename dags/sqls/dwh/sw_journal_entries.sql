select
    id,
    wallet_transaction_id,
    idempotency_key,
    reference_number,
    external_reference_number,
    gateway_reference_number,
    description,
    currency,
    status,
    transaction_date::timestamp as transaction_date,
    posted_at::timestamp as posted_at,
    reversal_of_id,
    created_at::timestamp as created_at,
    created_by,
    updated_at::timestamp as updated_at,
    updated_by,
    deleted_at::timestamp as deleted_at
from sare_wallet.journal_entries