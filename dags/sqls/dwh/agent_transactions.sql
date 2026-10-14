select
    atr.id,
    atr.agent_shop,
    atr.type,
    atr.amount::float as amount,
    atr.status,
    atr.agent_user_id,
    atr.location,
    atr.created_at::timestamp as created_at,
    atr.created_by,
    atr.updated_at::timestamp as updated_at,
    atr.updated_by
from sare_wallet.agent_transactions atr