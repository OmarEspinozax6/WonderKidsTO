"""Dashboard routes for the therapy center."""

from datetime import date

from flask import Blueprint, jsonify, render_template, request

import extensions


dashboard_bp = Blueprint("dashboard", __name__)


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
            agenda_query = extensions.supabase.table("v_agenda_pacientes").select("*").eq("fecha", selected["fecha"])
            for key in ("terapeuta", "paciente", "padre", "especialidad"):
                if selected[key]:
                    agenda_query = agenda_query.ilike(key, f"%{selected[key]}%")
            agenda_response = agenda_query.order("hora_inicio").execute()
            agenda = agenda_response.data or []
            terapeutas = extensions.supabase.table("terapeutas").select("id,nombre,especialidad").eq("activo", True).order("nombre").execute().data or []
            pacientes = extensions.supabase.table("pacientes").select("id,nombre,padre_nombre").eq("activo", True).order("nombre").execute().data or []
        except Exception:
            error = "No se pudo cargar el resumen del dashboard."
    return render_template("dashboard.html", summary=summary, agenda=agenda, terapeutas=terapeutas, pacientes=pacientes, selected=selected, error=error)


@dashboard_bp.patch("/api/sesiones/<id>")
def update_session(id):
    """Reschedule, cancel, or update payment status for one session."""
    if extensions.supabase is None:
        return jsonify({"ok": False, "error": "Supabase no esta configurado."}), 503
    data = request.get_json(silent=True) or {}
    allowed = {"fecha", "hora_inicio", "hora_fin", "estado", "estado_pago", "notas"}
    changes = {key: value for key, value in data.items() if key in allowed}
    if not changes:
        return jsonify({"ok": False, "error": "No hay cambios validos."}), 400
    try:
        response = extensions.supabase.table("sesiones").update(changes).eq("id", id).execute()
        if not response.data:
            return jsonify({"ok": False, "error": "Sesion no encontrada."}), 404
        return jsonify({"ok": True, "data": response.data[0], "error": None})
    except Exception:
        return jsonify({"ok": False, "error": "No se pudo actualizar la sesion."}), 400