select 
    w.id,  --uuid [primary key]
    w.type,
    w.user_id,
    w.balance::float as balance,
    w.wallet_active_status,
    u.first_name || ' ' || u.last_name as created_by,
    w.created_at::timestamp as created_at,
    w.updated_at::timestamp as updated_at,
    u2.first_name || ' ' || u2.last_name as updated_by,
    w.deleted_at::timestamp as deleted_at,
    u3.first_name || ' ' || u3.last_name as deleted_by,
    w.external_id,
    w.daily_transaction_limit::float as daily_transaction_limit,
    w.wallet_limit::float as wallet_limit
from sare_wallet.wallets w
join sare_wallet.users u on w.created_by = u.id
left join sare_wallet.users u2 on w.updated_by = u2.id
left join sare_wallet.users u3 on w.deleted_by = u3.id