select
    la.id,
    la.code,
    la.name,
    la.account_category,
    la.normal_balance,
    la.wallet_id,
    la.currency,
    la.status,
    la.created_at::timestamp as created_at,
    la.updated_at::timestamp as updated_at

from sare_wallet.ledger_accounts la