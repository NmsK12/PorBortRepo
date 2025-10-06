#!/usr/bin/env python3
"""
Script de inicio para Respaldodox Bot en Railway
"""

import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Función principal"""
    try:
        # Verificar variables de entorno
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN no está configurado")
            sys.exit(1)
        
        logger.info("🤖 Iniciando Respaldodox Bot...")
        logger.info(f"Bot Token: {bot_token[:10]}...")
        
        # Importar y ejecutar el bot
        from bot_requests import RespaldoDoxBot
        
        bot = RespaldoDoxBot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("🤖 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
