# core/autenticacion.py
from typing import Optional
from Modelo.models import AdminUser
from core.seguridad import (
    hash_password_bcrypt, check_password_bcrypt,
    generate_totp_secret, generate_salt,
    generate_fernet_key_from_password,
)
from core.almacenamiento import (
    initialize_database, save_admin_user, load_admin_user
)
from base64 import urlsafe_b64encode, urlsafe_b64decode
import logging

logger = logging.getLogger(__name__)


def admin_exists() -> bool:
    """Retorna True si ya hay un administrador registrado en la BD."""
    initialize_database()
    return load_admin_user() is not None


def load_admin_user_data() -> Optional[dict]:
    """
    Retorna los datos del usuario administrador como diccionario.
    Útil para crear instancia de AdminUser después de creación.
    """
    initialize_database()
    return load_admin_user()


def generar_Admin(username: str, password: str) -> tuple[bool, str]:
    """
    Crea el usuario administrador con contraseña maestra y TOTP.
    Retorna (True, mensaje) si se creó correctamente, (False, mensaje) en caso contrario.
    """
    if not username or not password:
        return False, "Usuario y contraseña son obligatorios"

    initialize_database()

    if load_admin_user() is not None:
        return False, "El usuario administrador ya existe"

    hashed_password = hash_password_bcrypt(password)
    fernet_salt_bytes = generate_salt()
    fernet_salt_str = urlsafe_b64encode(fernet_salt_bytes).decode('utf-8')
    totp_secret = generate_totp_secret()

    save_admin_user(
        username=username,
        password=hashed_password,
        totp_secret=totp_secret,
        fernet_key_salt=fernet_salt_str,
    )

    logger.info(f"Usuario administrador '{username}' creado exitosamente.")
    return True, "Usuario administrador creado correctamente"


def autenticar_admin(username: str, password: str) -> tuple[AdminUser | None, bytes | None]:
    """
    Autentica al administrador con nombre de usuario y contraseña maestra.
    Devuelve (AdminUser, fernet_key) si la autenticación es exitosa, o (None, None).
    """
    initialize_database()
    user_data = load_admin_user()

    if user_data is None:
        logger.warning("Intento de autenticación sin usuario registrado.")
        return None, None

    admin_user = AdminUser(**user_data)

    if username == admin_user.username and check_password_bcrypt(password, admin_user.password):
        try:
            fernet_salt_bytes = urlsafe_b64decode(admin_user.fernet_key_salt)
            fernet_key = generate_fernet_key_from_password(password, fernet_salt_bytes)
            logger.info(f"Autenticación exitosa para '{username}'.")
            return admin_user, fernet_key
        except Exception as e:
            logger.error(f"Error al derivar clave Fernet: {e}", exc_info=True)
            return None, None

    logger.warning(f"Credenciales incorrectas para '{username}'.")
    return None, None