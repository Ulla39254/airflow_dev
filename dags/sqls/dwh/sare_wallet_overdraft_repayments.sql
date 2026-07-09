select
    ovr.id,
    ovr.reference,
    ovr.overdraft_draw_id,
    ovr.active_overdraft_rollover,
    ovr.wallet_transaction,
    ovr.guarantor_lien_id,
    ovr.principal_amount::float as principal_amount,
    ovr.fee_amount::float as fee_amount,
    ovr.excise_duty_amount::float as excise_duty_amount,
    ovr.total_amount_paid::float as total_amount_paid,
    ovr.total_amount_due::float as total_amount_due,
    ovr.status,
    ovr.created_at::timestamp as created_at,
    ovr.created_by,
    ovr.updated_at::timestamp as updated_at,
    ovr.updated_by

from sare_wallet.overdraft_repayments ovr