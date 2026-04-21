# core/seguridad.py
import os
import bcrypt
import secrets
import pyotp
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode

logger = logging.getLogger(__name__)

# NOTA: La ruta de almacenamiento de datos (AppData/GestorDeCuentasWroser)
# ahora está centralizada en core/almacenamiento.py → get_appdata_dir().
# Este módulo ya no necesita definir su propia RUTA_DBWROSER.


# --- Hashing con BCrypt (contraseña maestra del usuario) ---

def hash_password_bcrypt(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password_bcrypt(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


# --- Derivación de Clave Fernet con PBKDF2HMAC ---

def generate_fernet_key_from_password(master_password: str, salt: bytes) -> bytes:
    """Deriva una clave Fernet de 256 bits a partir de la contraseña maestra."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
        backend=default_backend()
    )
    return urlsafe_b64encode(kdf.derive(master_password.encode('utf-8')))

def generate_salt(length: int = 16) -> bytes:
    """Genera un salt aleatorio para PBKDF2HMAC."""
    return os.urandom(length)


# --- Cifrado / Descifrado Fernet ---

def encrypt_data_fernet(data: str, fernet_key: bytes) -> str:
    cipher = Fernet(fernet_key)
    return cipher.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_data_fernet(encrypted_data: str, fernet_key: bytes) -> str:
    cipher = Fernet(fernet_key)
    return cipher.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')


# --- Generación de Contraseñas Fuertes ---

def generate_strong_password(length: int = 12,
                              use_uppercase: bool = True,
                              use_lowercase: bool = True,
                              use_digits: bool = True,
                              use_symbols: bool = True) -> str:
    characters = ""
    if use_lowercase:
        characters += "abcdefghijklmnopqrstuvwxyz"
    if use_uppercase:
        characters += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if use_digits:
        characters += "0123456789"
    if use_symbols:
        characters += "!@#$%^&*()-_+=[]{}|;:,.<>?"

    if not characters:
        raise ValueError("Debe seleccionar al menos un tipo de caracter para la contraseña.")

    password = ''.join(secrets.choice(characters) for _ in range(length))
    logger.debug(f"Contraseña fuerte generada con longitud {length}")
    return password


# --- TOTP ---

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code)