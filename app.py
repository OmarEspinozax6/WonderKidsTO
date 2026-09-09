import os
from pathlib import Path
from flask import Flask, jsonify, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client, Client

import extensions

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# La aplicacion puede arrancar sin credenciales para mostrar un error 503 claro.
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client | None = None
if not url or not key:
    app.logger.warning("Supabase no esta configurado: faltan SUPABASE_URL o SUPABASE_KEY.")
else:
    try:
        supabase = create_client(url, key)
        extensions.supabase = supabase
        app.logger.info("Cliente Supabase configurado para %s", url)
    except Exception:
        app.logger.exception("No se pudo crear el cliente de Supabase.")


def supabase_unavailable():
    """Return the standard response when Supabase is not configured."""
    return jsonify({"ok": False, "data": None, "error": "Supabase no esta configurado."}), 503


@app.get("/api/diagnostico-supabase")
def diagnostico_supabase():
    """Check configuration and the dashboard view without exposing credentials."""
    if supabase is None:
        return jsonify({"ok": False, "configured": False, "error": "SUPABASE_URL o SUPABASE_KEY no estan configuradas."}), 503
    try:
        response = supabase.table("v_resumen_dashboard").select("*").limit(1).execute()
        return jsonify({"ok": True, "configured": True, "url": url, "data": response.data or []})
    except Exception as exc:
        app.logger.exception("Diagnostico Supabase fallido: %s", exc)
        return jsonify({"ok": False, "configured": True, "url": url, "error": str(exc)}), 502

@app.route("/")
def inicio():
    """Abrir el dashboard del centro de terapias."""
    return redirect(url_for("dashboard.dashboard_page"))

# Ruta para insertar un paciente
@app.route("/registrar")
def registrar():
    if not supabase:
        return supabase_unavailable()
    try:
        supabase.table("pacientes").insert({
            "nombre": "María López",
            "dni": "87654321",
            "celular": "988888888"
        }).execute()
        return "Paciente registrado en Supabase", 201
    except Exception:
        app.logger.exception("Error registrando paciente en Supabase.")
        return jsonify({"ok": False, "data": None, "error": "Error interno registrando paciente."}), 500


# Importar y registrar antes de iniciar el servidor evita rutas ausentes.
try:
    from routes.pacientes_routes import pacientes_bp
except ImportError:
    app.logger.exception("No se pudo importar el blueprint de pacientes.")
else:
    app.register_blueprint(pacientes_bp)

try:
    from routes.dashboard_routes import dashboard_bp
except ImportError:
    app.logger.exception("No se pudo importar el blueprint del dashboard.")
else:
    app.register_blueprint(dashboard_bp)

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(debug=True)
