"""HTTP routes for the pacientes CRUD and its small browser UI."""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from services import pacientes_service


pacientes_bp = Blueprint("pacientes", __name__)


def _status(result: dict, success_status: int = 200) -> int:
    """Map a service result to the API HTTP status."""
    if result["ok"]:
        return success_status
    if result["error"] == "Supabase no esta configurado.":
        return 503
    if result["error"] == "Paciente no encontrado.":
        return 404
    return 400


def _json_result(result: dict, success_status: int = 200):
    """Serialize a service result and its appropriate HTTP status."""
    return jsonify(result), _status(result, success_status)


@pacientes_bp.get("/api/pacientes")
def api_list_pacientes():
    """Return the paginated patient list."""
    try:
        limit = int(request.args["limit"]) if "limit" in request.args else None
        offset = int(request.args.get("offset", 0))
        if limit is not None and limit < 1 or offset < 0:
            raise ValueError
    except ValueError:
        return jsonify({"ok": False, "data": None, "error": "limit/offset deben ser enteros validos."}), 400
    return _json_result(pacientes_service.list_pacientes(limit, offset))


@pacientes_bp.get("/api/pacientes/<id>")
def api_get_paciente(id):
    """Return one patient."""
    return _json_result(pacientes_service.get_paciente(id))


@pacientes_bp.post("/api/pacientes")
def api_create_paciente():
    """Create a patient from a JSON body."""
    return _json_result(pacientes_service.create_paciente(request.get_json(silent=True)), 201)


@pacientes_bp.put("/api/pacientes/<id>")
def api_update_paciente(id):
    """Update a patient from a JSON body."""
    return _json_result(pacientes_service.update_paciente(id, request.get_json(silent=True)))


@pacientes_bp.delete("/api/pacientes/<id>")
def api_delete_paciente(id):
    """Delete one patient."""
    return _json_result(pacientes_service.delete_paciente(id))


@pacientes_bp.get("/pacientes")
def pacientes_list_page():
    """Render the patient list page."""
    result = pacientes_service.list_pacientes()
    return render_template("pacientes/list.html", pacientes=result["data"] or [], error=result["error"])


@pacientes_bp.get("/pacientes/nuevo")
def paciente_new_page():
    """Render the create form."""
    return render_template("pacientes/form.html", paciente=None)


@pacientes_bp.get("/pacientes/<id>/editar")
def paciente_edit_page(id):
    """Render the edit form, or redirect when the patient does not exist."""
    result = pacientes_service.get_paciente(id)
    if not result["ok"]:
        flash(result["error"], "error")
        return redirect(url_for("pacientes.pacientes_list_page"))
    return render_template("pacientes/form.html", paciente=result["data"])