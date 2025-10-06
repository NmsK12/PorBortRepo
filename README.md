# 🤖 Respaldodox - Bot de Telegram

Bot de Telegram para consultas de DNI, nombres y teléfonos utilizando APIs de RENIEC.

## 🚀 Características

- ✅ **Comando `/dni`** - Consultar información de DNI con foto
- ✅ **Comando `/nm`** - Búsqueda por nombres y apellidos
- ✅ **Comando `/telp`** - Consultas telefónicas por DNI o teléfono
- ✅ **Comando `/cmds`** - Menú interactivo con botones
- ✅ **Sistema anti-spam** - 8 segundos entre consultas
- ✅ **Validación estricta** - DNI (8 dígitos), Teléfono (9 dígitos)
- ✅ **Respuestas organizadas** - Formato profesional con emojis
- ✅ **Archivos TXT** - Para resultados extensos

## 📱 Comandos Disponibles

### `/start`
Muestra el mensaje de bienvenida del bot.

### `/dni {número}`
Consulta información de un DNI específico.
- **Ejemplo:** `/dni 44443333`
- **Requisito:** El DNI debe tener exactamente 8 dígitos

### `/nm {nombres|apellidos}`
Busca personas por nombres y apellidos.
- **Ejemplo:** `/nm Juan|Perez|Gonzalez`
- **Múltiples nombres:** `/nm Maria,Jose|Lopez|Martinez`

### `/telp {número}`
Consulta información telefónica.
- **DNI:** `/telp 44443333` (8 dígitos)
- **Teléfono:** `/telp 987654321` (9 dígitos)

### `/cmds`
Muestra el menú de comandos con botones interactivos.

## 🛠️ APIs Utilizadas

- **RENIEC DNI:** `https://zgatoodni.up.railway.app/dniresult`
- **Nombres:** `https://zgatoonm.up.railway.app/nm`
- **Teléfonos:** `http://161.132.51.34:1520/api/osipteldb`

## 🚀 Despliegue en Railway

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/NmsK12/PorBortRepo.git
   cd PorBortRepo
   ```

2. **Instala dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura variables de entorno:**
   - `BOT_TOKEN`: Token del bot de Telegram
   - `API_KEY_DNI`: Clave para API de DNI
   - `API_KEY_NOMBRES`: Clave para API de nombres
   - `API_KEY_TELEFONOS`: Clave para API de teléfonos

4. **Ejecuta el bot:**
   ```bash
   python bot_requests.py
   ```

## 📦 Dependencias

- `requests==2.31.0`
- `python-telegram-bot==20.8`

## 🔧 Configuración

El bot está configurado para funcionar con:
- **Python 3.11+**
- **Railway** para despliegue
- **APIs externas** para consultas

## 📝 Notas

- El bot maneja automáticamente los errores de las APIs
- Los mensajes incluyen emojis para mejor experiencia de usuario
- Soporte completo para fotos en formato base64
- Interfaz responsive con botones interactivos
- Sistema anti-spam para evitar abuso

---

🤖 **Respaldodox v2.0** - Bot de respaldo para consultas de DNI