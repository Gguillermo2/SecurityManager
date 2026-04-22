# Controladores/home_controller.py
from typing import List, Optional
from datetime import datetime

from Modelo.models import AdminUser, Account
from core.account_manager import AccountManager
from core.session import SessionManager


class HomeController:
    """Controlador que maneja toda la lógica de negocio de la ventana principal"""

    def __init__(self, admin_user: AdminUser, fernet_key: bytes):
        self.admin_user: AdminUser = admin_user
        self.fernet_key: bytes = fernet_key

        # Managers
        self.session_manager = SessionManager()
        self.account_manager = AccountManager(fernet_key)

        # Estado
        self.selected_account: Optional[Account] = None

        # Iniciar sesión
        self.session_manager.start_session(admin_user, fernet_key)

    # ====================== Gestión de Cuentas ======================

    def get_filtered_accounts(self, search: str = "", category: str = "Todas") -> List[Account]:
        return self.account_manager.get_filtered_accounts(search=search, category=category)

    def get_all_categories(self) -> List[str]:
        return self.account_manager.get_all_categories()

    def get_account_by_id(self, account_id: str) -> Optional[Account]:
        return self.account_manager.get_account_by_id(account_id)

    def create_account(self, platform: str, email_or_username: str, 
                        password: str, category: str, notes: str = "") -> Account:
        return self.account_manager.create_account(
            platform=platform,
            email_or_username=email_or_username,
            password=password,
            category=category,
            notes=notes
        )

    def update_account(self, platform: str, account_id: str, email_or_username: Optional[str] = None,
                        password: Optional[str] = None, category: Optional[str] = None,
                        notes: Optional[str] = None) -> bool:
        return self.account_manager.update_account(
            platform=platform,
            account_id=account_id,
            email_or_username=email_or_username,
            password=password,
            category=category,
            notes=notes
        )

    def delete_account(self, account_id: str) -> bool:
        success = self.account_manager.delete_account(account_id)
        if success:
            self.selected_account = None
        return success

    def get_decrypted_password(self, account_id: str) -> str:
        return self.account_manager.get_decrypted_password(account_id)

    def suggest_strong_password(self, length: int = 16) -> str:
        return self.account_manager.suggest_strong_password(length)

    def get_accounts_summary(self) -> dict:
        return self.account_manager.get_accounts_summary()

    # ====================== Estado ======================

    def select_account(self, account_id: str) -> Optional[Account]:
        self.selected_account = self.get_account_by_id(account_id)
        return self.selected_account

    def get_selected_account(self) -> Optional[Account]:
        return self.selected_account

    # ====================== Sesión ======================

    def is_session_valid(self) -> bool:
        return self.session_manager.is_session_valid()

    def refresh_user_activity(self):
        """Refresca la sesión cuando el usuario realiza una actividad en la UI."""
        if self.session_manager.current_user:
            self.session_manager.refresh_session()

    def logout(self):
        self.session_manager.end_session()

    # ====================== Utilidades ======================

    def refresh_data(self):
        """Fuerza la recarga de datos desde almacenamiento"""
        self.account_manager.load_accounts()