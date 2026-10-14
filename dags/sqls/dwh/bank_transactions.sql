select
    id,
    account_number,
    amount::float as amount,
    bank_id,
    account_name,
    recipient_name, 
    payment_purpose,
    wallet_transaction_type,
    deleted_at::timestamp as deleted_at,
    created_at::timestamp as created_at,
    created_by,
    updated_at::timestamp as updated_at,
    updated_by
from sare_wallet.bank_transactions