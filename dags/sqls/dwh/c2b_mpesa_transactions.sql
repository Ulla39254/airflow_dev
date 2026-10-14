select 
    id,
    transaction_type,
    transaction_id,
    transaction_time::timestamp as transaction_time,
    transaction_amount::float as transaction_amount,
    business_short_code,
    bill_reference_number,
    invoice_number,
    org_account_balance::float as org_account_balance,
    third_party_transaction_id,
    msisdn,
    first_name,
    middle_name,
    last_name,
    created_at::timestamp as created_at
from sare_wallet.c2b_mpesa_transactions