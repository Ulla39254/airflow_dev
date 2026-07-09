select 
  oah.id, -- uuid [primary key]
  oah.overdraft_account_id,  -- uuid [ref: > overdraft_accounts.id]
  oah.overdraft_limit::float,
  oah.opted_on::timestamp as opted_on,
  oah.opted_out::timestamp as opted_out,
  oah.active_status,
  oah.term_and_condition_id, -- uuid [ref: > terms_and_conditions.id]
  oah.created_at::timestamp as created_at,
  oah.created_by
from sare_wallet.overdraft_account_histories oah