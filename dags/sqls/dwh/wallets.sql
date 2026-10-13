select 
    w.id,  --uuid [primary key]
    w.type,
    w.user_id,
    w.balance::float as balance,
    w.wallet_active_status,
    w.created_at::timestamp as created_at,
    w.created_by,
    w.updated_at::timestamp as updated_at,
    w.updated_by,
    w.deleted_at::timestamp as deleted_at,
    w.deleted_by,
    w.external_id,
    w.business_number,
    w.daily_transaction_limit::float as daily_transaction_limit,
    w.wallet_limit::float as wallet_limit
from sare_wallet.wallets w
