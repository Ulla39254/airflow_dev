select 
    u.id,
    u.first_name || ' ' || u.last_name as name,
    u.email,
    u.phone::text,
    u.identification_number::text,
    u.shofco_id::text,
    u.user_type,
    u.organization,
    u.wallet_status,
    u.created_at::timestamp,
    u.updated_at::timestamp,
    u.created_by,
    u.updated_by,
    u.deleted_at::timestamp

from sare_wallet.users u