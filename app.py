import os
from flask import Flask, jsonify
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

# Ruta principal
@app.route("/")
def inicio():
    if not supabase:
        return supabase_unavailable()
    try:
        pacientes = supabase.table("pacientes").select("nombre, celular").limit(1).execute()
        paciente = pacientes.data[0] if pacientes.data else {"nombre": "Sin datos", "celular": "N/A"}
    except Exception:
        app.logger.exception("Error consultando pacientes en la ruta principal.")
        return jsonify({"ok": False, "data": None, "error": "Error interno consultando pacientes."}), 500

    return f"""
    <html>
        <head>
            <title>Centro de Terapias</title>
        </head>
        <body>
            <h1>Centro de Terapias</h1>
            <h2>Paciente registrado</h2>
            <p>Nombre: {paciente['nombre']}</p>
            <p>Celular: {paciente['celular']}</p>
        </body>
    </html>
    """

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
