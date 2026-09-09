-- Vistas compatibles con el modelo real de WonderKids.
-- Ejecutar despues de crear las tablas e insertar los datos iniciales.

create or replace view public.v_agenda_pacientes as
select
  e.id,
  (e.inicio_ts at time zone 'America/Lima')::date as fecha,
  (e.inicio_ts at time zone 'America/Lima')::time as hora_inicio,
  (e.fin_ts at time zone 'America/Lima')::time as hora_fin,
  e.titulo as tipo_sesion,
  e.estado,
  coalesce(f.estado, 'pendiente') as estado_pago,
  null::text as notas,
  p.id as paciente_id,
  concat_ws(' ', p.nombre, p.apellido) as paciente,
  t.nombre as padre_nombre,
  t.telefono as padre_telefono,
  e.trabajador_id as terapeuta_id,
  concat_ws(' ', w.nombre, w.apellido) as terapeuta,
  'Terapia'::text as especialidad
from public.eventos e
left join public.pacientes p on p.id = e.paciente_id
left join public.tutores t on t.id = p.tutor_id
left join public.trabajadores w on w.id = e.trabajador_id
left join lateral (
  select f.estado
  from public.facturas f
  where f.paciente_id = p.id
  order by f.creado_en desc
  limit 1
) f on true
where e.paciente_id is not null
   or exists (
     select 1
     from public.eventos_pacientes ep
     where ep.evento_id = e.id
   );

create or replace view public.v_resumen_dashboard as
select
  (select count(*) from public.pacientes where activo = true) as pacientes_activos,
  (select count(*) from public.trabajadores where activo = true) as terapeutas_activos,
  (select count(*) from public.eventos
   where (inicio_ts at time zone 'America/Lima')::date = (now() at time zone 'America/Lima')::date
     and estado <> 'cancelado') as citas_hoy,
  (select count(*) from public.registros_sesion_participante
   where asistencia = 'asistio'
     and (inicio_real_ts at time zone 'America/Lima')::date = (now() at time zone 'America/Lima')::date) as asistencias_hoy;

grant usage on schema public to anon, authenticated;
grant usage on schema public to service_role;
grant select on public.v_agenda_pacientes, public.v_resumen_dashboard to anon, authenticated, service_role;
grant select on public.pacientes, public.tutores, public.trabajadores, public.eventos,
  public.eventos_pacientes, public.facturas, public.registros_sesion_participante
to anon, authenticated, service_role;
grant insert, update, delete on public.pacientes, public.eventos
to anon, authenticated, service_role;