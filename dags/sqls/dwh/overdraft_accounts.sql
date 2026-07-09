select
  oa.id, -- uuid [primary key]
  oa.wallet_id,   --uuid [ref: > wallets.id, unique]
  oa.overdraft_limit::float as overdraft_limit,
  oa.overdraft_used::float as overdraft_used,
  oa.cooling_off_until::timestamp as cooling_off_until,
  oa.cooling_off_reason,
  oa.opted_on::timestamp as opted_on,
  oa.opted_out::timestamp as opted_out,
  oa.is_delinquent,
  oa.delinquent_since::timestamp as delinquent_since,
  oa.active_status,
  oa.term_and_condition_id,  -- uuid [ref: > terms_and_conditions.id]
  oa.created_at::timestamp as created_at,
  oa.created_by,
  oa.updated_at::timestamp as updated_at,  
  oa.updated_by, 
  oa.deleted_at::timestamp as deleted_at,
  oa.deleted_by 
from sare_wallet.overdraft_accounts oa