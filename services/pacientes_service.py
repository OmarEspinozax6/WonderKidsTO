"""Operations for the pacientes table in Supabase."""

from typing import Any

from app import supabase


REQUIRED_FIELDS = ("nombre", "dni", "celular", "asistencia")


def _validate_data(data: Any) -> str | None:
    """Return a validation message, or None when patient data is valid."""
    if not isinstance(data, dict):
        return "El cuerpo debe ser un objeto JSON."
    for field in REQUIRED_FIELDS:
        if field not in data:
            return f"El campo '{field}' es obligatorio."
    for field in ("nombre", "dni", "celular"):
        if not isinstance(data[field], str) or not data[field].strip():
            return f"El campo '{field}' debe ser un string no vacio."
    if not isinstance(data["asistencia"], bool):
        return "El campo 'asistencia' debe ser booleano."
    return None


def _result(data: Any = None, error: str | None = None) -> dict:
    """Build the common service response shape."""
    return {"ok": error is None, "data": data, "error": error}


def list_pacientes(limit: int | None = None, offset: int = 0) -> dict:
    """List patients, optionally applying a limit and offset."""
    if supabase is None:
        return _result(error="Supabase no esta configurado.")
    try:
        query = supabase.table("pacientes").select("*")
        if offset:
            query = query.range(offset, offset + (limit or 1000) - 1)
        elif limit is not None:
            query = query.limit(limit)
        response = query.execute()
        return _result(data=response.data or [])
    except Exception as exc:
        return _result(error=str(exc))


def get_paciente(id: str) -> dict:
    """Get one patient by its identifier."""
    if supabase is None:
        return _result(error="Supabase no esta configurado.")
    try:
        response = supabase.table("pacientes").select("*").eq("id", id).limit(1).execute()
        data = response.data or []
        return _result(data=data[0] if data else None, error=None if data else "Paciente no encontrado.")
    except Exception as exc:
        return _result(error=str(exc))


def create_paciente(data: dict) -> dict:
    """Validate and create a patient."""
    validation_error = _validate_data(data)
    if validation_error:
        return _result(error=validation_error)
    if supabase is None:
        return _result(error="Supabase no esta configurado.")
    try:
        response = supabase.table("pacientes").insert(data).execute()
        return _result(data=(response.data or [None])[0])
    except Exception as exc:
        return _result(error=str(exc))


def update_paciente(id: str, data: dict) -> dict:
    """Validate and update a patient by its identifier."""
    validation_error = _validate_data(data)
    if validation_error:
        return _result(error=validation_error)
    if supabase is None:
        return _result(error="Supabase no esta configurado.")
    try:
        response = supabase.table("pacientes").update(data).eq("id", id).execute()
        return _result(data=(response.data or [None])[0], error=None if response.data else "Paciente no encontrado.")
    except Exception as exc:
        return _result(error=str(exc))


def delete_paciente(id: str) -> dict:
    """Delete a patient by its identifier."""
    if supabase is None:
        return _result(error="Supabase no esta configurado.")
    try:
        response = supabase.table("pacientes").delete().eq("id", id).execute()
        return _result(data=(response.data or [None])[0], error=None if response.data else "Paciente no encontrado.")
    except Exception as exc:
        return _result(error=str(exc))