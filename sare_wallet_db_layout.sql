Table users {
  id uuid [primary key]
  firstname varchar
  lastname varchar
  email varchar [unique]
  phonenumber varchar [unique]
  identification_number varchar [unique]
  shofco_id varchar
  password_hash text
  wallet_pin_hash TEXT
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table users_kyc {
  id uuid [primary key]
  user_id uuid [ref: > users.id, null]
  id_number varchar
  verification_status enum('PENDING', 'VERIFIED', 'REJECTED')
  verified_at timestamp
  rejection_reason text
  accepted_terms_and_conditions boolean
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table devices {
  id uuid [primary key]
  client_device_id uuid [unique, not null]
  device_type varchar(20) [not null]
  operating_system varchar(50) [not null]
  operating_system_version varchar(20)
  app_version varchar(20)
  model varchar(50)
  compromise_flags varchar(50)[]
  is_revoked boolean [default: false]
  revoked_reason text
  revoked_at timestamp
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table user_devices {
  id uuid [primary key]
  user_id uuid [not null, ref: > users.id]
  device_id uuid [not null, ref: > devices.id]
  is_active boolean [default: true]
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  indexes {
    (user_id, device_id) [unique]
    user_id
  }
}

Table user_device_histories {
  id uuid [primary key]
  user_device_id uuid [not null, ref: > user_devices.id]
  last_used_at timestamp
  created_at timestamp
  updated_at timestamp
}
// Immutable history — no soft-delete fields

Table audit_logs {
  id uuid [primary key]
  user_device_id uuid [not null, ref: > user_devices.id]
  ip_address inet [not null]
  location point
  action varchar(255)
  status enum('SUCCESS', 'FAILED')
  failure_reason text
  metadata jsonb
  created_at timestamp
}
// Immutable audit trail — no update or delete fields

Table auth_token_sessions {
  id uuid [primary key]
  user_device_id uuid [not null, ref: > user_devices.id]
  refresh_token_hash text [not null]
  expires_at timestamp [not null]
  revoked boolean [default: false]
  revoked_at timestamp
  revoked_status enum('ACTIVE', 'REVOKED', 'EXPIRED')
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}
// Sessions are not deleted; they expire or are revoked

Table shops {
  id uuid [primary key]
  name varchar
  shop_type enum('NORMAL', 'SARE')
  default_sap_code varchar
  address varchar
  longitude varchar
  latitude varchar
  registration_cert varchar
  kra_pin varchar
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table wallets {
  id uuid [primary key]
  external_id uuid
  type enum('PERSONAL', 'PERSONAL_BUSINESS', 'BUSINESS', 'OVERDRAFT', 'PLATFORM', 'AGGREGATOR_KCB')
  user_id uuid [ref: > users.id, null]
  shop_id uuid [ref: > shops.id, null]
  balance decimal
  status enum('ACTIVE', 'INACTIVE', 'BLACKLISTED')
  business_number varchar
  daily_transaction_limit decimal
  wallet_limit uuid [ref: > wallet_limits.id, null]
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
  indexes {
    (user_id, type) [unique]
    (shop_id, type) [unique]
    (status)
  }
}

Table wallet_limits {
  id uuid [pk]
  wallet_type enum('PERSONAL', 'PERSONAL_BUSINESS', 'BUSINESS')
  previous_limit decimal
  new_limit decimal
  effective_from timestamp
  effective_to timestamp
  reason text
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table mobile_money_transactions {
  id uuid [primary key]
  provider enum('MPESA', 'AIRTEL', 'T-KASH')
  transaction_code varchar [unique]
  account_number varchar
  type enum('DEPOSIT', 'WITHDRAWAL')
  amount decimal(18,2)
  status enum('PENDING', 'SUCCESS', 'FAILED', 'REVERSED')
  metadata jsonb
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table bank_transactions {
  id uuid [primary key]
  bank_name varchar
  account_number varchar
  transaction_reference varchar [unique]
  type enum('DEPOSIT', 'WITHDRAWAL')
  amount decimal(18,2)
  status enum('PENDING', 'SUCCESS', 'FAILED', 'REVERSED')
  metadata jsonb
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table agent_transactions {
  id uuid [primary key]
  agent_shop uuid [ref: > shops.id]
  type enum('CASH_IN', 'CASH_OUT')
  amount decimal(18,2)
  status enum('PENDING', 'SUCCESS', 'FAILED', 'REVERSED')
  agent_user_id varchar
  location varchar
  metadata jsonb
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table wallet_transactions {
  id uuid [primary key]
  reference varchar [unique]
  source_wallet uuid [ref: > wallets.id]
  destination_wallet uuid [ref: > wallets.id]
  mobile_money_transaction uuid [ref: > mobile_money_transactions.id]
  bank_transaction uuid [ref: > bank_transactions.id]
  agent_transaction uuid [ref: > agent_transactions.id]
  type enum(
    'DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'BILL_PAYMENT',
    'OVERDRAFT_ISSUE', 'OVERDRAFT_REPAYMENT', 'REVERSAL'
  )
  channel_type enum('P2P', 'P2PB', 'P2B', 'B2P', 'PB2P', 'MOMO', 'AGENT', 'BANK')
  uses_overdraft boolean
  overdraft_amount decimal(18,2)
  amount decimal(18,2)
  transaction_fee decimal(18,2)
  external_reference varchar
  metadata jsonb
  transaction_status enum('PENDING', 'SUCCESS', 'FAILED')
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}
// Transactions are never deleted — no soft-delete fields

Table revenue_split_configurations {
  id uuid [pk]
  transaction_type enum('OVERDRAFT', 'WITHDRAWAL', 'DEPOSIT', 'LOAN')
  sare_split decimal
  partner_split decimal
  exercise_duty_split decimal
  fee_percentage decimal(18,2)
  active_from timestamp
  active_to timestamp
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table ledger {
  id uuid [primary key]
  wallet_transaction_id uuid [ref: > wallet_transactions.id]
  ledger_account_id uuid [ref: > ledger_accounts.id]
  entry_type enum('DEBIT', 'CREDIT')
  amount decimal(18,2)
  balance_before decimal(18,2)
  balance_after decimal(18,2)
  created_at timestamp
  created_by uuid
}
// Immutable double-entry ledger — no updates or deletes ever

Table bill_providers {
  id uuid [primary key]
  name varchar(100)
  category enum('ELECTRICITY', 'WATER', 'INTERNET', 'GOVERNMENT', 'OTHER')
  paybill_number varchar(20)
  logo_url varchar(255)
  account_type varchar('Meter No', 'Account No')
  short_description text
  is_active boolean
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table bill_accounts {
  id uuid [primary key]
  wallet uuid [ref: > wallets.id]
  bill_provider uuid [ref: > bill_providers.id]
  paybill_number varchar(20)
  account_number varchar(50)
  nickname varchar(50)
  default_amount decimal(18,2)
  is_favorite boolean
  is_active boolean
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table bill_payments {
  id uuid [primary key]
  wallet_transaction_id uuid [ref: > wallet_transactions.id]
  bill_account_id uuid [ref: > bill_accounts.id, null]
  payment_status enum('PENDING', 'SUCCESS', 'FAILED', 'REVERSED')
  amount decimal(18,2)
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table overdraft_accounts {
  id uuid [primary key]
  wallet_id uuid [ref: > wallets.id, unique]
  overdraft_limit decimal(18,2)
  overdraft_used decimal(18,2)
  cooling_off_until timestamp
  cooling_off_reason enum('GUARANTOR_RECOVERY', 'POST_WRITEOFF_RECOVERY')
  opted_on timestamp
  opted_out timestamp
  is_delinquent boolean
  delinquent_since timestamp
  active_status enum('ACTIVE', 'OPTED_OUT', 'WRITE_OFF', 'SUSPENDED')
  term_and_condition_id uuid [ref: > terms_and_conditions.id]
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table overdraft_account_histories {
  id uuid [primary key]
  overdraft_account_id uuid [ref: > overdraft_accounts.id]
  overdraft_limit decimal(18,2)
  opted_on timestamp
  opted_out timestamp
  active_status enum('ACTIVE', 'OPTED_OUT', 'WRITE_OFF', 'SUSPENDED')
  term_and_condition_id uuid [ref: > terms_and_conditions.id]
  created_at timestamp
  created_by uuid
}
// Immutable history snapshots — no updates or deletes

Table overdraft_guarantors{
  id uuid [primary key]
  overdraft_account_id uuid [ref: > overdraft_accounts.id]
  guarantor_wallet_id uuid [ref: > wallets.id]
  active_status enum('PENDING', 'ACCEPTED', 'DECLINED', 'REVOKED')
  effective_from timestamp
  effective_to timestamp
  term_and_condition_id uuid [ref: > terms_and_conditions.id]
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table terms_and_conditions {
  id uuid [primary key]
  url text
  title varchar
  version number
  status enum('DRAFT', 'ACTIVE', 'DEPRECATED')
  product enum('OVERDRAFT', 'PERSONAL_WALLET', 'BUSINESS_WALLET')
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table overdraft_draws {
  id uuid [primary key]
  reference varchar [unique]
  overdraft_account_id uuid [ref: > overdraft_accounts.id]
  overdraft_guarantor_id uuid [ref: > overdraft_guarantors.id, null]
  wallet_transaction uuid [ref: > wallet_transactions.id, null]
  principal_amount decimal(18,2)
  fee_amount decimal(18,2)
  excise_duty_amount decimal(18,2)
  total_amount_paid decimal(18,2)
  total_amount_due decimal(18,2)
  due_date timestamp
  payment_status enum('PENDING', 'PARTIALLY_PAID', 'PAID')
  overdraft_status enum(
    'INITIAL', 'DELINQUENCY', 'PARTNER_RECOVERY',
    'GUARANTOR_LIEN', 'GUARANTOR_RECOVERY', 'WRITTEN_OFF'
  )
  written_off_date timestamp
  written_off_reason text
  delinquent_from timestamp
  delinqunet_to timestamp
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table overdraft_repayments {
  id uuid [primary key]
  reference varchar [unique]
  overdraft_draw_id uuid [ref: > overdraft_draws.id]
  active_overdraft_rollover uuid [ref: > overdraft_rollovers.id]
  wallet_transaction uuid [ref: > wallet_transactions.id, null]
  guarantor_lien_id uuid [ref: > overdraft_guarantor_liens.id, null]
  principal_amount decimal(18,2)
  fee_amount decimal(18,2)
  excise_duty_amount decimal(18,2)
  total_amount_paid decimal(18,2)
  total_amount_due decimal(18,2)
  status enum('PENDING', 'SUCCESS', 'FAILED')
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table overdraft_rollovers {
  id uuid [primary key]
  overdraft_draw_id uuid [ref: > overdraft_draws.id]
  revenue_split_configuration_id uuid [ref: > revenue_split_configurations.id]
  principal_amount decimal(18,2)
  fee_amount decimal(18,2)
  excise_duty_amount decimal(18,2)
  total_amount_due decimal(18,2)
  status enum('SCHEDULED', 'PROCESSED')
  payment_status enum('PENDING', 'PARTIALLY_PAID', 'PAID')
  due_date timestamp
  rollover_stage enum('R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6')
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table overdraft_guarantor_liens {
  id uuid [primary key]
  amount_locked decimal(18,2)
  overdraft_draw_id uuid [ref: > overdraft_draws.id]
  guarantor_id uuid [ref: > overdraft_guarantors.id, null]
  active_status enum('ACTIVE', 'CLOSED')
  lien_closed_date timestamp
  executed_at timestamp
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table ledger_accounts {
  id uuid [primary key]
  code varchar(100) [unique]
  name varchar(150)
  account_category enum('ASSET', 'LIABILITY', 'REVENUE', 'EXPENSE', 'EQUITY')
  normal_balance enum('DEBIT', 'CREDIT')
  wallet_id uuid [ref: > wallets.id, null]
  currency varchar(3) [default: 'KES']
  status enum('ACTIVE', 'INACTIVE')
  created_at timestamp
  updated_at timestamp
}

Table reversal_requests {
  id uuid [primary key]
  original_wallet_transaction_id uuid [ref: > wallet_transactions.id]
  reversed_wallet_transaction_id uuid [ref: > wallet_transactions.id]
  initiator_type enum('USER', 'ADMIN')
  reversal_type enum('SYSTEM_ERROR', 'USER_ERROR')
  reversal_reason text
  rejection_reason text
  status enum('PENDING', 'APPROVED', 'REJECTED', 'REVERSED')
  created_at timestamp
  updated_at timestamp
  processed_at timestamp
  created_by uuid
  updated_by uuid
}

Table module_notification_providers {
  id int [primary key]
  module_name enum('FINTECH', 'E-COMMERCE')
  channel enum('SMS', 'EMAIL', 'PUSH')
  primary_provider_id int [ref: > notification_providers.id]
  backup_provider_id int [ref: > notification_providers.id]
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
}

Table notification_providers {
  id int [primary key]
  name varchar
  channel enum('SMS', 'EMAIL', 'PUSH')
  provider varchar
  sender_id varchar
  active boolean
  is_healthy boolean
  metadata jsonb
  last_success_at timestamp
  consecutive_failures int
  default boolean
  created_at timestamp
  updated_at timestamp
  created_by uuid
  updated_by uuid
  deleted_at timestamp
  deleted_by uuid
}

Table notification_outbox {
  id int [primary key]
  channel enum('SMS', 'EMAIL', 'PUSH')
  module_name varchar
  entity_type varchar
  entity_id int
  provider_id int [ref: > notification_providers.id]
  delivery_status enum('PENDING', 'SENT', 'FAILED')
  retry_count int
  max_retries int
  sent_at timestamp
  last_retry_at timestamp
  error_message text
  created_at timestamp
  updated_at timestamp
}
// Outbox records are operational logs — no soft-delete

Table sms_outbox {
  id int [primary key]
  notification_id int [ref: > notification_outbox.id]
  recipient_phone varchar
  sender_id varchar
  message_body text
  delivery_status enum('PENDING', 'SENT', 'FAILED')
  response_code varchar
  response_message text
  channel_payload jsonb
  sent_at timestamp
  created_at timestamp
  updated_at timestamp
}

Table email_outbox {
  id int [primary key]
  notification_id int [ref: > notification_outbox.id]
  recipient_email varchar
  subject varchar
  body text
  attachments jsonb
  delivery_status enum('PENDING', 'SENT', 'FAILED')
  response_code varchar
  response_message text
  channel_payload jsonb
  sent_at timestamp
  created_at timestamp
  updated_at timestamp
}

Table push_outbox {
  id int [primary key]
  notification_id int [ref: > notification_outbox.id]
  recipient_device_token varchar
  title varchar
  body text
  data_payload jsonb
  delivery_status enum('PENDING', 'SENT', 'FAILED')
  response_code varchar
  response_message text
  channel_payload jsonb
  sent_at timestamp
  created_at timestamp
  updated_at timestamp
}