import os
from flask import Flask, jsonify, redirect, url_for
from supabase import create_client, Client

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
    except Exception:
        app.logger.exception("No se pudo crear el cliente de Supabase.")


def supabase_unavailable():
    """Return the standard response when Supabase is not configured."""
    return jsonify({"ok": False, "data": None, "error": "Supabase no esta configurado."}), 503

@app.route("/")
def inicio():
    """Abrir la pantalla principal del CRUD de pacientes."""
    return redirect(url_for("pacientes.pacientes_list_page"))

# Ruta para insertar un paciente
@app.route("/registrar")
def registrar():
    if not supabase:
        return supabase_unavailable()
    try:
        supabase.table("pacientes").insert({
            "nombre": "María López",
            "dni": "87654321",
            "celular": "988888888",
            "asistencia": True
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

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(debug=True)
