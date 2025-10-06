import requests
import base64
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

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

def start_command(update, context):
    """Manejar comando /start"""
    welcome_message = """
🤖 **BOT DE RESPALDO DOX v2.0**

¡Hola! Soy **Respaldodox**, tu asistente para consultas de DNI.

📋 **Comandos disponibles:**
• `/dni {número}` - Consultar información de DNI
• `/cmds` - Ver todos los comandos disponibles

¡Estoy aquí para ayudarte! 🚀
    """
    
    update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

def dni_command(update, context):
    """Manejar comando /dni"""
    if not context.args:
        update.message.reply_text(
            "❌ **Error:** Debes proporcionar un número de DNI.\n\n"
            "📝 **Uso correcto:** `/dni 12345678`",
            parse_mode='Markdown'
        )
        return
    
    dni = context.args[0]
    
    # Validar que sea un número
    if not dni.isdigit() or len(dni) != 8:
        update.message.reply_text(
            "❌ **Error:** El DNI debe ser un número de 8 dígitos.\n\n"
            "📝 **Ejemplo:** `/dni 12345678`",
            parse_mode='Markdown'
        )
        return
    
    # Mostrar mensaje de carga
    loading_msg = update.message.reply_text(
        "🔍 **Consultando información del DNI...**\n"
        f"📄 DNI: `{dni}`\n"
        "⏳ Por favor espera...",
        parse_mode='Markdown'
    )
    
    try:
        # Consultar la API
        dni_data = consultar_dni(dni)
        
        if dni_data and dni_data.get('success'):
            # Formatear respuesta
            response = formatear_respuesta_dni(dni_data, dni)
            
            # Si hay foto en base64, enviarla
            if dni_data.get('photo_base64'):
                enviar_foto_dni(update, context, dni_data['photo_base64'], response)
            else:
                loading_msg.edit_text(response, parse_mode='Markdown')
        else:
            loading_msg.edit_text(
                f"❌ **No se encontró información** para el DNI: `{dni}`\n\n"
                "🔍 Verifica que el número sea correcto e intenta nuevamente.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error al consultar DNI {dni}: {e}")
        loading_msg.edit_text(
            f"❌ **Error al consultar** el DNI: `{dni}`\n\n"
            "🔄 Intenta nuevamente en unos momentos.",
            parse_mode='Markdown'
        )

def consultar_dni(dni):
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

def formatear_respuesta_dni(data, dni):
    """Formatear la respuesta de la API para mostrar"""
    response = f"""
✅ **INFORMACIÓN DEL DNI: {dni}**

📋 **Datos encontrados:**
"""
    
    # Obtener datos del campo 'data'
    if data.get('data'):
        for key, value in data['data'].items():
            if value:
                # Formatear nombres de campos
                field_name = key.replace('_', ' ').title()
                response += f"• **{field_name}:** {value}\n"
    
    response += "\n🤖 *Consulta realizada por Respaldodox*"
    return response

def enviar_foto_dni(update, context, foto_base64, texto):
    """Enviar foto del DNI si está disponible"""
    try:
        # Decodificar imagen base64
        if foto_base64.startswith('data:image'):
            # Remover el prefijo data:image/jpeg;base64,
            foto_base64 = foto_base64.split(',')[1]
        
        foto_bytes = base64.b64decode(foto_base64)
        
        # Enviar foto con caption
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=foto_bytes,
            caption=texto,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error al enviar foto: {e}")
        # Si falla la foto, enviar solo texto
        update.message.reply_text(texto, parse_mode='Markdown')

def cmds_command(update, context):
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
    
    update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def button_callback(update, context):
    """Manejar callbacks de botones"""
    query = update.callback_query
    query.answer()
    
    if query.data == "reniec_info":
        query.edit_message_text(
            "🔍 **RENIEC - Consulta de DNI**\n\n"
            "📝 **Uso del comando /dni:**\n"
            "• Escribe: `/dni 12345678`\n"
            "• Reemplaza `12345678` con el DNI que quieres consultar\n"
            "• El DNI debe tener exactamente 8 dígitos\n\n"
            "✅ **Ejemplo:** `/dni 44443333`\n\n"
            "🤖 *Respaldodox - Bot de respaldo*",
            parse_mode='Markdown'
        )

def handle_message(update, context):
    """Manejar mensajes de texto"""
    update.message.reply_text(
        "🤖 **Respaldodox** aquí!\n\n"
        "📝 Usa `/cmds` para ver todos los comandos disponibles.",
        parse_mode='Markdown'
    )

def main():
    """Función principal"""
    # Crear updater
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Agregar handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("dni", dni_command))
    dispatcher.add_handler(CommandHandler("cmds", cmds_command))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Iniciar bot
    logger.info("🤖 Iniciando Respaldodox...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
