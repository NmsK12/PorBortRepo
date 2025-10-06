# 🚀 Guía de Despliegue - Respaldodox Bot

## 📋 Preparación para Railway

### 1. Archivos del Proyecto
- ✅ `bot_requests.py` - Bot principal
- ✅ `start.py` - Script de inicio
- ✅ `requirements.txt` - Dependencias
- ✅ `Procfile` - Configuración de Railway
- ✅ `runtime.txt` - Versión de Python
- ✅ `railway.json` - Configuración de Railway
- ✅ `README.md` - Documentación
- ✅ `.gitignore` - Archivos a ignorar

### 2. Variables de Entorno Necesarias
```
BOT_TOKEN=7735457887:AAF-bzmviBfh5x1kuMe0IQaaP_Ij9VoBpxM
API_KEY_DNI=3378f24e438baad1797c5b
API_KEY_NOMBRES=9d2c423573b857e46235f9c50645f
API_URL_DNI=https://zgatoodni.up.railway.app/dniresult
API_URL_NOMBRES=https://zgatoonm.up.railway.app/nm
API_URL_TELEFONOS=http://161.132.51.34:1520/api/osipteldb
```

## 🔧 Pasos para Desplegar

### 1. Subir a GitHub
```bash
git add .
git commit -m "Respaldodox Bot v2.0 - Listo para Railway"
git push origin main
```

### 2. Conectar con Railway
1. Ve a [Railway.app](https://railway.app)
2. Conecta tu cuenta de GitHub
3. Selecciona el repositorio `PorBortRepo`
4. Railway detectará automáticamente los archivos de configuración

### 3. Configurar Variables de Entorno
En Railway Dashboard:
1. Ve a tu proyecto
2. Selecciona "Variables"
3. Agrega las variables de entorno listadas arriba

### 4. Desplegar
1. Railway iniciará el despliegue automáticamente
2. El bot se ejecutará con `python start.py`
3. Verifica los logs para confirmar que funciona

## 📱 Comandos del Bot

- `/start` - Mensaje de bienvenida
- `/dni 44443333` - Consulta por DNI
- `/nm Juan|Perez|Gonzalez` - Búsqueda por nombres
- `/telp 44443333` - Consulta telefónica
- `/cmds` - Menú interactivo

## 🔍 Verificación

1. Busca tu bot en Telegram
2. Envía `/start` para probar
3. Usa `/cmds` para ver el menú
4. Prueba los comandos de consulta

## 🛠️ Solución de Problemas

### Bot no responde
- Verifica que `BOT_TOKEN` esté configurado
- Revisa los logs en Railway Dashboard

### Errores de API
- Verifica que las claves de API estén correctas
- Revisa que las URLs de API sean accesibles

### Bot responde doble
- El problema está solucionado en la versión actual
- Si persiste, reinicia el servicio en Railway

---

🤖 **Respaldodox v2.0** - Listo para Railway
