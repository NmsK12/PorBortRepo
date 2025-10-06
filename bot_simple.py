import requests
import base64
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Configuración del bot
BOT_TOKEN = "7735457887:AAF-bzmviBfh5x1kuMe0IQaaP_Ij9VoBpxM"
API_BASE_URL = "https://zgatoodni.up.railway.app/dniresult"
API_KEY = "3378f24e438baad1797c5b"

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar comando /start"""
    welcome_message = """
🤖 **BOT DE RESPALDO DOX v2.0**

¡Hola! Soy **Respaldodox**, tu asistente para consultas de DNI.

📋 **Comandos disponibles:**
• `/dni {número}` - Consultar información de DNI
• `/cmds` - Ver todos los comandos disponibles

¡Estoy aquí para ayudarte! 🚀
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def dni_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar comando /dni"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Error:** Debes proporcionar un número de DNI.\n\n"
            "📝 **Uso correcto:** `/dni 12345678`",
            parse_mode='Markdown'
        )
        return
    
    dni = context.args[0]
    
    # Validar que sea un número
    if not dni.isdigit() or len(dni) != 8:
        await update.message.reply_text(
            "❌ **Error:** El DNI debe ser un número de 8 dígitos.\n\n"
            "📝 **Ejemplo:** `/dni 12345678`",
            parse_mode='Markdown'
        )
        return
    
    # Mostrar mensaje de carga
    loading_msg = await update.message.reply_text(
        "🔍 **Consultando información del DNI...**\n"
        f"📄 DNI: `{dni}`\n"
        "⏳ Por favor espera...",
        parse_mode='Markdown'
    )
    
    try:
        # Consultar la API
        dni_data = consultar_dni(dni)
        
        if dni_data:
            # Formatear respuesta
            response = formatear_respuesta_dni(dni_data, dni)
            
            # Si hay foto en base64, enviarla
            if dni_data.get('foto_base64'):
                await enviar_foto_dni(update, context, dni_data['foto_base64'], response)
            else:
                await loading_msg.edit_text(response, parse_mode='Markdown')
        else:
            await loading_msg.edit_text(
                f"❌ **No se encontró información** para el DNI: `{dni}`\n\n"
                "🔍 Verifica que el número sea correcto e intenta nuevamente.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error al consultar DNI {dni}: {e}")
        await loading_msg.edit_text(
            f"❌ **Error al consultar** el DNI: `{dni}`\n\n"
            "🔄 Intenta nuevamente en unos momentos.",
            parse_mode='Markdown'
        )

def consultar_dni(dni: str) -> dict:
    """Consultar información del DNI en la API"""
    url = f"{API_BASE_URL}?dni={dni}&key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logger.error(f"API error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error al consultar API: {e}")
        return None

def formatear_respuesta_dni(data: dict, dni: str) -> str:
    """Formatear la respuesta de la API para mostrar"""
    response = f"""
✅ **INFORMACIÓN DEL DNI: {dni}**

📋 **Datos encontrados:**
"""
    
    # Agregar campos disponibles
    for key, value in data.items():
        if key != 'foto_base64' and value:
            # Formatear nombres de campos
            field_name = key.replace('_', ' ').title()
            response += f"• **{field_name}:** {value}\n"
    
    response += "\n🤖 *Consulta realizada por Respaldodox*"
    return response

async def enviar_foto_dni(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                        foto_base64: str, texto: str):
    """Enviar foto del DNI si está disponible"""
    try:
        # Decodificar imagen base64
        foto_bytes = base64.b64decode(foto_base64)
        
        # Enviar foto con caption
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=foto_bytes,
            caption=texto,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error al enviar foto: {e}")
        # Si falla la foto, enviar solo texto
        await update.message.reply_text(texto, parse_mode='Markdown')

async def cmds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar comando /cmds"""
    keyboard = [
        [InlineKeyboardButton("🔍 RENIEC", callback_data="reniec_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = """
📋 **COMANDOS DE BOT DE RESPALDO**

🤖 **Respaldodox** - Tu asistente para consultas de DNI

**Comandos disponibles:**
• `/start` - Iniciar el bot
• `/dni {número}` - Consultar información de DNI
• `/cmds` - Ver este menú de comandos

**¿Cómo usar /dni?**
Simplemente escribe: `/dni 12345678`
    """
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar callbacks de botones"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "reniec_info":
        await query.edit_message_text(
            "🔍 **RENIEC - Consulta de DNI**\n\n"
            "📝 **Uso del comando /dni:**\n"
            "• Escribe: `/dni 12345678`\n"
            "• Reemplaza `12345678` con el DNI que quieres consultar\n"
            "• El DNI debe tener exactamente 8 dígitos\n\n"
            "✅ **Ejemplo:** `/dni 44443333`\n\n"
            "🤖 *Respaldodox - Bot de respaldo*",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar mensajes de texto"""
    await update.message.reply_text(
        "🤖 **Respaldodox** aquí!\n\n"
        "📝 Usa `/cmds` para ver todos los comandos disponibles.",
        parse_mode='Markdown'
    )

def main():
    """Función principal"""
    # Crear aplicación
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Agregar handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("dni", dni_command))
    app.add_handler(CommandHandler("cmds", cmds_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Iniciar bot
    logger.info("🤖 Iniciando Respaldodox...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
