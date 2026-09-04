"""Dashboard routes for the therapy center."""

from datetime import date

from flask import Blueprint, render_template

import extensions


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/dashboard")
def dashboard_page():
    """Render summary cards and today's agenda."""
    summary = {}
    agenda = []
    error = None
    if extensions.supabase is None:
        error = "Supabase no esta configurado."
    else:
        try:
            summary_response = extensions.supabase.table("v_resumen_dashboard").select("*").limit(1).execute()
            summary = (summary_response.data or [{}])[0]
            agenda_response = (
                extensions.supabase.table("v_agenda_pacientes")
                .select("*")
                .eq("fecha", date.today().isoformat())
                .order("hora_inicio")
                .execute()
            )
            agenda = agenda_response.data or []
        except Exception:
            error = "No se pudo cargar el resumen del dashboard."
    return render_template("dashboard.html", summary=summary, agenda=agenda, error=error)