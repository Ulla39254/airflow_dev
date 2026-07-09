select
  wt.id,   --uuid [primary key]
  wt.reference,
  wt.source_wallet_id,     --uuid [ref: > wallets.id]
  wt.destination_wallet_id,    --uuid [ref: > wallets.id]
  wt.mobile_money_transaction_id,    --uuid [ref: > mobile_money_transactions.id]
  wt.payment_method,
  wt.amount::float as amount,
  wt.balance_before::float as balance_before,
  wt.balance_after::float as balance_after,
  wt.wallet_transaction_status,
  wt.created_at::timestamp as created_at,
  u.first_name as created_by,
  wt.updated_at::timestamp as updated_at,
  u2.first_name as updated_by,
  wt.deleted_at::timestamp as deleted_at

from sare_wallet.wallet_transactions wt
join sare_wallet.users u on u.id = wt.created_by
join sare_wallet.users u2 on u2.id = wt.updated_by