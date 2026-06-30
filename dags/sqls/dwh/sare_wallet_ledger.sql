select 
    l.id,
    l.wallet_transaction_id,
    l.ledger_account_id,
    l.entry_type,
    l.amount::float,
    l.balance_before::float,
    l.balance_after::float,
    l.created_at::timestamp,
    l.created_by
from sare_wallet.ledger l