# core/autenticacion
from Modelo.models import AdminUser
from core.seguridad import hash_password_bcrypt, check_password_bcrypt, generate_totp_secret, \
                        generate_salt, generate_fernet_key_from_password, verify_totp as seguridad_verify_totp
from core.almacenamiento import save_jsonD, load_json_data
from base64 import urlsafe_b64encode, urlsafe_b64decode

UserPrincipal = "DBusers.json"


def generar_Admin(username: str, password: str) -> tuple[bool, str]:
    """
    Crea un nuevo usuario administrador con contraseña maestra y TOTP.
    Retorna (True, mensaje) si se creó correctamente, o (False, mensaje) en caso contrario.
    """
    if not username or not password:
        return False, "Usuario y contraseña son obligatorios"

    user_data = load_json_data(UserPrincipal)
    if user_data is not None:
        return False, "El usuario administrador ya existe"

    hashed_password = hash_password_bcrypt(password)
    fernet_salt_bytes = generate_salt()
    fernet_salt_str = urlsafe_b64encode(fernet_salt_bytes).decode('utf-8')
    totp_secret = generate_totp_secret()

    nuevo_admin = AdminUser(
        username=username,
        password=hashed_password,
        totp_secret=totp_secret,
        fernet_key_salt=fernet_salt_str
    )

    save_jsonD(UserPrincipal, nuevo_admin.model_dump())
    return True, "Usuario administrador creado correctamente"


def autenticar_admin(username: str, password: str) -> tuple[AdminUser | None, bytes | None]:
    """
    Autentica al administrador usando el nombre de usuario y contraseña.
    Devuelve (AdminUser, fernet_key_bytes) cuando la autenticación es exitosa,
    o (None, None) en caso contrario.
    """
    user_data = load_json_data(UserPrincipal)
    if user_data is None:
        return None, None

    admin_user = AdminUser(**user_data)

    if username == admin_user.username and check_password_bcrypt(password, admin_user.password):
        try:
            fernet_salt_bytes = urlsafe_b64decode(admin_user.fernet_key_salt)
            fernet_key_for_session = generate_fernet_key_from_password(password, fernet_salt_bytes)
            return admin_user, fernet_key_for_session
        except Exception:
            return None, None

    return None, None