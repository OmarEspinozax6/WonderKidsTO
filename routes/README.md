# API de pacientes

La aplicacion expone un CRUD sobre `pacientes` usando el cliente oficial de Supabase:

- `GET /api/pacientes?limit=20&offset=0` lista pacientes.
- `GET /api/pacientes/<id>` obtiene un paciente.
- `POST /api/pacientes` crea un paciente.
- `PUT /api/pacientes/<id>` actualiza un paciente.
- `DELETE /api/pacientes/<id>` elimina un paciente.

Los cuerpos de `POST` y `PUT` deben incluir `nombre`, `dni`, `celular` (strings) y `asistencia` (booleano). Ejemplo: `{"nombre":"Ana","dni":"123","celular":"999","asistencia":true}`.

Para ejecutar localmente en PowerShell:

```powershell
\.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SUPABASE_URL = "https://tu-proyecto.supabase.co"
$env:SUPABASE_KEY = "tu-clave"
python app.py
python -m unittest discover -s tests
```

Una respuesta exitosa tiene la forma `{"ok":true,"data":...,"error":null}`. Los errores de validacion devuelven `400`, un paciente inexistente `404`, la falta de configuracion `503` y los errores del backend `400`.