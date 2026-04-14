# core/autenticacion
import getpass
from Modelo.models import AdminUser
# Importar las nuevas funciones de seguridad
from core.seguridad import hash_password_bcrypt, check_password_bcrypt, generate_totp_secret, \
                        generate_salt, generate_fernet_key_from_password
from core.almacenamiento import save_jsonD, load_json_data
from base64 import urlsafe_b64encode, urlsafe_b64decode # Necesario para codificar/decodificar el salt

UserPrincipal = "DBusers.json"

# Funcion para generar usuario y Contraseña Principal
def generar_Admin():
    """
    Gestiona la creación inicial del usuario administrador y su contraseña 2FA.
    Ahora incluye la generación y almacenamiento del salt para la clave Fernet.
    """
    user_data = load_json_data(UserPrincipal)

    if user_data is None:
        print("Creando nuevo usuario administrador...")
        nombre_admin = input("Ingrese su nombre de usuario: ")
        password = getpass.getpass("Ingrese su contraseña maestra: ")
        
        hashed_password = hash_password_bcrypt(password)
        # --- NUEVO: Generar y almacenar el salt para la derivación de clave Fernet ---
        fernet_salt_bytes = generate_salt() # Genera bytes
        # Guardamos el salt como string base64 en el JSON
        fernet_salt_str = urlsafe_b64encode(fernet_salt_bytes).decode('utf-8')

        # Generar secreto TOTP
        totp_secret = generate_totp_secret()

        nuevo_admin = AdminUser(
            username=nombre_admin,
            password=hashed_password,
            totp_secret=totp_secret,
            fernet_key_salt=fernet_salt_str # Guardamos el salt aquí
        )

        save_jsonD(UserPrincipal, nuevo_admin.model_dump())
        print(f"Usuario administrador '{nombre_admin}' creado correctamente con TOTP y seguridad Fernet mejorada.")
        print(f"Secreto TOTP: {totp_secret}")
    else:
        print(f"El archivo de usuario maestro ya existe.")

def autenticar_admin() -> tuple[AdminUser | None, bytes | None]:
    """
    Intenta autenticar al usuario administrador y, si tiene éxito, deriva
    y retorna la clave Fernet para la sesión.
    Retorna una tupla (AdminUser, fernet_key_bytes) si la autenticación es exitosa,
    (None, None) en caso contrario.
    """
    user_data = load_json_data(UserPrincipal)

    if user_data is None:
        print("No se encontró un usuario administrador. Por favor, créelo primero.")
        return None, None
    
    admin_user = AdminUser(**user_data)

    nombre_ingresado = input("Ingrese su nombre de usuario: ")
    password_ingresada = getpass.getpass("Ingrese su contraseña maestra: ")

    if nombre_ingresado == admin_user.username and \
       check_password_bcrypt(password_ingresada, admin_user.password):
        print("¡Autenticación de contraseña maestra exitosa!")
        
        # --- NUEVO: Derivar la clave Fernet ---
        try:
            # Decodificar el salt de string a bytes
            fernet_salt_bytes = urlsafe_b64decode(admin_user.fernet_key_salt)
            # Derivar la clave Fernet usando la contraseña ingresada y el salt guardado
            fernet_key_for_session = generate_fernet_key_from_password(password_ingresada, fernet_salt_bytes)
            print("Clave Fernet derivada exitosamente para la sesión.")
            return admin_user, fernet_key_for_session
        except Exception as e:
            print(f"Error al derivar la clave Fernet: {e}")
            print("Puede que el archivo de usuario esté corrupto o el salt no sea válido.")
            return None, None
    else:
        print("Usuario o contraseña maestra incorrectos.")
        return None, None