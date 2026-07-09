select
  od.id,
  od.reference,
  od.overdraft_account_id, --uuid [ref: > overdraft_accounts.id]
  od.overdraft_guarantor_id,      --uuid [ref: > overdraft_guarantors.id, null]
  od.wallet_transaction, --uuid[ref: > wallet_transactions.id, null]
  od.principal_amount::float as principal_amount,
  od.fee_amount::float,
  od.excise_duty_amount::float,
  od.total_amount_paid::float,
  od.total_amount_due::float,
  od.due_date::timestamp as due_date,
  od.payment_status,
  od.overdraft_status,
  od.written_off_date::timestamp as written_off_date,
  od.written_off_reason::text as written_off_reason,
  od.delinquent_from::timestamp as delinquent_from,
  od.delinqunet_to::timestamp as delinqunet_to,
  od.created_at::timestamp as created_at,
  od.updated_at::timestamp as updated_at,
  od.created_by,
  od.updated_by
from sare_wallet.overdraft_draws od
