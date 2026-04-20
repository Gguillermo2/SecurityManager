# core/account_manager.py
from typing import List, Optional, Dict
from datetime import datetime
import logging
from Modelo.models import Account
from core.almacenamiento import save_accounts_data, load_accounts_data
from core.seguridad import generate_strong_password, encrypt_data_fernet, decrypt_data_fernet

logger = logging.getLogger(__name__)


class AccountManager:
    """Gestor CRUD para las cuentas de usuario"""

    def __init__(self, fernet_key: bytes):
        self.fernet_key = fernet_key
        self.accounts: List[Account] = []
        self.load_accounts()

    def load_accounts(self):
        """Carga todas las cuentas desde el almacenamiento"""
        self.accounts = load_accounts_data() or []

    def save_all_accounts(self):
        """Guarda todas las cuentas en el almacenamiento"""
        save_accounts_data(self.accounts)

    def create_account(self, platform: str, email_or_username: str, 
                        password: str, category: str = "General", notes: str = "") -> Account:
        """Crea y guarda una nueva cuenta"""
        encrypted_password = encrypt_data_fernet(password, self.fernet_key)

        new_account = Account(
            platform=platform.strip(),
            email_or_username=email_or_username.strip(),
            password=encrypted_password,
            category=category.strip(),
            notes=notes.strip(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self.accounts.append(new_account)
        self.save_all_accounts()
        return new_account

    def get_account_by_id(self, account_id: str) -> Optional[Account]:
        return next((acc for acc in self.accounts if str(acc.id) == str(account_id)), None)

    def update_account(self, account_id: str, **kwargs) -> bool:
        """Actualiza una cuenta (acepta campos parciales)"""
        account = self.get_account_by_id(account_id)
        if not account:
            return False

        # Cifrar contraseña si se está actualizando
        if 'password' in kwargs and kwargs['password'] is not None:
            kwargs['password'] = encrypt_data_fernet(kwargs['password'], self.fernet_key)

        updated = False
        for field, value in kwargs.items():
            if value is not None:
                setattr(account, field, value)
                updated = True

        if updated:
            account.updated_at = datetime.now().isoformat()
            self.save_all_accounts()

        return updated

    def delete_account(self, account_id: str) -> bool:
        """Elimina una cuenta"""
        account = self.get_account_by_id(account_id)
        if not account:
            return False

        self.accounts.remove(account)
        self.save_all_accounts()
        return True

    def get_decrypted_password(self, account_id: str) -> str:
        """Retorna la contraseña descifrada"""
        account = self.get_account_by_id(account_id)
        if not account or not account.password:
            logger.warning(f"Intento de desciframiento para cuenta no encontrada: {account_id}")
            return ""

        try:
            return decrypt_data_fernet(account.password, self.fernet_key)
        except Exception as e:
            logger.error(f"Error al descifrar contraseña para cuenta {account_id}: {str(e)}", exc_info=True)
            return "[Error al descifrar]"

    # ====================== Consultas ======================

    def get_filtered_accounts(self, search: str = "", category: str = "Todas") -> List[Account]:
        accounts = self.accounts.copy()

        if category and category != "Todas":
            accounts = [acc for acc in accounts if acc.category == category]

        if search:
            search = search.lower()
            accounts = [
                acc for acc in accounts
                if search in acc.platform.lower() or search in acc.email_or_username.lower()
            ]
        return accounts

    def get_all_categories(self) -> List[str]:
        categories = {acc.category for acc in self.accounts if acc.category}
        return sorted(["Todas"] + list(categories))

    def get_accounts_summary(self) -> dict:
        """Resumen para la barra de estado"""
        by_category = {}
        for cat in self.get_all_categories():
            if cat != "Todas":
                count = len([acc for acc in self.accounts if acc.category == cat])
                by_category[cat] = count

        return {
            'total': len(self.accounts),
            'by_category': by_category
        }

    def suggest_strong_password(self, length: int = 16) -> str:
        return generate_strong_password(
            length=length,
            use_uppercase=True,
            use_lowercase=True,
            use_digits=True,
            use_symbols=True
        )