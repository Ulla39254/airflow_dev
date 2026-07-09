select
  og.id, --uuid [primary key]
  og.overdraft_account_id,  --uuid [ref: > overdraft_accounts.id]
  og.guarantor_wallet_id,  --uuid [ref: > wallets.id]
  og.active_status,
  og.effective_from::timestamp as effective_from,
  og.effective_to::timestamp as effective_to,
  og.term_and_condition_id, --uuid [ref: > terms_and_conditions.id]
  og.created_at::timestamp as created_at,
  og.updated_at::timestamp as updated_at,
  og.created_by,
  og.updated_by
  
from sare_wallet.overdraft_guarantors og