create role academia_f01_app nologin nosuperuser nocreatedb nocreaterole noinherit noreplication nobypassrls;
grant usage on schema academia_private to academia_f01_app;
grant select, insert, update on academia_private.f01_sessions to academia_f01_app;
grant select, insert, delete on academia_private.f01_tokens to academia_f01_app;
create policy f01_app_sessions on academia_private.f01_sessions for all to academia_f01_app using (true) with check (true);
create policy f01_app_tokens on academia_private.f01_tokens for all to academia_f01_app using (true) with check (true);
