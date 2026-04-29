# Controladores/login_controller.py
import pyotp
import logging
from Modelo.models import AdminUser
from core.autenticacion import generar_Admin, autenticar_admin, admin_exists, load_admin_user_data
from core.seguridad import verify_totp
from core.login_attempts import (
    is_user_locked_out, 
    record_failed_login_attempt,
    record_successful_login_attempt,
    get_remaining_attempts
)

logger = logging.getLogger(__name__)


class LoginController:
    def __init__(self):
        self.current_user: AdminUser | None = None
        self.fernet_key: bytes | None = None

    def admin_exists(self) -> bool:
        """Verifica si ya existe un administrador en la base de datos."""
        return admin_exists()

    def create_admin(self, username: str, master_password: str) -> tuple[bool, str]:
        """Crea el usuario administrador."""
        if not username or not master_password:
            return False, "Todos los campos son obligatorios"
        
        success, message = generar_Admin(username, master_password)
        
        if success:
            # Cargar el usuario recién creado para tener el secreto TOTP disponible
            try:
                user_data = load_admin_user_data()
                if user_data:
                    self.current_user = AdminUser(**user_data)
                    logger.info(f"Usuario {username} cargado en memoria para QR TOTP")
            except Exception as e:
                logger.error(f"Error al cargar usuario recién creado: {e}", exc_info=True)
        
        return success, message

    def authenticate(self, username: str, password: str) -> tuple[bool, AdminUser | None, bytes | None, str]:
        """
        Autentica usuario + contraseña maestra.
        
        Retorna:
            (True, admin_user, fernet_key, "") si autenticación exitosa
            (False, None, None, mensaje_error) si falla
        """
        # Verificar si el usuario está bloqueado por intentos fallidos
        is_locked, lockout_message = is_user_locked_out(username)
        if is_locked:
            return False, None, None, lockout_message
        
        # Intentar autenticar
        admin_user, fernet_key = autenticar_admin(username, password)
        
        if admin_user and fernet_key:
            # Login exitoso: guardar intento exitoso y limpiar intentos fallidos
            record_successful_login_attempt(username)
            self.current_user = admin_user
            self.fernet_key = fernet_key
            logger.info(f"Autenticación exitosa para {username}")
            return True, admin_user, fernet_key, ""
        else:
            # Login fallido: registrar intento fallido
            record_failed_login_attempt(username)
            remaining = get_remaining_attempts(username)
            
            if remaining > 0:
                message = f"Credenciales incorrectas. Intentos restantes: {remaining}"
            else:
                message = "Credenciales incorrectas. Cuenta bloqueada por demasiados intentos."
            
            logger.warning(f"Autenticación fallida para {username}. Intentos restantes: {remaining}")
            return False, None, None, message

    def verify_totp_code(self, code: str) -> bool:
        """Verifica el código TOTP."""
        if not self.current_user or not code:
            return False
        try:
            return verify_totp(self.current_user.totp_secret, code)
        except Exception:
            return False

    def get_totp_uri(self, username: str) -> str:
        """
        Genera URI para QR de TOTP.
        Primero intenta usar self.current_user, si no está disponible 
        carga del usuario administrador de la BD.
        """
        if not self.current_user:
            # Cargar desde BD si no está en memoria
            try:
                user_data = load_admin_user_data()
                if user_data:
                    self.current_user = AdminUser(**user_data)
                    logger.info("Usuario administrador cargado de BD para generar URI TOTP")
                else:
                    logger.error("No se pudo cargar usuario administrador de BD")
                    return ""
            except Exception as e:
                logger.error(f"Error al cargar usuario para URI TOTP: {e}", exc_info=True)
                return ""
        
        if not self.current_user or not self.current_user.totp_secret:
            logger.warning("Usuario o secreto TOTP no disponible")
            return ""
        
        try:
            totp = pyotp.TOTP(self.current_user.totp_secret)
            uri = totp.provisioning_uri(name=username, issuer_name="GestorWroser")
            logger.info(f"URI TOTP generada correctamente para {username}")
            return uri
        except Exception as e:
            logger.error(f"Error al generar URI TOTP: {e}", exc_info=True)
            return ""
    
    def check_lockout_status(self, username: str) -> tuple[bool, str]:
        """
        Verifica si un usuario está bloqueado por intentos fallidos.
        Retorna (True, mensaje) si está bloqueado, (False, "") si no.
        """
        return is_user_locked_out(username)
    
    def get_remaining_login_attempts(self, username: str) -> int:
        """
        Retorna el número de intentos de login restantes antes del bloqueo.
        """
        return get_remaining_attempts(username)