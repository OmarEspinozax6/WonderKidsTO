import os
from flask import Flask
from supabase import create_client, Client

app = Flask(__name__)

url = "https://znxhmovobemhpebzzkrp.supabase.co"
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Ruta principal
@app.route("/")
def inicio():
    pacientes = supabase.table("pacientes").select("nombre, celular").limit(1).execute()
    paciente = pacientes.data[0] if pacientes.data else {"nombre": "Sin datos", "celular": "N/A"}

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
    supabase.table("pacientes").insert({
        "nombre": "María López",
        "dni": "87654321",
        "celular": "988888888",
        "asistencia": True
    }).execute()
    return "Paciente registrado en Supabase"

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(debug=True)
