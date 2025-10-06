import requests
import json
import time
import logging
import threading
from queue import Queue
import base64
from threading import Thread
import os

# Configuración del bot
BOT_TOKEN = "7735457887:AAF-bzmviBfh5x1kuMe0IQaaP_Ij9VoBpxM"
API_BASE_URL = "https://zgatoodni.up.railway.app/dniresult"
API_KEY = "3378f24e438baad1797c5b"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Diccionario para controlar spam (user_id: timestamp)
user_cooldowns = {}

# Sistema de cola para consultas
consulta_queue = Queue()
consulta_processing = False
consulta_thread = None

class RespaldoDoxBot:
    def __init__(self):
        self.last_update_id = 0
        self.running = True
        self.start_consulta_processor()
        
        # Configuración de seguridad
        self.ADMIN_ID = 6862902399  # Tu ID de administrador
        self.ALLOWED_GROUPS = [
            "respaldochoco",
            "𝑮𝑹𝑼𝑷𝑶 𝑽𝑰𝑷 𝒁𝑮𝑨𝑻𝑶𝑶 2.0",
            "ᴄʜᴏᴄᴏ GRP",
            "CHOCO VIP"
        ]
        self.AUTHORIZED_USERS = set()  # Usuarios autorizados para privado
    
    def escape_html(self, text):
        """Escapar caracteres especiales para HTML"""
        if not text:
            return ""
        # Escapar caracteres HTML
        text = str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return text
    
    def is_admin(self, user_id):
        """Verificar si el usuario es administrador"""
        return user_id == self.ADMIN_ID
    
    def is_group_allowed(self, chat_title):
        """Verificar si el grupo está permitido"""
        if not chat_title:
            return False
        return chat_title in self.ALLOWED_GROUPS
    
    def is_user_authorized(self, user_id):
        """Verificar si el usuario está autorizado para privado"""
        return user_id in self.AUTHORIZED_USERS
    
    def can_use_bot(self, chat_type, chat_title, user_id):
        """Verificar si se puede usar el bot en este contexto"""
        # Si es grupo, verificar si está en la lista permitida
        if chat_type == "group" or chat_type == "supergroup":
            return self.is_group_allowed(chat_title)
        
        # Si es privado, verificar si el usuario está autorizado
        elif chat_type == "private":
            return self.is_user_authorized(user_id)
        
        return False
    
    def handle_adduser_command(self, chat_id, user_id, user_info, username):
        """Manejar comando /adduser"""
        if not self.is_admin(user_id):
            self.send_message(chat_id, "❌ <b>Acceso denegado.</b>\n\nSolo el administrador puede usar este comando.", include_image=True)
            return
        
        if not username:
            self.send_message(chat_id, "❌ <b>Uso incorrecto:</b>\n\n<code>/adduser @usuario</code>\n\nEjemplo: <code>/adduser @juan123</code>", include_image=True)
            return
        
        # Remover @ si está presente
        username = username.replace('@', '')
        
        # Agregar usuario a la lista de autorizados
        self.AUTHORIZED_USERS.add(username)
        
        self.send_message(chat_id, f"✅ <b>Usuario autorizado</b>\n\n👤 <b>Usuario:</b> @{username}\n🔓 <b>Estado:</b> Autorizado para privado\n\n🤖 <i>Acción realizada por: {self.get_user_display_name(user_info)}</i>", include_image=True)
    
    def handle_unuser_command(self, chat_id, user_id, user_info, username):
        """Manejar comando /unuser"""
        if not self.is_admin(user_id):
            self.send_message(chat_id, "❌ <b>Acceso denegado.</b>\n\nSolo el administrador puede usar este comando.", include_image=True)
            return
        
        if not username:
            self.send_message(chat_id, "❌ <b>Uso incorrecto:</b>\n\n<code>/unuser @usuario</code>\n\nEjemplo: <code>/unuser @juan123</code>", include_image=True)
            return
        
        # Remover @ si está presente
        username = username.replace('@', '')
        
        # Remover usuario de la lista de autorizados
        if username in self.AUTHORIZED_USERS:
            self.AUTHORIZED_USERS.remove(username)
            self.send_message(chat_id, f"❌ <b>Usuario desautorizado</b>\n\n👤 <b>Usuario:</b> @{username}\n🔒 <b>Estado:</b> Sin acceso a privado\n\n🤖 <i>Acción realizada por: {self.get_user_display_name(user_info)}</i>", include_image=True)
        else:
            self.send_message(chat_id, f"⚠️ <b>Usuario no encontrado</b>\n\n👤 <b>Usuario:</b> @{username}\n❌ <b>Estado:</b> No estaba autorizado\n\n🤖 <i>Acción realizada por: {self.get_user_display_name(user_info)}</i>", include_image=True)
    
    def send_access_denied_message(self, chat_id, chat_type, chat_title):
        """Enviar mensaje de acceso denegado"""
        if chat_type == "private":
            message = "❌ <b>Bot no disponible en privado</b>\n\n"
            message += "🔒 <b>Este bot solo funciona en grupos autorizados.</b>\n\n"
            message += "📞 <b>Para usarlo en un grupo, contacta a:</b>\n"
            message += "• @zGatoO\n"
            message += "• @WinniePoohOFC\n"
            message += "• @choco_tete\n\n"
            message += "🤖 <i>Respaldodox v2.0</i>"
        else:
            message = "❌ <b>Bot no autorizado para este grupo</b>\n\n"
            message += f"🏷️ <b>Grupo:</b> {self.escape_html(chat_title or 'Sin nombre')}\n"
            message += "🔒 <b>Este bot solo funciona en grupos autorizados.</b>\n\n"
            message += "📞 <b>Para autorización, contacta a:</b>\n"
            message += "• @zGatoO\n"
            message += "• @WinniePoohOFC\n"
            message += "• @choco_tete\n\n"
            message += "🤖 <i>Respaldodox v2.0</i>"
        
        self.send_message(chat_id, message, include_image=True)
    
    def start_consulta_processor(self):
        """Iniciar el procesador de consultas en cola"""
        global consulta_processing, consulta_thread
        if not consulta_processing:
            consulta_processing = True
            consulta_thread = threading.Thread(target=self.process_consulta_queue, daemon=True)
            consulta_thread.start()
            logger.info("🔄 Procesador de consultas iniciado")
    
    def process_consulta_queue(self):
        """Procesar consultas en cola"""
        while consulta_processing:
            try:
                if not consulta_queue.empty():
                    consulta = consulta_queue.get()
                    self.execute_consulta(consulta)
                    consulta_queue.task_done()
                else:
                    time.sleep(0.5)  # Esperar 500ms antes de verificar nuevamente
            except Exception as e:
                logger.error(f"Error procesando consulta: {e}")
                time.sleep(1)
    
    def execute_consulta(self, consulta):
        """Ejecutar una consulta específica"""
        try:
            tipo = consulta['tipo']
            chat_id = consulta['chat_id']
            user_id = consulta['user_id']
            user_info = consulta['user_info']
            parametros = consulta['parametros']
            loading_msg = consulta['loading_msg']
            
            logger.info(f"Ejecutando consulta tipo: {tipo} para usuario: {user_id}")
            
            if tipo == 'dni':
                self.execute_dni_consulta(chat_id, user_id, user_info, parametros['dni'], loading_msg)
            elif tipo == 'nombres':
                self.execute_nombres_consulta(chat_id, user_id, user_info, parametros['nombres'], loading_msg)
            elif tipo == 'telefono':
                self.execute_telefono_consulta(chat_id, user_id, user_info, parametros['numero'], loading_msg)
            elif tipo == 'arbol':
                self.execute_arbol_consulta(chat_id, user_id, user_info, parametros['dni'], loading_msg)
            else:
                logger.error(f"Tipo de consulta desconocido: {tipo}")
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
    def send_message(self, chat_id, text, reply_markup=None, include_image=True):
        """Enviar mensaje a Telegram"""
        logger.info(f"send_message llamado: chat_id={chat_id}, include_image={include_image}, is_dni_response={self.is_dni_response(text)}")
        # Si debe incluir imagen y no es una respuesta de DNI, enviar con foto
        if include_image and not self.is_dni_response(text):
            logger.info("Enviando mensaje con imagen")
            return self.send_message_with_image(chat_id, text, reply_markup)
        
        # Envío normal sin imagen
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return None
    
    def is_dni_response(self, text):
        """Verificar si es una respuesta del comando DNI"""
        return "RENIEC ONLINE" in text or "DNI ➾" in text
    
    def send_message_with_image(self, chat_id, text, reply_markup=None):
        """Enviar mensaje con imagen adjunta"""
        try:
            # Leer la imagen
            with open('imagen.jpg', 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': text,
                    'parse_mode': 'HTML'
                }
                
                if reply_markup:
                    data['reply_markup'] = json.dumps(reply_markup)
                
                url = f"{TELEGRAM_API_URL}/sendPhoto"
                response = requests.post(url, files=files, data=data)
                return response.json()
        except FileNotFoundError:
            logger.error("Archivo imagen.jpg no encontrado, enviando mensaje sin imagen")
            return self.send_message(chat_id, text, reply_markup, include_image=False)
        except Exception as e:
            logger.error(f"Error enviando mensaje con imagen: {e}")
            return self.send_message(chat_id, text, reply_markup, include_image=False)
    
    def send_photo(self, chat_id, photo_bytes, caption=None):
        """Enviar foto a Telegram"""
        url = f"{TELEGRAM_API_URL}/sendPhoto"
        files = {'photo': ('dni_photo.jpg', photo_bytes, 'image/jpeg')}
        data = {'chat_id': chat_id}
        if caption:
            data['caption'] = caption
            data['parse_mode'] = 'Markdown'
        
        try:
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error enviando foto: {e}")
            return None
    
    def edit_message(self, chat_id, message_id, text, include_image=True):
        """Editar mensaje existente"""
        # Si debe incluir imagen y no es una respuesta de DNI, enviar nueva foto
        if include_image and not self.is_dni_response(text):
            # Eliminar mensaje anterior y enviar nuevo con imagen
            self.delete_message(chat_id, message_id)
            return self.send_message_with_image(chat_id, text)
        
        # Edición normal sin imagen
        url = f"{TELEGRAM_API_URL}/editMessageText"
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error editando mensaje: {e}")
            return None
    
    def edit_message_with_keyboard(self, chat_id, message_id, text, keyboard, include_image=True):
        """Editar mensaje existente con teclado"""
        # Si debe incluir imagen y no es una respuesta de DNI, enviar nueva foto
        if include_image and not self.is_dni_response(text):
            # Eliminar mensaje anterior y enviar nuevo con imagen
            self.delete_message(chat_id, message_id)
            return self.send_message_with_image(chat_id, text, keyboard)
        
        # Edición normal sin imagen
        url = f"{TELEGRAM_API_URL}/editMessageText"
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'Markdown',
            'reply_markup': json.dumps(keyboard)
        }
        
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error editando mensaje con teclado: {e}")
            return None
    
    def delete_message(self, chat_id, message_id):
        """Eliminar mensaje"""
        url = f"{TELEGRAM_API_URL}/deleteMessage"
        data = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error eliminando mensaje: {e}")
            return None
    
    def get_updates(self):
        """Obtener actualizaciones de Telegram"""
        url = f"{TELEGRAM_API_URL}/getUpdates"
        params = {
            'offset': self.last_update_id + 1,
            'timeout': 30
        }
        
        try:
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo updates: {e}")
            return None
    
    def consultar_dni(self, dni):
        """Consultar información del DNI en la API"""
        url = f"{API_BASE_URL}?dni={dni}&key={API_KEY}"
        
        try:
            logger.info(f"Consultando API DNI: {url}")
            response = requests.get(url, timeout=10)
            logger.info(f"Respuesta API DNI - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Datos recibidos de API DNI: {data}")
                return data
            else:
                logger.error(f"API DNI error: {response.status_code}")
                logger.error(f"Respuesta completa: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error al consultar API DNI: {e}")
            return None
    
    def formatear_respuesta_dni(self, data, dni, user_display):
        """Formatear la respuesta de la API para mostrar"""
        if not data.get('data'):
            return f"❌ **El DNI {dni} no se encontró en el sistema RENIEC**\n\n🔍 Verifica que el número sea correcto e intenta nuevamente.\n\n🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
        
        data_info = data['data']
        
        response = f"""
**[RESPALDODOX-CHOCO] RENIEC ONLINE**

🆔 **DNI ➾ {data_info.get('DNI', dni)}**
👤 **NOMBRES ➾ {data_info.get('NOMBRES', 'N/A')}**
👥 **APELLIDOS ➾ {data_info.get('APELLIDOS', 'N/A')}**
⚧ **GÉNERO ➾ {data_info.get('GENERO', 'N/A')}**
🎂 **EDAD ➾ {data_info.get('EDAD', 'N/A')}**
💍 **ESTADO CIVIL ➾ {data_info.get('ESTADO_CIVIL', 'N/A')}**
⚠️ **RESTRICCIÓN ➾ {data_info.get('RESTRICCION', 'N/A')}**

📅 **FECHA NACIMIENTO ➾ {data_info.get('FECHA_NACIMIENTO', 'N/A')}**
👨 **PADRE ➾ {data_info.get('PADRE', 'N/A')}**
👩 **MADRE ➾ {data_info.get('MADRE', 'N/A')}**

📝 **FECHA INSCRIPCIÓN ➾ {data_info.get('FECHA_INSCRIPCION', 'N/A')}**
📄 **FECHA EMISIÓN ➾ {data_info.get('FECHA_EMISION', 'N/A')}**
⏰ **FECHA CADUCIDAD ➾ {data_info.get('FECHA_CADUCIDAD', 'N/A')}**
🎓 **NIVEL EDUCATIVO ➾ {data_info.get('NIVEL_EDUCATIVO', 'N/A')}**
📏 **ESTATURA ➾ {data_info.get('ESTATURA', 'N/A')}**
❤️ **DONANTE ÓRGANOS ➾ {data_info.get('DONANTE_ORGANOS', 'N/A')}**

🏠 **DIRECCIÓN ➾ {data_info.get('DIRECCION', 'N/A')}**
🏘️ **DISTRITO ➾ {data_info.get('DISTRITO', 'N/A')}**
🏛️ **PROVINCIA ➾ {data_info.get('PROVINCIA', 'N/A')}**
🌍 **DEPARTAMENTO ➾ {data_info.get('DEPARTAMENTO', 'N/A')}**

🔢 **UBIGEO RENIEC ➾ {data_info.get('UBIGEO_RENIEC', 'N/A')}**
🔢 **UBIGEO INEI ➾ {data_info.get('UBIGEO_INE', 'N/A')}**
🔢 **UBIGEO SUNAT ➾ {data_info.get('UBIGEO_SUNAT', 'N/A')}**

🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>
"""
        return response
    
    def handle_start_command(self, chat_id):
        """Manejar comando /start"""
        welcome_message = """
🤖 **BOT DE RESPALDO DOX v2.0**

¡Hola! Soy **Respaldodox**, tu asistente para consultas de DNI.

📋 **Comandos disponibles:**
• `/dni {número}` - Consultar información de DNI
• `/nm {nombres|apellidos}` - Buscar por nombres
• `/telp {número}` - Consultar teléfonos por DNI o teléfono
• `/arg {dni}` - Consultar árbol genealógico
• `/cmds` - Ver todos los comandos disponibles

¡Estoy aquí para ayudarte! 🚀
        """
        
        self.send_message(chat_id, welcome_message)
    
    def handle_dni_command(self, chat_id, user_id, user_info, dni):
        """Manejar comando /dni"""
        # Verificar cooldown (8 segundos)
        current_time = time.time()
        if user_id in user_cooldowns:
            time_left = 8 - (current_time - user_cooldowns[user_id])
            if time_left > 0:
                self.send_message(
                    chat_id,
                    f"⏰ **Espera {int(time_left)} segundos** antes de hacer otra consulta.\n\n"
                    "🛡️ *Sistema anti-spam activo*"
                )
                return
        
        # Actualizar cooldown
        user_cooldowns[user_id] = current_time
        
        # Validar que sea un número
        if not dni.isdigit() or len(dni) != 8:
            self.send_message(
                chat_id,
                "❌ **Error:** El DNI debe ser un número de 8 dígitos.\n\n"
                "📝 **Ejemplo:** `/dni 12345678`"
            )
            return
        
        # Mostrar mensaje de carga inmediatamente
        loading_msg = self.send_message(
            chat_id,
            f"🔍 **Consultando información del DNI...**\n"
            f"📄 DNI: `{dni}`\n"
            "⏳ Tu consulta está en cola, por favor espera..."
        )
        
        # Agregar a la cola de consultas
        consulta = {
            'tipo': 'dni',
            'chat_id': chat_id,
            'user_id': user_id,
            'user_info': user_info,
            'parametros': {'dni': dni},
            'loading_msg': loading_msg
        }
        consulta_queue.put(consulta)
        logger.info(f"Consulta DNI agregada a la cola para usuario {user_id}")
    
    def execute_dni_consulta(self, chat_id, user_id, user_info, dni, loading_msg):
        """Ejecutar consulta DNI en la cola"""
        try:
            # Obtener nombre de usuario para mostrar
            user_display = self.get_user_display_name(user_info)
            
            # Consultar la API
            dni_data = self.consultar_dni(dni)
            
            if dni_data and dni_data.get('success'):
                # Formatear respuesta
                response = self.formatear_respuesta_dni(dni_data, dni, user_display)
                
                # Si hay foto, enviarla primero
                if dni_data.get('photo_base64'):
                    try:
                        # Decodificar imagen base64
                        photo_data = dni_data['photo_base64']
                        if photo_data.startswith('data:image'):
                            photo_data = photo_data.split(',')[1]
                        
                        photo_bytes = base64.b64decode(photo_data)
                        
                        # Enviar foto con caption
                        self.send_photo(chat_id, photo_bytes, response)
                        
                        # Eliminar mensaje de carga
                        if loading_msg and 'result' in loading_msg:
                            message_id = loading_msg['result']['message_id']
                            self.delete_message(chat_id, message_id)
                    except Exception as e:
                        logger.error(f"Error enviando foto: {e}")
                        # Si falla la foto, enviar solo texto
                        if loading_msg and 'result' in loading_msg:
                            message_id = loading_msg['result']['message_id']
                            self.edit_message(chat_id, message_id, response, include_image=False)
                else:
                    # Sin foto, solo texto
                    if loading_msg and 'result' in loading_msg:
                        message_id = loading_msg['result']['message_id']
                        self.edit_message(chat_id, message_id, response, include_image=False)
            else:
                if loading_msg and 'result' in loading_msg:
                    message_id = loading_msg['result']['message_id']
                    self.edit_message(
                        chat_id, message_id,
                        f"❌ **No se encontró información** para el DNI: `{dni}`\n\n"
                        "🔍 Verifica que el número sea correcto e intenta nuevamente.\n\n"
                        f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                        include_image=False
                    )
                
        except Exception as e:
            logger.error(f"Error al consultar DNI {dni}: {e}")
            if loading_msg and 'result' in loading_msg:
                message_id = loading_msg['result']['message_id']
                self.edit_message(
                    chat_id, message_id,
                    f"❌ **Error al consultar** el DNI: `{dni}`\n\n"
                    "🔄 Intenta nuevamente en unos momentos.",
                    include_image=False
                )
    
    def execute_nombres_consulta(self, chat_id, user_id, user_info, nombres, loading_msg):
        """Ejecutar consulta de nombres en la cola"""
        try:
            # Obtener nombre de usuario para mostrar
            user_display = self.get_user_display_name(user_info)
            
            # Parsear nombres y apellidos del formato "nombres|apellidos"
            if '|' in nombres:
                partes = nombres.split('|', 1)
                nombres_part = partes[0]
                apellidos_part = partes[1] if len(partes) > 1 else ""
            else:
                nombres_part = nombres
                apellidos_part = ""
            
            # Consultar la API
            nombres_data = self.consultar_nombres(nombres_part, apellidos_part)
            
            if nombres_data and nombres_data.get('success'):
                # Formatear respuesta
                response = self.formatear_respuesta_nombres(nombres_data, nombres, user_display)
                
                # Si hay más de 10 resultados, crear archivo
                if len(nombres_data['data']['results']) > 10:
                    # Crear archivo TXT
                    file_path = self.crear_archivo_nombres(nombres_data['data']['results'], nombres, user_display)
                    
                    # Enviar archivo con imagen
                    self.send_document_with_image(chat_id, file_path, "📄 **Resultados de búsqueda por nombres**")
                    
                    # Eliminar mensaje de carga
                    if loading_msg and 'result' in loading_msg:
                        message_id = loading_msg['result']['message_id']
                        self.delete_message(chat_id, message_id)
                else:
                    # Mostrar resultados en el chat
                    if loading_msg and 'result' in loading_msg:
                        message_id = loading_msg['result']['message_id']
                        self.edit_message(chat_id, message_id, response, include_image=True)
            else:
                if loading_msg and 'result' in loading_msg:
                    message_id = loading_msg['result']['message_id']
                    self.edit_message(
                        chat_id, message_id,
                        f"❌ **No se encontraron resultados** para: `{nombres}`\n\n"
                        "🔍 Verifica los nombres e intenta nuevamente.\n\n"
                        f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                        include_image=True
                    )
                
        except Exception as e:
            logger.error(f"Error al consultar nombres {nombres}: {e}")
            if loading_msg and 'result' in loading_msg:
                message_id = loading_msg['result']['message_id']
                self.edit_message(
                    chat_id, message_id,
                    f"❌ **Error al consultar** los nombres: `{nombres}`\n\n"
                    "🔄 Intenta nuevamente en unos momentos.",
                    include_image=True
                )
    
    def execute_telefono_consulta(self, chat_id, user_id, user_info, numero, loading_msg):
        """Ejecutar consulta de teléfono en la cola"""
        try:
            # Obtener nombre de usuario para mostrar
            user_display = self.get_user_display_name(user_info)
            
            # Consultar la API
            telefono_data = self.consultar_telefono(numero)
            
            if telefono_data and telefono_data.get('coRespuesta') == '0000':
                # Formatear respuesta
                response = self.formatear_respuesta_telefono(telefono_data, numero, user_display)
                
                # Editar mensaje de carga
                if loading_msg and 'result' in loading_msg:
                    message_id = loading_msg['result']['message_id']
                    self.edit_message(chat_id, message_id, response, include_image=True)
            else:
                if loading_msg and 'result' in loading_msg:
                    message_id = loading_msg['result']['message_id']
                    self.edit_message(
                        chat_id, message_id,
                        f"❌ **No se encontró información** para: `{numero}`\n\n"
                        "🔍 Verifica el número e intenta nuevamente.\n\n"
                        f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                        include_image=True
                    )
                
        except Exception as e:
            logger.error(f"Error al consultar teléfono {numero}: {e}")
            if loading_msg and 'result' in loading_msg:
                message_id = loading_msg['result']['message_id']
                self.edit_message(
                    chat_id, message_id,
                    f"❌ **Error al consultar** el número: `{numero}`\n\n"
                    "🔄 Intenta nuevamente en unos momentos.",
                    include_image=True
                )
    
    def handle_cmds_command(self, chat_id):
        """Manejar comando /cmds"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔍 [RENIEC]", "callback_data": "reniec_info"}],
                [{"text": "👤 [NOMBRES]", "callback_data": "nombres_info"}],
                [{"text": "📱 [TELÉFONOS]", "callback_data": "telefonos_info"}],
                [{"text": "🌳 [ÁRBOL GENEALÓGICO]", "callback_data": "arbol_info"}]
            ]
        }
        
        message = """
**[RESPALDODOX-CHOCO]**

📋 **COMANDOS DISPONIBLES, PRESIONA UN BOTÓN**

🤖 **Respaldodox** - Tu asistente para consultas de DNI
        """
        
        self.send_message(chat_id, message, keyboard)
    
    def consultar_nombres(self, nombres, apellidos):
        """Consultar información por nombres en la API"""
        url = "https://zgatoonm.up.railway.app/nm"
        params = {
            'nombres': nombres,
            'apellidos': apellidos,
            'key': '9d2c423573b857e46235f9c50645f'
        }
        
        try:
            logger.info(f"Consultando API nombres: {url}")
            logger.info(f"Parámetros: {params}")
            response = requests.get(url, params=params, timeout=10)
            logger.info(f"Respuesta API nombres - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Datos recibidos de API nombres: {data}")
                return data
            else:
                logger.error(f"API nombres error: {response.status_code}")
                logger.error(f"Respuesta completa: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error al consultar API de nombres: {e}")
            return None
    
    def formatear_respuesta_nombres(self, data, nombres_busqueda, user_display):
        """Formatear la respuesta de búsqueda por nombres"""
        if not data.get('data') or not data['data'].get('results'):
            return f"❌ **No se encontraron resultados para: {nombres_busqueda}**\n\n🔍 Verifica los nombres e intenta nuevamente.\n\n🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
        
        results = data['data']['results']
        
        if len(results) <= 10:
            # Mostrar hasta 10 resultados en el chat
            response = f"**[RESPALDODOX-CHOCO] BÚSQUEDA POR NOMBRES**\n\n"
            response += f"🔍 **Búsqueda:** `{nombres_busqueda}`\n"
            response += f"📊 **Resultados encontrados:** {len(results)}\n\n"
            
            for i, result in enumerate(results, 1):
                response += f"**{i}.** 👤 **{result.get('nombres', 'N/A')} {result.get('apellidos', 'N/A')}**\n"
                response += f"    🆔 DNI: `{result.get('dni', 'N/A')}`\n"
                response += f"    🎂 Edad: {result.get('edad', 'N/A')}\n\n"
            
            response += f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
            return response
        else:
            # Crear archivo TXT para más de 10 resultados
            return self.crear_archivo_nombres(results, nombres_busqueda, user_display)
    
    def crear_archivo_nombres(self, results, nombres_busqueda, user_display):
        """Crear archivo TXT con los resultados de nombres"""
        content = f"[RESPALDODOX-CHOCO] BÚSQUEDA POR NOMBRES\n\n"
        content += f"Búsqueda: {nombres_busqueda}\n"
        content += f"Resultados encontrados: {len(results)}\n\n"
        
        for i, result in enumerate(results, 1):
            content += f"{i}. {result.get('nombres', 'N/A')} {result.get('apellidos', 'N/A')}\n"
            content += f"   DNI: {result.get('dni', 'N/A')}\n"
            content += f"   Edad: {result.get('edad', 'N/A')}\n\n"
        
        content += f"Consulta realizada por: {user_display}"
        
        # Crear archivo temporal
        filename = f"nombres_{int(time.time())}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename
    
    def send_document(self, chat_id, file_path, caption=None):
        """Enviar documento a Telegram"""
        url = f"{TELEGRAM_API_URL}/sendDocument"
        files = {'document': open(file_path, 'rb')}
        data = {'chat_id': chat_id}
        if caption:
            data['caption'] = caption
        
        try:
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error enviando documento: {e}")
            return None
        finally:
            # Cerrar y eliminar archivo
            files['document'].close()
            import os
            os.remove(file_path)
    
    def send_document_with_image(self, chat_id, file_path, caption=None):
        """Enviar documento con imagen adjunta a Telegram"""
        try:
            # Leer el documento
            with open(file_path, 'rb') as document:
                files = {'document': document}
                data = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                # Enviar como documento
                url = f"{TELEGRAM_API_URL}/sendDocument"
                response = requests.post(url, files=files, data=data)
                
                return response.json()
        except FileNotFoundError:
            logger.error(f"Archivo {file_path} no encontrado")
            return {'ok': False, 'error': 'File not found'}
        except Exception as e:
            logger.error(f"Error enviando documento: {e}")
            return {'ok': False, 'error': str(e)}
    
    def handle_nm_command(self, chat_id, user_id, user_info, nombres_texto):
        """Manejar comando /nm"""
        # Verificar cooldown (8 segundos)
        current_time = time.time()
        if user_id in user_cooldowns:
            time_left = 8 - (current_time - user_cooldowns[user_id])
            if time_left > 0:
                self.send_message(
                    chat_id,
                    f"⏰ **Espera {int(time_left)} segundos** antes de hacer otra consulta.\n\n"
                    "🛡️ *Sistema anti-spam activo*"
                )
                return
        
        # Actualizar cooldown
        user_cooldowns[user_id] = current_time
        
        # Procesar nombres y apellidos
        try:
            # Separar por | para nombres y apellidos
            partes = nombres_texto.split('|')
            if len(partes) < 2:
                self.send_message(
                    chat_id,
                    "❌ **Error:** Formato incorrecto.\n\n"
                    "📝 **Uso correcto:** `/nm Pedro|Castillo|Terrones`\n"
                    "📝 **Ejemplo:** `/nm Juan|Perez|Gonzalez`\n\n"
                    "🤖 *Respaldodox*"
                )
                return
            
            nombres = partes[0].strip()
            apellidos = '|'.join(partes[1:]).strip()
            
            if not nombres or not apellidos:
                self.send_message(
                    chat_id,
                    "❌ **Error:** Debes proporcionar nombres y apellidos.\n\n"
                    "📝 **Uso correcto:** `/nm Pedro|Castillo|Terrones`\n"
                    "📝 **Ejemplo:** `/nm Juan|Perez|Gonzalez`\n\n"
                    "🤖 *Respaldodox*"
                )
                return
            
            # Mostrar mensaje de carga inmediatamente
            loading_msg = self.send_message(
                chat_id,
                f"🔍 **Buscando por nombres...**\n"
                f"👤 Nombres: `{nombres}`\n"
                f"👥 Apellidos: `{apellidos}`\n"
                "⏳ Tu consulta está en cola, por favor espera..."
            )
            
            # Agregar a la cola de consultas
            consulta = {
                'tipo': 'nombres',
                'chat_id': chat_id,
                'user_id': user_id,
                'user_info': user_info,
                'parametros': {'nombres': f"{nombres}|{apellidos}"},
                'loading_msg': loading_msg
            }
            consulta_queue.put(consulta)
            logger.info(f"Consulta nombres agregada a la cola para usuario {user_id}")
                
        except Exception as e:
            logger.error(f"Error al procesar comando /nm: {e}")
            self.send_message(
                chat_id,
                f"❌ **Error al procesar** la búsqueda.\n\n"
                "🔄 Intenta nuevamente en unos momentos.\n\n"
                "🤖 *Respaldodox*"
            )
    
    def handle_callback_query(self, chat_id, message_id, callback_data):
        """Manejar callbacks de botones"""
        if callback_data == "reniec_info":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 VOLVER AL MENÚ", "callback_data": "back_to_menu"}]
                ]
            }
            
            response_text = (
                "🔍 **RENIEC - Consulta de DNI**\n\n"
                "📝 **Uso del comando /dni:**\n"
                "• Escribe: `/dni 12345678`\n"
                "• Reemplaza `12345678` con el DNI que quieres consultar\n"
                "• El DNI debe tener exactamente 8 dígitos\n\n"
                "✅ **Ejemplo:** `/dni 44443333`\n\n"
                "🤖 *Respaldodox - Bot de respaldo*"
            )
            self.edit_message_with_keyboard(chat_id, message_id, response_text, keyboard, include_image=True)
        elif callback_data == "nombres_info":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 VOLVER AL MENÚ", "callback_data": "back_to_menu"}]
                ]
            }
            
            response_text = (
                "👤 **NOMBRES - Búsqueda por Nombres**\n\n"
                "📝 **Uso del comando /nm:**\n"
                "• Escribe: `/nm Pedro|Castillo|Terrones`\n"
                "• Separa nombres y apellidos con |\n"
                "• Puedes usar múltiples nombres: `/nm Juan,Pedro|Perez|Gonzalez`\n\n"
                "✅ **Ejemplos:**\n"
                "• `/nm Juan|Perez|Gonzalez`\n"
                "• `/nm Maria,Jose|Lopez|Martinez`\n\n"
                "🤖 *Respaldodox - Bot de respaldo*"
            )
            self.edit_message_with_keyboard(chat_id, message_id, response_text, keyboard, include_image=True)
        elif callback_data == "telefonos_info":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 VOLVER AL MENÚ", "callback_data": "back_to_menu"}]
                ]
            }
            
            response_text = (
                "📱 **TELÉFONOS - Consulta Telefónica**\n\n"
                "📝 **Uso del comando /telp:**\n"
                "• Escribe: `/telp 12345678` (DNI de 8 dígitos)\n"
                "• Escribe: `/telp 987654321` (Teléfono de 9 dígitos)\n"
                "• El número debe tener exactamente 8 o 9 dígitos\n\n"
                "✅ **Ejemplos:**\n"
                "• `/telp 44443333` (DNI)\n"
                "• `/telp 987654321` (Teléfono)\n\n"
                "🤖 *Respaldodox - Bot de respaldo*"
            )
            self.edit_message_with_keyboard(chat_id, message_id, response_text, keyboard, include_image=True)
        elif callback_data == "arbol_info":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 VOLVER AL MENÚ", "callback_data": "back_to_menu"}]
                ]
            }
            
            response_text = (
                "🌳 **ÁRBOL GENEALÓGICO - Consulta Familiar**\n\n"
                "📝 **Uso del comando /arg:**\n"
                "• Escribe: `/arg 12345678` (DNI de 8 dígitos)\n"
                "• El DNI debe tener exactamente 8 dígitos\n\n"
                "✅ **Ejemplo:**\n"
                "• `/arg 44443333`\n\n"
                "🌳 **Información que obtienes:**\n"
                "• Datos de padres\n"
                "• Información de abuelos\n"
                "• Lista de hermanos\n"
                "• Datos de hijos\n\n"
                "🤖 *Respaldodox - Bot de respaldo*"
            )
            self.edit_message_with_keyboard(chat_id, message_id, response_text, keyboard, include_image=True)
        elif callback_data == "back_to_menu":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔍 [RENIEC]", "callback_data": "reniec_info"}],
                    [{"text": "👤 [NOMBRES]", "callback_data": "nombres_info"}],
                    [{"text": "📱 [TELÉFONOS]", "callback_data": "telefonos_info"}],
                    [{"text": "🌳 [ÁRBOL GENEALÓGICO]", "callback_data": "arbol_info"}]
                ]
            }
            
            response_text = (
                "**[RESPALDODOX-CHOCO]**\n\n"
                "📋 **COMANDOS DISPONIBLES, PRESIONA UN BOTÓN**\n\n"
                "🤖 **Respaldodox** - Tu asistente para consultas de DNI"
            )
            self.edit_message_with_keyboard(chat_id, message_id, response_text, keyboard, include_image=True)
    
    def consultar_telefono(self, numero):
        """Consultar información por teléfono o DNI en la API"""
        url = "http://161.132.51.34:1520/api/osipteldb"
        params = {'tel': numero}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error al consultar API de teléfonos: {e}")
            return None
    
    def consultar_arbol_genealogico(self, dni):
        """Consultar árbol genealógico por DNI en la API"""
        url = "https://zgatooarg.up.railway.app/ag"
        params = {
            'dni': dni,
            'key': 'd59c297a6fd28f7e4387720e810a66b5'
        }
        
        try:
            # Aumentar timeout a 30 segundos para esta API lenta
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API árbol genealógico respondió correctamente para DNI: {dni}")
                return data
            else:
                logger.error(f"Error en API de árbol genealógico: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error(f"Timeout en API de árbol genealógico para DNI: {dni}")
            return None
        except Exception as e:
            logger.error(f"Error al consultar API de árbol genealógico: {e}")
            return None
    
    def formatear_respuesta_telefono(self, data, numero, user_display):
        """Formatear la respuesta de consulta por teléfono"""
        if not data.get('listaAni') or not data['listaAni']:
            return f"❌ **No se encontró información para: {numero}**\n\n🔍 Verifica el número e intenta nuevamente.\n\n🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
        
        results = data['listaAni']
        
        response = f"**[RESPALDODOX-CHOCO] CONSULTA TELEFÓNICA**\n\n"
        response += f"🔍 **Consulta:** `{numero}`\n"
        response += f"📊 **Resultados encontrados:** {len(results)}\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"**{i}.** 📱 **{result.get('telefono', 'N/A')}**\n"
            response += f"    👤 **Titular:** {result.get('titular', 'N/A')}\n"
            response += f"    🆔 **DNI:** `{result.get('documento', 'N/A')}`\n"
            response += f"    🏢 **Empresa:** {result.get('empresa', 'N/A')}\n"
            response += f"    📡 **Operador:** {result.get('operador', 'N/A')}\n"
            response += f"    📋 **Plan:** {result.get('plan', 'N/A')}\n"
            response += f"    📧 **Correo:** {result.get('correo', 'N/A')}\n"
            response += f"    📅 **Fecha:** {result.get('fecha', 'N/A')}\n\n"
        
        response += f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
        return response
    
    def formatear_respuesta_arbol_genealogico(self, data, dni, user_display):
        """Formatear la respuesta de árbol genealógico"""
        # Verificar si hay familiares en la respuesta
        if not data.get('FAMILIARES') or not data['FAMILIARES']:
            return f"❌ **No se encontró información genealógica para el DNI: {dni}**\n\n🔍 Verifica el número e intenta nuevamente.\n\n🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
        
        familiares = data['FAMILIARES']
        
        response = f"<b>[RESPALDODOX-CHOCO] ÁRBOL GENEALÓGICO</b>\n\n"
        response += f"🆔 <b>DNI:</b> <code>{dni}</code>\n"
        response += f"📋 <b>Tipo de consulta:</b> {self.escape_html(data.get('TIPO_CONSULTA', 'N/A'))}\n"
        response += f"🆔 <b>Request ID:</b> <code>{data.get('request_id', 'N/A')}</code>\n\n"
        
        # Procesar familiares por relación
        if familiares:
            
            # Agrupar por relación
            relaciones = {}
            for familiar in familiares:
                relacion = familiar.get('RELACION', 'DESCONOCIDO')
                if relacion not in relaciones:
                    relaciones[relacion] = []
                relaciones[relacion].append(familiar)
            
            # Mostrar por categorías
            for relacion, lista_familiares in relaciones.items():
                if relacion == 'PADRE':
                    response += f"👨 <b>PADRES:</b>\n"
                elif relacion == 'MADRE':
                    response += f"👩 <b>MADRES:</b>\n"
                elif relacion == 'HERMANO' or relacion == 'HERMANA':
                    response += f"👫 <b>HERMANOS/AS:</b>\n"
                elif relacion == 'HIJO' or relacion == 'HIJA':
                    response += f"👶 <b>HIJOS/AS:</b>\n"
                elif relacion == 'ABUELO' or relacion == 'ABUELA' or relacion == 'ABUELA PATERNO' or relacion == 'ABUELO MATERNO':
                    response += f"👴👵 <b>ABUELOS/AS:</b>\n"
                elif relacion == 'CUÑADO' or relacion == 'CUÑADA':
                    response += f"👨‍👩‍👧‍👦 <b>CUÑADOS/AS:</b>\n"
                elif relacion == 'TIO' or relacion == 'TIA':
                    response += f"👨‍👩‍👧‍👦 <b>TIOS/AS:</b>\n"
                elif relacion == 'PRIMO' or relacion == 'PRIMA':
                    response += f"👨‍👩‍👧‍👦 <b>PRIMOS/AS:</b>\n"
                elif relacion == 'SOBRINO' or relacion == 'SOBRINA':
                    response += f"👶 <b>SOBRINOS/AS:</b>\n"
                elif relacion == 'NIETO' or relacion == 'NIETA':
                    response += f"👶 <b>NIETOS/AS:</b>\n"
                elif relacion == 'BISABUELO' or relacion == 'BISABUELA':
                    response += f"👴👵 <b>BISABUELOS/AS:</b>\n"
                else:
                    response += f"👥 <b>{self.escape_html(relacion.upper())}S:</b>\n"
                
                for i, familiar in enumerate(lista_familiares, 1):
                    nombre = f"{self.escape_html(familiar.get('NOMBRES', 'N/A'))} {self.escape_html(familiar.get('APELLIDOS', 'N/A'))}"
                    dni_familiar = familiar.get('DNI', 'N/A')
                    edad = self.escape_html(familiar.get('EDAD', 'N/A'))
                    sexo = familiar.get('SEXO', 'N/A')
                    verificacion = self.escape_html(familiar.get('VERIFICACION', 'N/A'))
                    
                    # Emoji según sexo
                    emoji_sexo = "👨" if sexo == "MASCULINO" else "👩" if sexo == "FEMENINO" else "👤"
                    
                    # Emoji según verificación
                    emoji_verif = "✅" if verificacion == "ALTA" else "⚠️" if verificacion == "MEDIA" else "❌"
                    
                    response += f"   <b>{i}.</b> {emoji_sexo} <b>{nombre}</b>\n"
                    response += f"       🆔 DNI: <code>{dni_familiar}</code>\n"
                    response += f"       🎂 Edad: {edad} años\n"
                    response += f"       {emoji_verif} Verificación: {verificacion}\n\n"
        
        response += f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
        
        # Si hay muchos familiares, crear archivo TXT
        if len(familiares) > 10:
            return self.crear_archivo_arbol_genealogico(familiares, dni, user_display, data)
        
        return response
    
    def crear_archivo_arbol_genealogico(self, familiares, dni, user_display, data):
        """Crear archivo TXT para árbol genealógico con muchos familiares"""
        try:
            # Crear contenido del archivo
            contenido = f"[RESPALDODOX-CHOCO] ÁRBOL GENEALÓGICO\n"
            contenido += f"=" * 50 + "\n\n"
            contenido += f"DNI: {dni}\n"
            contenido += f"Tipo de consulta: {data.get('TIPO_CONSULTA', 'N/A')}\n"
            contenido += f"Request ID: {data.get('request_id', 'N/A')}\n"
            contenido += f"Total familiares: {len(familiares)}\n\n"
            
            # Agrupar por relación
            relaciones = {}
            for familiar in familiares:
                relacion = familiar.get('RELACION', 'DESCONOCIDO')
                if relacion not in relaciones:
                    relaciones[relacion] = []
                relaciones[relacion].append(familiar)
            
            # Escribir por categorías
            for relacion, lista_familiares in relaciones.items():
                if relacion == 'PADRE':
                    contenido += f"PADRES:\n"
                elif relacion == 'MADRE':
                    contenido += f"MADRES:\n"
                elif relacion == 'HERMANO' or relacion == 'HERMANA':
                    contenido += f"HERMANOS/AS:\n"
                elif relacion == 'HIJO' or relacion == 'HIJA':
                    contenido += f"HIJOS/AS:\n"
                elif relacion == 'ABUELO' or relacion == 'ABUELA' or relacion == 'ABUELA PATERNO' or relacion == 'ABUELO MATERNO':
                    contenido += f"ABUELOS/AS:\n"
                elif relacion == 'CUÑADO' or relacion == 'CUÑADA':
                    contenido += f"CUÑADOS/AS:\n"
                elif relacion == 'TIO' or relacion == 'TIA':
                    contenido += f"TIOS/AS:\n"
                elif relacion == 'PRIMO' or relacion == 'PRIMA':
                    contenido += f"PRIMOS/AS:\n"
                elif relacion == 'SOBRINO' or relacion == 'SOBRINA':
                    contenido += f"SOBRINOS/AS:\n"
                elif relacion == 'NIETO' or relacion == 'NIETA':
                    contenido += f"NIETOS/AS:\n"
                elif relacion == 'BISABUELO' or relacion == 'BISABUELA':
                    contenido += f"BISABUELOS/AS:\n"
                else:
                    contenido += f"{relacion.upper()}S:\n"
                
                for i, familiar in enumerate(lista_familiares, 1):
                    nombre = f"{familiar.get('NOMBRES', 'N/A')} {familiar.get('APELLIDOS', 'N/A')}"
                    dni_familiar = familiar.get('DNI', 'N/A')
                    edad = familiar.get('EDAD', 'N/A')
                    sexo = familiar.get('SEXO', 'N/A')
                    verificacion = familiar.get('VERIFICACION', 'N/A')
                    
                    contenido += f"   {i}. {nombre}\n"
                    contenido += f"       DNI: {dni_familiar}\n"
                    contenido += f"       Edad: {edad} años\n"
                    contenido += f"       Sexo: {sexo}\n"
                    contenido += f"       Verificación: {verificacion}\n\n"
            
            contenido += f"Consulta realizada por: {user_display}\n"
            contenido += f"Fecha: {time.strftime('%d/%m/%Y %H:%M:%S')}\n"
            
            # Guardar archivo
            filename = f"arbol_genealogico_{dni}_{int(time.time())}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error creando archivo de árbol genealógico: {e}")
            return None
    
    def handle_telp_command(self, chat_id, user_id, user_info, numero):
        """Manejar comando /telp"""
        # Verificar cooldown (8 segundos)
        current_time = time.time()
        if user_id in user_cooldowns:
            time_left = 8 - (current_time - user_cooldowns[user_id])
            if time_left > 0:
                self.send_message(
                    chat_id,
                    f"⏰ **Espera {int(time_left)} segundos** antes de hacer otra consulta.\n\n"
                    "🛡️ *Sistema anti-spam activo*"
                )
                return
        
        # Actualizar cooldown
        user_cooldowns[user_id] = current_time
        
        # Validar formato del número
        if not numero.isdigit():
            self.send_message(
                chat_id,
                "❌ **Error:** El número debe contener solo dígitos.\n\n"
                "📝 **Uso correcto:** `/telp 12345678` (DNI de 8 dígitos)\n"
                "📝 **Uso correcto:** `/telp 987654321` (Teléfono de 9 dígitos)\n"
                "📝 **Ejemplo:** `/telp 44443333`\n\n"
                "🤖 *Respaldodox*"
            )
            return
        
        # Validar longitud
        if len(numero) == 8:
            tipo_consulta = "DNI"
        elif len(numero) == 9:
            tipo_consulta = "Teléfono"
        else:
            self.send_message(
                chat_id,
                f"❌ **Error:** El número debe tener 8 dígitos (DNI) o 9 dígitos (teléfono).\n\n"
                f"📝 **Recibido:** {len(numero)} dígitos\n"
                f"📝 **Debe ser:** 8 dígitos para DNI o 9 dígitos para teléfono\n\n"
                "🤖 *Respaldodox*"
            )
            return
        
        # Mostrar mensaje de carga inmediatamente
        loading_msg = self.send_message(
            chat_id,
            f"🔍 **Consultando {tipo_consulta.lower()}...**\n"
            f"📞 {tipo_consulta}: `{numero}`\n"
            "⏳ Tu consulta está en cola, por favor espera..."
        )
        
        # Agregar a la cola de consultas
        consulta = {
            'tipo': 'telefono',
            'chat_id': chat_id,
            'user_id': user_id,
            'user_info': user_info,
            'parametros': {'numero': numero},
            'loading_msg': loading_msg
        }
        consulta_queue.put(consulta)
        logger.info(f"Consulta teléfono agregada a la cola para usuario {user_id}")
    
    def handle_arg_command(self, chat_id, user_id, user_info, dni):
        """Manejar comando /arg"""
        # Verificar cooldown (8 segundos)
        current_time = time.time()
        if user_id in user_cooldowns:
            time_left = 8 - (current_time - user_cooldowns[user_id])
            if time_left > 0:
                self.send_message(
                    chat_id,
                    f"⏰ **Espera {int(time_left)} segundos** antes de hacer otra consulta.\n\n"
                    "🛡️ *Sistema anti-spam activo*"
                )
                return
        
        # Actualizar cooldown
        user_cooldowns[user_id] = current_time
        
        # Validar formato del DNI
        if not dni.isdigit() or len(dni) != 8:
            self.send_message(
                chat_id,
                "❌ **Error:** El DNI debe tener exactamente 8 dígitos.\n\n"
                "📝 **Uso correcto:** `/arg 12345678`\n"
                "📝 **Ejemplo:** `/arg 44443333`\n\n"
                "🤖 *Respaldodox*"
            )
            return
        
        # Mostrar mensaje de carga
        loading_msg = self.send_message(
            chat_id,
            f"🌳 **Consultando árbol genealógico...**\n"
            f"📄 DNI: `{dni}`\n"
            "⏳ Esta consulta puede tardar hasta 30 segundos...\n"
            "🔄 Por favor espera pacientemente..."
        )
        
        try:
            # Obtener nombre de usuario para mostrar
            user_display = self.get_user_display_name(user_info)
            
            # Consultar la API
            arbol_data = self.consultar_arbol_genealogico(dni)
            logger.info(f"Datos de API recibidos: {arbol_data}")
            
            if arbol_data:
                logger.info(f"Verificando familiares: {arbol_data.get('FAMILIARES')}")
                # Verificar si la respuesta tiene familiares
                if arbol_data.get('FAMILIARES') and len(arbol_data['FAMILIARES']) > 0:
                    logger.info(f"Encontrados {len(arbol_data['FAMILIARES'])} familiares")
                    # Formatear respuesta
                    response = self.formatear_respuesta_arbol_genealogico(arbol_data, dni, user_display)
                    logger.info(f"Respuesta formateada: {response[:100]}...")
                    
                    # Verificar si es un archivo
                    logger.info(f"Tipo de respuesta: {type(response)}")
                    logger.info(f"Contenido de respuesta: {response[:100]}...")
                    logger.info(f"¿Termina en .txt?: {response.endswith('.txt') if isinstance(response, str) else False}")
                    
                    if isinstance(response, str) and response.endswith('.txt'):
                        # Es un archivo, enviarlo como documento
                        logger.info(f"Enviando archivo: {response}")
                        caption = f"🌳 <b>Árbol Genealógico - DNI: {dni}</b>\n\n📊 <b>Total familiares:</b> {len(arbol_data['FAMILIARES'])}\n\n📄 <b>Los datos son muy largos, por eso te enviamos un archivo TXT</b>\n\n🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
                        result = self.send_document_with_image(chat_id, response, caption)
                        logger.info(f"Resultado del envío de archivo: {result}")
                        
                        # Eliminar archivo temporal
                        try:
                            os.remove(response)
                        except:
                            pass
                    else:
                        # Es texto normal, enviar mensaje
                        logger.info("Procesando como texto normal")
                        result = self.send_message(chat_id, response, include_image=True)
                        logger.info(f"Resultado del envío: {result}")
                    
                    # Eliminar mensaje de carga
                    if loading_msg and 'result' in loading_msg:
                        message_id = loading_msg['result']['message_id']
                        self.delete_message(chat_id, message_id)
                else:
                    # No hay familiares en la respuesta
                    self.send_message(
                        chat_id,
                        f"❌ **No se encontró información genealógica** para el DNI: `{dni}`\n\n"
                        "🔍 Verifica que el número sea correcto e intenta nuevamente.\n\n"
                        f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                        include_image=True
                    )
                    
                    # Eliminar mensaje de carga
                    if loading_msg and 'result' in loading_msg:
                        message_id = loading_msg['result']['message_id']
                        self.delete_message(chat_id, message_id)
            else:
                # Error en la consulta (timeout, error de conexión, etc.)
                self.send_message(
                    chat_id,
                    f"⏰ **Timeout en la consulta** del árbol genealógico para DNI: `{dni}`\n\n"
                    "🔄 La API está tardando más de lo esperado.\n"
                    "💡 Intenta nuevamente en unos momentos.\n\n"
                    f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                    include_image=True
                )
                
                # Eliminar mensaje de carga
                if loading_msg and 'result' in loading_msg:
                    message_id = loading_msg['result']['message_id']
                    self.delete_message(chat_id, message_id)
                
        except Exception as e:
            logger.error(f"Error al procesar comando /arg: {e}")
            self.send_message(
                chat_id,
                f"❌ **Error al procesar** la consulta.\n\n"
                "🔄 Intenta nuevamente en unos momentos.\n\n"
                f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                include_image=True
            )
            
            # Eliminar mensaje de carga
            if loading_msg and 'result' in loading_msg:
                message_id = loading_msg['result']['message_id']
                self.delete_message(chat_id, message_id)
    
    def execute_arbol_consulta(self, chat_id, user_id, user_info, dni, loading_msg):
        """Ejecutar consulta árbol genealógico en la cola"""
        try:
            logger.info(f"Iniciando consulta árbol genealógico para DNI: {dni}")
            
            # Obtener nombre de usuario para mostrar
            user_display = self.get_user_display_name(user_info)
            logger.info(f"Usuario display: {user_display}")
            
            # Consultar la API
            arbol_data = self.consultar_arbol_genealogico(dni)
            logger.info(f"Datos recibidos de API: {arbol_data is not None}")
            
            if arbol_data:
                # Verificar si la respuesta tiene familiares
                if arbol_data.get('FAMILIARES') and len(arbol_data['FAMILIARES']) > 0:
                    logger.info(f"Encontrados {len(arbol_data['FAMILIARES'])} familiares")
                    # Formatear respuesta
                    response = self.formatear_respuesta_arbol_genealogico(arbol_data, dni, user_display)
                    logger.info(f"Respuesta formateada, longitud: {len(response)}")
                    
                    # Verificar si es un archivo
                    logger.info(f"Tipo de respuesta: {type(response)}")
                    logger.info(f"Contenido de respuesta: {response[:100]}...")
                    logger.info(f"¿Termina en .txt?: {response.endswith('.txt') if isinstance(response, str) else False}")
                    
                    if isinstance(response, str) and response.endswith('.txt'):
                        # Es un archivo, enviarlo como documento
                        logger.info(f"Enviando archivo: {response}")
                        caption = f"🌳 <b>Árbol Genealógico - DNI: {dni}</b>\n\n📊 <b>Total familiares:</b> {len(arbol_data['FAMILIARES'])}\n\n📄 <b>Los datos son muy largos, por eso te enviamos un archivo TXT</b>\n\n🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>"
                        result = self.send_document_with_image(chat_id, response, caption)
                        logger.info(f"Resultado del envío de archivo: {result}")
                        
                        # Eliminar archivo temporal
                        try:
                            os.remove(response)
                        except:
                            pass
                    else:
                        # Es texto normal, editar mensaje
                        logger.info("Procesando como texto normal")
                        if loading_msg and 'result' in loading_msg:
                            message_id = loading_msg['result']['message_id']
                            logger.info(f"Editando mensaje {message_id} en chat {chat_id}")
                            self.edit_message(chat_id, message_id, response, include_image=True)
                            logger.info("Mensaje editado exitosamente")
                        else:
                            logger.error("No se pudo obtener message_id del loading_msg")
                else:
                    # No hay familiares en la respuesta
                    if loading_msg and 'result' in loading_msg:
                        message_id = loading_msg['result']['message_id']
                        self.edit_message(
                            chat_id, message_id,
                            f"❌ **No se encontró información genealógica** para el DNI: `{dni}`\n\n"
                            "🔍 Verifica que el número sea correcto e intenta nuevamente.\n\n"
                            f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                            include_image=True
                        )
            else:
                # Error en la consulta (timeout, error de conexión, etc.)
                if loading_msg and 'result' in loading_msg:
                    message_id = loading_msg['result']['message_id']
                    self.edit_message(
                        chat_id, message_id,
                        f"⏰ **Timeout en la consulta** del árbol genealógico para DNI: `{dni}`\n\n"
                        "🔄 La API está tardando más de lo esperado.\n"
                        "💡 Intenta nuevamente en unos momentos.\n\n"
                        f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                        include_image=True
                    )
                
        except Exception as e:
            logger.error(f"Error al procesar comando /arg: {e}")
            if loading_msg and 'result' in loading_msg:
                message_id = loading_msg['result']['message_id']
                self.edit_message(
                    chat_id, message_id,
                    f"❌ **Error al procesar** la consulta.\n\n"
                    "🔄 Intenta nuevamente en unos momentos.\n\n"
                    f"🤖 <i>Consulta realizada por: {self.escape_html(user_display)}</i>",
                    include_image=True
                )
    
    def is_command(self, text):
        """Verificar si el texto es un comando válido"""
        valid_commands = ['/start', '/dni', '/DNI', '.dni', '/cmds', '/CMDS', '.cmds', '/nm', '/NM', '.nm', '/telp', '/TELP', '.telp', '/arg', '/ARG', '.arg', '/adduser', '/unuser']
        return any(text.startswith(cmd) for cmd in valid_commands)
    
    def get_user_display_name(self, user_info):
        """Obtener el nombre de usuario para mostrar"""
        # Prioridad: username > first_name > id
        if user_info.get('username'):
            return f"@{user_info['username']}"
        elif user_info.get('first_name'):
            last_name = user_info.get('last_name', '')
            full_name = f"{user_info['first_name']} {last_name}".strip()
            return full_name
        else:
            return f"Usuario {user_info.get('id', 'Desconocido')}"
    
    def handle_message(self, chat_id, user_id, user_info, text, chat_type=None, chat_title=None):
        """Manejar mensajes de texto"""
        # Solo procesar comandos válidos
        if not self.is_command(text):
            return  # Ignorar mensajes que no son comandos
        
        # Verificar acceso (excepto para comandos de administración)
        if not text.startswith('/adduser') and not text.startswith('/unuser'):
            if not self.can_use_bot(chat_type, chat_title, user_id):
                self.send_access_denied_message(chat_id, chat_type, chat_title)
                return
        
        if text.startswith('/start'):
            self.handle_start_command(chat_id)
        elif text.startswith('/adduser '):
            username = text.split(' ', 1)[1] if len(text.split(' ')) > 1 else ""
            self.handle_adduser_command(chat_id, user_id, user_info, username)
        elif text.startswith('/unuser '):
            username = text.split(' ', 1)[1] if len(text.split(' ')) > 1 else ""
            self.handle_unuser_command(chat_id, user_id, user_info, username)
        elif text.startswith('/dni ') or text.startswith('/DNI ') or text.startswith('.dni '):
            dni = text.split(' ', 1)[1] if len(text.split(' ')) > 1 else ""
            if not dni:
                self.send_message(
                    chat_id,
                    "❌ **Error:** Debes proporcionar un número de DNI.\n\n"
                    "📝 **Uso correcto:** `/dni 12345678`\n"
                    "📝 **Ejemplo:** `/dni 44443333`\n\n"
                    "🤖 *Respaldodox*"
                )
                return
            self.handle_dni_command(chat_id, user_id, user_info, dni)
        elif text.startswith('/nm ') or text.startswith('/NM ') or text.startswith('.nm '):
            nombres = text.split(' ', 1)[1] if len(text.split(' ')) > 1 else ""
            if not nombres:
                self.send_message(
                    chat_id,
                    "❌ **Error:** Debes proporcionar nombres y apellidos.\n\n"
                    "📝 **Uso correcto:** `/nm Pedro|Castillo|Terrones`\n"
                    "📝 **Ejemplo:** `/nm Juan|Perez|Gonzalez`\n\n"
                    "🤖 *Respaldodox*"
                )
                return
            self.handle_nm_command(chat_id, user_id, user_info, nombres)
        elif text.startswith('/telp ') or text.startswith('/TELP ') or text.startswith('.telp '):
            telefono = text.split(' ', 1)[1] if len(text.split(' ')) > 1 else ""
            if not telefono:
                self.send_message(
                    chat_id,
                    "❌ **Error:** Debes proporcionar un DNI o teléfono.\n\n"
                    "📝 **Uso correcto:** `/telp 12345678` (DNI de 8 dígitos)\n"
                    "📝 **Uso correcto:** `/telp 987654321` (Teléfono de 9 dígitos)\n"
                    "📝 **Ejemplo:** `/telp 44443333`\n\n"
                    "🤖 *Respaldodox*"
                )
                return
            self.handle_telp_command(chat_id, user_id, user_info, telefono)
        elif text.startswith('/arg ') or text.startswith('/ARG ') or text.startswith('.arg '):
            dni = text.split(' ', 1)[1] if len(text.split(' ')) > 1 else ""
            if not dni:
                self.send_message(
                    chat_id,
                    "❌ **Error:** Debes proporcionar un número de DNI.\n\n"
                    "📝 **Uso correcto:** `/arg 12345678`\n"
                    "📝 **Ejemplo:** `/arg 44443333`\n\n"
                    "🤖 *Respaldodox*"
                )
                return
            self.handle_arg_command(chat_id, user_id, user_info, dni)
        elif text.startswith('/cmds') or text.startswith('/CMDS') or text.startswith('.cmds'):
            self.handle_cmds_command(chat_id)
    
    def process_update(self, update):
        """Procesar una actualización de Telegram"""
        try:
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                user_id = message['from']['id']
                user_info = message['from']
                text = message.get('text', '')
                chat_type = message['chat'].get('type')
                chat_title = message['chat'].get('title')
                
                if text:
                    self.handle_message(chat_id, user_id, user_info, text, chat_type, chat_title)
            
            elif 'callback_query' in update:
                callback_query = update['callback_query']
                chat_id = callback_query['message']['chat']['id']
                message_id = callback_query['message']['message_id']
                callback_data = callback_query['data']
                
                self.handle_callback_query(chat_id, message_id, callback_data)
                
        except Exception as e:
            logger.error(f"Error procesando update: {e}")
    
    def run(self):
        """Ejecutar el bot"""
        logger.info("🤖 Iniciando Respaldodox...")
        
        while self.running:
            try:
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    for update in updates.get('result', []):
                        self.last_update_id = update['update_id']
                        self.process_update(update)
                
                time.sleep(1)  # Esperar 1 segundo entre consultas
                
            except KeyboardInterrupt:
                logger.info("🤖 Deteniendo Respaldodox...")
                self.running = False
            except Exception as e:
                logger.error(f"Error en el loop principal: {e}")
                time.sleep(5)  # Esperar 5 segundos antes de reintentar

if __name__ == "__main__":
    bot = RespaldoDoxBot()
    bot.run()
