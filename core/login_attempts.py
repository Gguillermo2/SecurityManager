# core/login_attempts.py
"""
Gestión de intentos de login fallidos con bloqueo temporal.
Implementa límite de 4 intentos con bloqueo de 5 minutos.
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

from core.almacenamiento import (
    get_failed_login_attempts,
    get_last_failed_attempt_time,
    record_login_attempt,
    clear_login_attempts
)

logger = logging.getLogger(__name__)

# Configuración
MAX_FAILED_ATTEMPTS = 4
LOCKOUT_DURATION_MINUTES = 5


def is_user_locked_out(username: str) -> tuple[bool, str]:
    """
    Verifica si un usuario está bloqueado por intentos fallidos.
    
    Retorna:
        (True, mensaje_de_error) si está bloqueado
        (False, "") si no está bloqueado
    """
    failed_attempts = get_failed_login_attempts(username, minutes=LOCKOUT_DURATION_MINUTES)
    
    if failed_attempts >= MAX_FAILED_ATTEMPTS:
        # Calcular tiempo restante de bloqueo
        last_attempt_time_str = get_last_failed_attempt_time(username)
        
        if last_attempt_time_str:
            try:
                last_attempt_time = datetime.fromisoformat(last_attempt_time_str)
                lockout_end_time = last_attempt_time + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                time_remaining = lockout_end_time - datetime.now()
                
                if time_remaining.total_seconds() > 0:
                    minutes = int(time_remaining.total_seconds() // 60)
                    seconds = int(time_remaining.total_seconds() % 60)
                    message = (
                        f"Cuenta bloqueada por demasiados intentos fallidos. "
                        f"Intente más tarde en {minutes}m {seconds}s."
                    )
                    logger.warning(f"Usuario {username} está bloqueado por {minutes}m {seconds}s")
                    return True, message
            except Exception as e:
                logger.error(f"Error al calcular tiempo de bloqueo: {e}")
        
        return True, "Cuenta bloqueada. Intente más tarde."
    
    return False, ""


def record_failed_login_attempt(username: str):
    """
    Registra un intento de login fallido.
    """
    record_login_attempt(username, success=False)
    failed_count = get_failed_login_attempts(username, minutes=LOCKOUT_DURATION_MINUTES)
    
    if failed_count < MAX_FAILED_ATTEMPTS:
        remaining_attempts = MAX_FAILED_ATTEMPTS - failed_count
        logger.warning(
            f"Intento de login fallido para {username}. "
            f"Intentos restantes: {remaining_attempts}"
        )
    else:
        logger.warning(f"Usuario {username} ha sido bloqueado por exceso de intentos fallidos")


def record_successful_login_attempt(username: str):
    """
    Registra un intento de login exitoso y limpia los intentos fallidos previos.
    """
    record_login_attempt(username, success=True)
    clear_login_attempts(username)
    logger.info(f"Login exitoso para {username}. Intentos fallidos limpiados.")


def get_remaining_attempts(username: str) -> int:
    """
    Retorna el número de intentos restantes antes del bloqueo.
    Si el resultado es negativo, el usuario está bloqueado.
    """
    failed_attempts = get_failed_login_attempts(username, minutes=LOCKOUT_DURATION_MINUTES)
    return MAX_FAILED_ATTEMPTS - failed_attempts
