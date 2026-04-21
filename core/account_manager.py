# core/account_manager.py
from typing import List, Optional, Dict
from datetime import datetime
import logging

from Modelo.models import Account
from core.almacenamiento import (
    initialize_database,
    save_account,
    update_account_db,
    delete_account_db,
    load_accounts_data,
    get_filtered_accounts_db,
    get_categories_db,
    get_accounts_summary_db,
    get_account_by_id_db,
)
from core.seguridad import generate_strong_password, encrypt_data_fernet, decrypt_data_fernet

logger = logging.getLogger(__name__)


class AccountManager:
    """
    Gestor CRUD para las cuentas de usuario.

    Con la migración a SQLite ya no se mantiene una lista en memoria:
    cada operación va directamente a la base de datos, lo que hace que
    el consumo de memoria sea mínimo y los filtros sean más rápidos.
    """

    def __init__(self, fernet_key: bytes):
        self.fernet_key = fernet_key
        initialize_database()   # garantiza que las tablas existen al arrancar

    # ====================== ESCRITURA ======================

    def create_account(self, platform: str, email_or_username: str,
                       password: str, category: str = "General",
                       notes: str = "") -> Account:
        """Cifra la contraseña e inserta la cuenta en SQLite."""
        encrypted_password = encrypt_data_fernet(password, self.fernet_key)
        now = datetime.now().isoformat()

        new_account = Account(
            platform=platform.strip(),
            email_or_username=email_or_username.strip(),
            password=encrypted_password,
            category=category.strip(),
            notes=notes.strip(),
            created_at=now,
            updated_at=now,
        )

        save_account(new_account)
        logger.info(f"Cuenta '{platform}' creada (id={new_account.id})")
        return new_account

    def update_account(self, account_id: str, **kwargs) -> bool:
        """
        Actualiza campos parciales de una cuenta.
        Si se pasa 'password', se cifra antes de guardar.
        """
        # Verificar que la cuenta existe
        account = get_account_by_id_db(account_id)
        if not account:
            logger.warning(f"update_account: cuenta no encontrada id={account_id}")
            return False

        fields: Dict = {}

        for field, value in kwargs.items():
            if value is None:
                continue
            if field == "password":
                fields["password"] = encrypt_data_fernet(value, self.fernet_key)
            else:
                fields[field] = value

        if not fields:
            return False

        fields["updated_at"] = datetime.now().isoformat()
        update_account_db(account_id, fields)
        logger.info(f"Cuenta id={account_id} actualizada: {list(fields.keys())}")
        return True

    def delete_account(self, account_id: str) -> bool:
        """Elimina la cuenta de la base de datos."""
        deleted = delete_account_db(account_id)
        if deleted:
            logger.info(f"Cuenta id={account_id} eliminada.")
        return deleted

    # ====================== LECTURA ======================

    def get_account_by_id(self, account_id: str) -> Optional[Account]:
        """Busca una cuenta por UUID directamente en SQLite."""
        return get_account_by_id_db(account_id)

    def get_filtered_accounts(self, search: str = "",
                               category: str = "Todas") -> List[Account]:
        """
        Devuelve cuentas filtradas por búsqueda y/o categoría.
        El filtrado ocurre en SQLite, no en Python.
        """
        return get_filtered_accounts_db(search=search, category=category)

    def get_all_categories(self) -> List[str]:
        """Retorna las categorías únicas existentes, precedidas por 'Todas'."""
        categories = get_categories_db()
        return ["Todas"] + categories

    def get_accounts_summary(self) -> dict:
        """Resumen para la barra de estado de la UI."""
        return get_accounts_summary_db()

    def get_decrypted_password(self, account_id: str) -> str:
        """Descifra y devuelve la contraseña de una cuenta."""
        account = get_account_by_id_db(account_id)
        if not account or not account.password:
            logger.warning(f"Contraseña no encontrada para id={account_id}")
            return ""
        try:
            return decrypt_data_fernet(account.password, self.fernet_key)
        except Exception as e:
            logger.error(f"Error al descifrar contraseña id={account_id}: {e}", exc_info=True)
            return "[Error al descifrar]"

    # ====================== UTILIDADES ======================

    def suggest_strong_password(self, length: int = 16) -> str:
        return generate_strong_password(
            length=length,
            use_uppercase=True,
            use_lowercase=True,
            use_digits=True,
            use_symbols=True,
        )

    # ====================== COMPATIBILIDAD (legacy) ======================
    # Estos métodos existían antes y son llamados por home_controller.
    # Se mantienen como alias para no romper nada.

    def load_accounts(self):
        """
        Anteriormente recargaba la lista en memoria.
        Con SQLite ya no es necesario, pero se conserva para compatibilidad
        con llamadas existentes en home_controller.refresh_data().
        """
        pass  # Sin-op: SQLite siempre lee el estado actual

    def save_all_accounts(self):
        """
        Anteriormente guardaba toda la lista en JSON.
        Con SQLite cada operación escribe de forma atómica; este método
        ya no hace nada pero se conserva por compatibilidad.
        """
        pass  # Sin-op