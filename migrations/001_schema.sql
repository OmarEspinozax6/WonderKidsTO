-- WonderKidsTO: esquema inicial del centro de terapias.
-- ADVERTENCIA: este script elimina las tablas actuales para crear el modelo completo.

create extension if not exists pgcrypto;

drop view if exists public.v_agenda_pacientes cascade;
drop view if exists public.v_resumen_dashboard cascade;
drop table if exists public.documentos cascade;
drop table if exists public.asistencias cascade;
drop table if exists public.citas cascade;
drop table if exists public.pacientes cascade;
drop table if exists public.terapeutas cascade;

create table public.terapeutas (
    id uuid primary key default gen_random_uuid(),
    nombre text not null,
    especialidad text not null,
    celular text,
    email text,
    activo boolean not null default true,
    created_at timestamptz not null default now()
);

create table public.pacientes (
    id uuid primary key default gen_random_uuid(),
    nombre text not null,
    dni text not null unique,
    celular text not null,
    fecha_nacimiento date,
    contacto_familiar text,
    diagnostico text,
    observaciones text,
    activo boolean not null default true,
    created_at timestamptz not null default now()
);

create table public.citas (
    id uuid primary key default gen_random_uuid(),
    paciente_id uuid not null references public.pacientes(id) on delete cascade,
    terapeuta_id uuid not null references public.terapeutas(id),
    fecha date not null,
    hora_inicio time not null,
    hora_fin time not null,
    estado text not null default 'programada' check (estado in ('programada', 'confirmada', 'atendida', 'cancelada', 'no_asistio')),
    observaciones text,
    created_at timestamptz not null default now(),
    check (hora_fin > hora_inicio)
);

create table public.asistencias (
    id uuid primary key default gen_random_uuid(),
    cita_id uuid not null references public.citas(id) on delete cascade,
    paciente_id uuid not null references public.pacientes(id) on delete cascade,
    terapeuta_id uuid not null references public.terapeutas(id),
    fecha date not null,
    estado text not null check (estado in ('presente', 'tarde', 'ausente', 'justificada')),
    observaciones text,
    created_at timestamptz not null default now()
);

create table public.documentos (
    id uuid primary key default gen_random_uuid(),
    paciente_id uuid not null references public.pacientes(id) on delete cascade,
    nombre_archivo text not null,
    ruta_storage text not null,
    tipo_mime text,
    tamano bigint,
    descripcion text,
    created_at timestamptz not null default now()
);

create index idx_citas_fecha on public.citas(fecha);
create index idx_citas_paciente on public.citas(paciente_id);
create index idx_citas_terapeuta on public.citas(terapeuta_id);
create index idx_asistencias_fecha on public.asistencias(fecha);
create index idx_documentos_paciente on public.documentos(paciente_id);

create or replace view public.v_agenda_pacientes as
select
    c.id,
    c.fecha,
    c.hora_inicio,
    c.hora_fin,
    c.estado,
    c.observaciones,
    p.id as paciente_id,
    p.nombre as paciente,
    p.dni,
    t.id as terapeuta_id,
    t.nombre as terapeuta,
    t.especialidad
from public.citas c
join public.pacientes p on p.id = c.paciente_id
join public.terapeutas t on t.id = c.terapeuta_id;

create or replace view public.v_resumen_dashboard as
select
    (select count(*) from public.pacientes where activo) as pacientes_activos,
    (select count(*) from public.terapeutas where activo) as terapeutas_activos,
    (select count(*) from public.citas where fecha = current_date and estado not in ('cancelada')) as citas_hoy,
    (select count(*) from public.asistencias where fecha = current_date and estado = 'presente') as asistencias_hoy;

-- Bucket privado para archivos vinculados a pacientes.
insert into storage.buckets (id, name, public)
values ('documentos-pacientes', 'documentos-pacientes', false)
on conflict (id) do nothing;

-- Politicas iniciales para desarrollo con la anon key.
-- En produccion deben sustituirse por politicas basadas en auth.uid() y roles.
alter table public.pacientes enable row level security;
alter table public.terapeutas enable row level security;
alter table public.citas enable row level security;
alter table public.asistencias enable row level security;
alter table public.documentos enable row level security;

create policy "dev pacientes access" on public.pacientes for all to anon, authenticated using (true) with check (true);
create policy "dev terapeutas access" on public.terapeutas for all to anon, authenticated using (true) with check (true);
create policy "dev citas access" on public.citas for all to anon, authenticated using (true) with check (true);
create policy "dev asistencias access" on public.asistencias for all to anon, authenticated using (true) with check (true);
create policy "dev documentos access" on public.documentos for all to anon, authenticated using (true) with check (true);

drop policy if exists "dev storage access" on storage.objects;
create policy "dev storage access" on storage.objects for all to anon, authenticated
using (bucket_id = 'documentos-pacientes')
with check (bucket_id = 'documentos-pacientes');
