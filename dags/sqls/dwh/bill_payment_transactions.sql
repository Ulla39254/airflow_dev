select
    id,
    bill_provider_id,
    utility_bill_type,
    account_number,
    due_amount::float as due_amount,
    due_date::timestamp as due_date,
    created_at::timestamp as created_at,
    created_by,
    updated_at::timestamp as updated_at,
    updated_by,
    deleted_at::timestamp as deleted_at
from sare_wallet.bill_payment_transactions