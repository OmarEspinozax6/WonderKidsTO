"""Dashboard routes for the therapy center."""

from datetime import date, timedelta

from flask import Blueprint, current_app, jsonify, render_template, request

import extensions


dashboard_bp = Blueprint("dashboard", __name__)


def _agenda_query(start_date: str, end_date: str, filters: dict):
    query = extensions.supabase.table("v_agenda_pacientes").select("*").gte("fecha", start_date).lte("fecha", end_date)
    view_filter_names = {"terapeuta": "terapeuta", "paciente": "paciente", "padre": "padre_nombre", "especialidad": "especialidad"}
    for key, column in view_filter_names.items():
        if filters.get(key):
            query = query.ilike(column, f"%{filters[key]}%")
    return query.order("fecha").order("hora_inicio").limit(1000)


@dashboard_bp.get("/dashboard")
def dashboard_page():
    """Render the visual agenda, keeping filters in the URL."""
    summary = {}
    agenda = []
    terapeutas = []
    pacientes = []
    error = None
    selected = {
        "fecha": request.args.get("fecha", date.today().isoformat()),
        "vista": request.args.get("vista", "dia"),
        "terapeuta": request.args.get("terapeuta", ""),
        "paciente": request.args.get("paciente", ""),
        "padre": request.args.get("padre", ""),
        "especialidad": request.args.get("especialidad", ""),
    }
    if extensions.supabase is None:
        error = "Supabase no esta configurado."
    else:
        try:
            summary_response = extensions.supabase.table("v_resumen_dashboard").select("*").limit(1).execute()
            summary = (summary_response.data or [{}])[0]
            selected_date = date.fromisoformat(selected["fecha"])
            if selected["vista"] == "semana":
                start_date = selected_date - timedelta(days=selected_date.weekday())
                end_date = start_date + timedelta(days=6)
            elif selected["vista"] == "mes":
                start_date = selected_date.replace(day=1)
                next_month = start_date.replace(day=28) + timedelta(days=4)
                end_date = next_month.replace(day=1) - timedelta(days=1)
            else:
                start_date = end_date = selected_date
            agenda_response = _agenda_query(start_date.isoformat(), end_date.isoformat(), selected).execute()
            agenda = agenda_response.data or []
            terapeutas_data = extensions.supabase.table("trabajadores").select("id,nombre,apellido").eq("activo", True).order("nombre").execute().data or []
            terapeutas = [
                {"id": item["id"], "nombre": f'{item.get("nombre", "")} {item.get("apellido", "")}'.strip(), "especialidad": "Terapia"}
                for item in terapeutas_data
            ]
            pacientes_data = extensions.supabase.table("pacientes").select("id,nombre,apellido,tutor_id").eq("activo", True).order("nombre").execute().data or []
            pacientes = [
                {"id": item["id"], "nombre": f'{item.get("nombre", "")} {item.get("apellido", "")}'.strip()}
                for item in pacientes_data
            ]
        except Exception as exc:
            current_app.logger.exception("Error cargando dashboard desde Supabase: %s", exc)
            error = "No se pudo cargar el resumen del dashboard."
    return render_template("dashboard.html", summary=summary, agenda=agenda, terapeutas=terapeutas, pacientes=pacientes, selected=selected, error=error)


@dashboard_bp.get("/api/agenda")
def agenda_data():
    """Return sessions for FullCalendar without reloading the page."""
    if extensions.supabase is None:
        return jsonify({"ok": False, "data": [], "error": "Supabase no esta configurado."}), 503
    try:
        start = request.args.get("start", date.today().isoformat())[:10]
        end = request.args.get("end", start)[:10]
        filters = {key: request.args.get(key, "") for key in ("terapeuta", "paciente", "padre", "especialidad")}
        response = _agenda_query(start, end, filters).execute()
        return jsonify({"ok": True, "data": response.data or [], "error": None})
    except Exception as exc:
        current_app.logger.exception("Error cargando agenda: %s", exc)
        return jsonify({"ok": False, "data": [], "error": "No se pudo cargar la agenda."}), 502


@dashboard_bp.patch("/api/sesiones/<id>")
def update_session(id):
    """Reschedule, cancel, or update payment status for one session."""
    if extensions.supabase is None:
        return jsonify({"ok": False, "error": "Supabase no esta configurado."}), 503
    data = request.get_json(silent=True) or {}
    allowed = {"fecha", "hora_inicio", "hora_fin", "estado"}
    changes = {key: value for key, value in data.items() if key in allowed}
    if not changes:
        return jsonify({"ok": False, "error": "No hay cambios validos."}), 400
    try:
        event_changes = {"estado": changes["estado"]} if "estado" in changes else {}
        if "fecha" in changes and "hora_inicio" in changes:
            event_changes["inicio_ts"] = f'{changes["fecha"]}T{changes["hora_inicio"]}:00-05:00'
        if "fecha" in changes and "hora_fin" in changes:
            event_changes["fin_ts"] = f'{changes["fecha"]}T{changes["hora_fin"]}:00-05:00'
        response = extensions.supabase.table("eventos").update(event_changes).eq("id", id).execute()
        if not response.data:
            return jsonify({"ok": False, "error": "Sesion no encontrada."}), 404
        return jsonify({"ok": True, "data": response.data[0], "error": None})
    except Exception:
        return jsonify({"ok": False, "error": "No se pudo actualizar la sesion."}), 400