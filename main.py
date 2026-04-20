# main.py
import sys
import os
import logging

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.logging_config import configure_logging
from Vista.login import start_login
from Vista.home import start_home

def main():
    """Función principal que inicia la aplicación"""
    # Configurar logging al inicio
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Iniciando SecurityManager")
    
    # Callback que se ejecuta cuando el login es exitoso
    def on_login_success(admin_user, fernet_key):
        logger.info(f"Login exitoso para usuario: {admin_user.username}")
        # Iniciar la ventana principal
        start_home(admin_user, fernet_key)
    
    # Iniciar con la ventana de login
    start_login(on_login_success)

if __name__ == "__main__":
    main()