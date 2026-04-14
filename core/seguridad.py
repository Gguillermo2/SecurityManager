import os
import bcrypt
import random
import pyotp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode

RUTA_DBWROSER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "DBwroser")

# --- Funciones de Hashing con BCrypt (para la contraseña maestra del usuario)
def hash_password_bcrypt(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    """
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password_bcrypt(password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña en texto plano contra un hash de bcrypt.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- Gestión del directorio de la "DB"
def _ensure_db_directory_exists():
    """Asegura que el directorio DBwroser exista."""
    if not os.path.exists(RUTA_DBWROSER):
        os.makedirs(RUTA_DBWROSER)

# --- Derivación de Clave Fernet usando PBKDF2HMAC
def generate_fernet_key_from_password(master_password: str, salt: bytes) -> bytes:
    """
    Deriva una clave Fernet a partir de una contraseña maestra y un salt usando PBKDF2HMAC.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # Fernet keys are 32 bytes (256 bits)
        salt=salt,
        iterations=480000, 
        backend=default_backend()
    )
    key = urlsafe_b64encode(kdf.derive(master_password.encode('utf-8')))
    return key

def generate_salt(length: int = 16) -> bytes:
    """
    Genera un salt aleatorio para PBKDF2HMAC. Este salt debe ser almacenado
    junto con el usuario maestro (no secreto, pero único por usuario).
    """
    return os.urandom(length)

# --- Funciones de Cifrado y Descifrado con Fernet (ahora necesitan la clave activa)
def encrypt_data_fernet(data: str, fernet_key: bytes) -> str:
    """
    Cifra una cadena de texto usando Fernet y la clave derivada.
    Retorna la cadena cifrada (base64).
    """
    cipher = Fernet(fernet_key)
    return cipher.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_data_fernet(encrypted_data: str, fernet_key: bytes) -> str:
    """
    Descifra una cadena cifrada con Fernet usando la clave derivada.
    Retorna la cadena original.
    """
    cipher = Fernet(fernet_key)
    return cipher.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')

# --- Generación de Contraseñas Fuertes
def generate_strong_password(length: int = 12,
                             use_uppercase: bool = True,
                             use_lowercase: bool = True,
                             use_digits: bool = True,
                             use_symbols: bool = True) -> str:
    """
    Genera una contraseña fuerte con caracteres seleccionados.
    """
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

    password = ''.join(random.choice(characters) for i in range(length))
    return password

# --- Funciones TOTP
def generate_totp_secret():
    return pyotp.random_base32()

def verify_totp(secret, code):
    return pyotp.TOTP(secret).verify(code)

