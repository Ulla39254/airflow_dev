select
    id,
    wallet_id,
    bill_provider_id,
    business_number,
    account_number,
    nickname,
    default_amount::float as default_amount,
    is_favorite,
    is_active,
    payment_method,
    created_at::timestamp as created_at,
    created_by,
    updated_at::timestamp as updated_at,
    updated_by,
    deleted_at::timestamp as deleted_at
from sare_wallet.bill_accounts 