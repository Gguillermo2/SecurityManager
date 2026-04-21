# core/logging_config.py
import logging
import logging.handlers
import os
from pathlib import Path

def configure_logging():
    """
    Configura el logging para toda la aplicación.
    Crea logs en el directorio AppData/GestorDeCuentasWroser/logs/
    """
    # Crear directorio de logs en AppData
    appdata = os.getenv('APPDATA') or os.path.expanduser('~')
    log_dir = Path(appdata) / "GestorDeCuentasWroser" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "security_manager.log"
    
    # Configurar formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Handler para archivo (DEBUG y superiores)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola (INFO y superiores)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info("=" * 60)
    logger.info("Logging configurado correctamente")
    logger.info(f"Archivo de logs: {log_file}")
    logger.info("=" * 60)
