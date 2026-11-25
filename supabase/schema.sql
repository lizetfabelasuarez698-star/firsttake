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

-- Perfiles de usuario para public/cuenta.html (ya existe en el proyecto;
-- se documenta aqui para que el repo refleje la base real).
create table if not exists perfiles (
  id uuid primary key references auth.users (id) on delete cascade,
  nombre text not null,
  creado_en timestamptz not null default now()
);

alter table perfiles enable row level security;

-- La pagina usa la publishable key (publica). Lo que protege los datos es
-- esto: cada persona solo ve, crea y edita SU fila.
create policy "ver mi perfil" on perfiles for select to authenticated
  using ((select auth.uid()) = id);
create policy "crear mi perfil" on perfiles for insert to authenticated
  with check ((select auth.uid()) = id);
create policy "editar mi perfil" on perfiles for update to authenticated
  using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
