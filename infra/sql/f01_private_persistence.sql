create schema academia_private;
revoke all on schema academia_private from public, anon, authenticated, service_role;
create table academia_private.f01_sessions (
 learner text primary key check (char_length(learner) between 1 and 128),
 payload text not null check (jsonb_typeof(payload::jsonb) = 'object')
);
create table academia_private.f01_tokens (
 digest text primary key check (digest ~ '^[0-9a-f]{64}$'),
 learner text not null unique check (learner ~ '^[0-9a-f]{32}$'),
 expires bigint not null check (expires > 0)
);
create index f01_tokens_expires_idx on academia_private.f01_tokens(expires);
alter table academia_private.f01_sessions enable row level security;
alter table academia_private.f01_tokens enable row level security;
revoke all on all tables in schema academia_private from public, anon, authenticated, service_role;
