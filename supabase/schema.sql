-- Tabla → regla de acceso, para First Take (3.21)
-- Correr en Supabase: Project > SQL Editor > New query

create table if not exists redemptions (
  creador text primary key,
  datos jsonb not null,
  canjeado_en timestamptz not null default now()
);

alter table redemptions enable row level security;

-- Nadie entra con la publishable/anon key: solo la funcion de servidor
-- (api/verify-tag.py), que usa la service_role key y por eso salta RLS
-- de por si. Esta policy es un segundo seguro explicito.
create policy "solo service role" on redemptions
  for all
  using (auth.role() = 'service_role');
