# API Consulta DNI (FastAPI)

## Requisitos
- Python 3.10+
- PowerShell (Windows)

## Instalación
1. Crear y activar entorno virtual:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:
```powershell
pip install -r requirements.txt
```

## Configuración
Crea un archivo `.env` en la raíz del proyecto con tus credenciales:

```
INTRA_USER=MRAMOS
INTRA_PASS=10162706
# Opcionalmente puedes sobreescribir endpoints y cabeceras
# LOGIN_URL=https://app.munitacna.gob.pe/intranet/login/login/index
# DNI_API_URL=https://app.munitacna.gob.pe/intranet/pide/reniecBuscar
# HTTP_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0
# HTTP_REFERER=https://app.munitacna.gob.pe/intranet/main
# HTTP_ORIGIN=https://app.munitacna.gob.pe
```

## Ejecutar servidor (local)
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Probar endpoints
- Documentación interactiva: `http://localhost:8000/docs`
- POST JSON:
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/consultar-dni" -ContentType 'application/json' -Body '{"dni":"12345678"}'
```
- GET con parámetro de ruta:
```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/consultar/dni/12345678"
```

## Despliegue en Railway
1. Asegúrate de tener una cuenta en Railway y el repositorio en GitHub.
2. En Railway, crea un nuevo proyecto y conéctalo a tu repositorio.
3. Railway detectará Python y el `Procfile`.
4. Configura variables de entorno en Railway (Settings → Variables):
   - `INTRA_USER`
   - `INTRA_PASS`
   - Opcionales: `LOGIN_URL`, `DNI_API_URL`, `HTTP_USER_AGENT`, `HTTP_REFERER`, `HTTP_ORIGIN`
5. Despliega. Railway expondrá una URL pública; prueba:
   - `GET https://<tu-app>.up.railway.app/consultar/dni/12345678`

### Notas para Railway
- El puerto se toma de la variable `PORT` proporcionada por Railway (via `Procfile`).
- Si necesitas forzar Python 3.10+, añade un archivo `runtime.txt` con `python-3.10.14`.
- Revisa logs en Railway para depurar login/consultas si algo falla.

## CI/CD con GitHub Actions → Railway
Este repo incluye `.github/workflows/deploy-railway.yml` para desplegar automáticamente en cada push a `main`.

Configura estos secretos en GitHub (Settings → Secrets and variables → Actions → New repository secret):
- `RAILWAY_TOKEN` (obligatorio): crea uno en Railway (Account → Tokens).
- `RAILWAY_SERVICE_NAME` (opcional): nombre exacto del Service (si tienes varios).
- `RAILWAY_PROJECT_ID` (opcional): ID del proyecto en Railway (para `railway link`).
- `RAILWAY_SERVICE_ID` (opcional): ID del service en Railway (para `railway link`).

El workflow hará:
1. Instalar Railway CLI
2. Si hay IDs, ejecuta `railway link --project <id>` y `--service <id>`
3. Desplegar con `railway up` (o `--service <name>` si definiste `RAILWAY_SERVICE_NAME`)
