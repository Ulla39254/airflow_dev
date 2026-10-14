select
    id,
    wallet_id,
    name,
    address,
    certificate_number,
    kra_pin,
    kin_full_name,
    kin_mobile_number,
    created_at::timestamp as created_at,
    created_by,
    updated_at::timestamp as updated_at,
    updated_by,
    deleted_at::timestamp as deleted_at,
    industry,
    specify_industry,
    kin_relationship
from sare_wallet.business_profiles