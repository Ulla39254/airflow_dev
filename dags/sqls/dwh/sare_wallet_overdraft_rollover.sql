select
  ro.id,
  ro.overdraft_draw_id, --ref:overdraft_draws.id
  ro.revenue_split_configuration_id, --ref:revenue_split_configurations.id
  ro.principal_amount::float as principal_amount,
  ro.fee_amount::float as fee_amount,
  ro.excise_duty_amount::float as excise_duty_amount,
  ro.total_amount_due::float as total_amount_due,
  ro.status,
  ro.payment_status,
  ro.due_date::timestamp as due_date,
  ro.rollover_stage,
  ro.created_at::timestamp as created_at,
  ro.created_by,
  ro.updated_at::timestamp as updated_at,
  ro.updated_by
  
from sare_wallet.overdraft_rollovers ro