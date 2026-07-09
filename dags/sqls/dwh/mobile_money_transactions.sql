select
  mmt.id,  -- uuid [primary key]
  mmt.mobile_money_provider,
  mmt.wallet_transaction_type,
  mmt.amount::float as amount,
  mmt.created_at::timestamp as created_at,
  u.first_name || ' ' || u.last_name as created_by,
  mmt.updated_at::timestamp as updated_at,
  u2.first_name || ' ' || u2.last_name as updated_by,
  mmt.deleted_at::timestamp as deleted_at
from sare_wallet.mobile_money_transactions mmt
join sare_wallet.users u on u.id = mmt.created_by
join sare_wallet.users u2 on u2.id = mmt.updated_by 