# core/login_controller.py
import pyotp
import qrcode
from PIL import Image, ImageTk
import io
from tkinter import messagebox

from core.autenticacion import generar_Admin, autenticar_admin
from core.seguridad import verify_totp, generate_totp_secret
from Modelo.models import AdminUser


class LoginController:
    def __init__(self):
        self.current_user: AdminUser | None = None
        self.fernet_key: bytes | None = None

    def admin_exists(self) -> bool:
        """Verifica si ya existe un administrador"""
        from core.almacenamiento import load_json_data
        return load_json_data("DBusers.json") is not None

    def create_admin(self, username: str, master_password: str) -> tuple[bool, str]:
        """Crea el usuario administrador (lógica de negocio)"""
        if not username or not master_password:
            return False, "Todos los campos son obligatorios"

        success, message = generar_Admin(username, master_password)
        return success, message

    def authenticate(self, username: str, password: str) -> tuple[bool, AdminUser | None, bytes | None]:
        """Autentica usuario + contraseña maestra"""
        admin_user, fernet_key = autenticar_admin(username, password)
        if admin_user and fernet_key:
            self.current_user = admin_user
            self.fernet_key = fernet_key
            return True, admin_user, fernet_key
        return False, None, None

    def verify_totp_code(self, code: str) -> bool:
        """Verifica el código TOTP"""
        if not self.current_user or not code:
            return False
        
        try:
            return verify_totp(self.current_user.totp_secret, code)
        except Exception:
            return False

    def get_totp_uri(self, username: str) -> str:
        """Genera URI para QR de TOTP"""
        if not self.current_user:
            return ""
        totp = pyotp.TOTP(self.current_user.totp_secret)
        return totp.provisioning_uri(name=username, issuer_name="GestorWroser")