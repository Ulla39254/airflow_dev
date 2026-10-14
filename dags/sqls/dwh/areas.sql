select 
    id,
    name,
    region_id,
    warehouse_id,
    fleet_id,
    created_at::timestamp as created_at,
    created_by,
    updated_at::timestamp as updated_at,
    updated_by,
    deleted_at::timestamp as deleted_at,
    sub_region_id 
from sare_wallet.areas