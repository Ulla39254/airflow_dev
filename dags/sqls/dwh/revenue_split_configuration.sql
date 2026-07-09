select
  rsc.id,  -- primary key
  rsc.transaction_type, 
  rsc.sare_split::float as sare_split,
  rsc.partner_split::float as partner_split,
  rsc.exercise_duty_split::float as exercise_duty_split,
  rsc.fee_percentage::float as fee_percentage,
  rsc.active_from::timestamp as active_from,
  rsc.active_to::timestamp as active_to,
  rsc.created_at::timestamp as created_at,
  rsc.created_by,
  rsc.updated_at::timestamp as updated_at,
  rsc.updated_by,
  rsc.deleted_at::timestamp as deleted_at,
  rsc.deleted_by,
from sare_wallet.revenue_split_configurations rsc