select
    id,
    bank_code,
    bank_name,
    created_at::timestamp as created_at,
    created_by,
    updated_at::timestamp as updated_at,
    updated_by,
    deleted_at::timestamp as deleted_at
from sare_wallet.banks