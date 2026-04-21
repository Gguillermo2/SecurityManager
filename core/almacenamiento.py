# core/almacenamiento.py
import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from Modelo.models import Account

logger = logging.getLogger(__name__)

# Obtener directorio de AppData
def get_appdata_dir():
    """Obtiene el directorio de la aplicación en AppData"""
    appdata = os.getenv('APPDATA')
    if not appdata:
        appdata = os.path.expanduser('~')
    
    app_dir = Path(appdata) / "GestorDeCuentasWroser"
    app_dir.mkdir(exist_ok=True)
    return app_dir

# Configurar rutas
RUTA_DBWROSER = get_appdata_dir()
PASSWORDS_DATA_FILE = "passwords_data.json"

def ensure_db_directory():
    """Asegura que el directorio de la base de datos exista (en AppData)"""
    RUTA_DBWROSER.mkdir(exist_ok=True)
    return True

def save_jsonD(filename: str, data: dict):
    """
    Guarda datos en un archivo JSON en el directorio DBwroser (AppData).
    """
    ensure_db_directory()
    full_path = RUTA_DBWROSER / filename
    try:
        with open(full_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        logger.info(f"Datos guardados correctamente en {filename}")
        print(f"✅ Datos guardados correctamente en {filename}") 
    except IOError as e:
        logger.error(f"Error al guardar datos en {full_path}: {str(e)}", exc_info=True)
        print(f"❌ Error al guardar datos en {full_path}: {e}")

def load_json_data(filename: str) -> Optional[Dict]:
    """Carga datos de un archivo JSON desde DBwroser (AppData)."""
    full_path = RUTA_DBWROSER / filename
    if full_path.exists():
        try:
            with open(full_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON de {full_path}: {str(e)}", exc_info=True)
            print(f"❌ Error al decodificar JSON de {full_path}: {e}")
            return None
        except IOError as e:
            logger.error(f"Error al cargar datos de {full_path}: {str(e)}", exc_info=True)
            print(f"❌ Error al cargando datos de {full_path}: {e}")
            return None
    return None   

def save_accounts_data(accounts: List[Account]):
    """
    Guarda los datos de las cuentas en el archivo JSON.
    Se asume que las contraseñas ya están cifradas en memoria.
    """
    ensure_db_directory()
    accounts_data = []
    for account in accounts:
        account_dict = account.model_dump()
        accounts_data.append(account_dict)

    save_jsonD(PASSWORDS_DATA_FILE, {"accounts": accounts_data})
    print("✅ Cuentas guardadas exitosamente.")

def load_accounts_data() -> List[Account]:
    """
    Carga los datos de las cuentas desde el archivo JSON.
    No descifra las contraseñas aquí: quedan cifradas en memoria.
    """
    ensure_db_directory()

    data = load_json_data(PASSWORDS_DATA_FILE)
    if not data or "accounts" not in data:
        print("ℹ️  No se encontraron datos de cuentas.")
        return []

    loaded_accounts = []
    for account_dict in data.get("accounts", []):
        if account_dict.get('password') is None:
            print(f"⚠️  Contraseña vacía para: {account_dict.get('platform', 'Desconocida')}")
            continue
        loaded_accounts.append(Account(**account_dict))

    print(f"✅ {len(loaded_accounts)} cuenta(s) cargadas exitosamente.")
    return loaded_accounts