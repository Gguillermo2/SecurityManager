# Controladores/home_controller.py
from typing import List, Optional, Tuple
from datetime import datetime

from Modelo.models import AdminUser, Account
from core.account_manager import AccountManager
from core.session import SessionManager
from automation.automation_service import AutomationService
from automation.errors import AutomationError
from automation.platform_config import PlatformConfig


class HomeController:
    """Controlador que maneja toda la lógica de negocio de la ventana principal"""

    def __init__(self, admin_user: AdminUser, fernet_key: bytes):
        self.admin_user: AdminUser = admin_user
        self.fernet_key: bytes = fernet_key

        # Managers
        self.session_manager = SessionManager()
        self.account_manager = AccountManager(fernet_key)
        self.automation_service = AutomationService(self.account_manager)

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

    def logout(self):
        self.automation_service.shutdown()
        self.session_manager.end_session()

    # ====================== Automatización web ======================
    # El controlador solo delega en AutomationService. La lógica de
    # Playwright permanece aislada en el paquete `automation`.

    def get_platform_configs(self, enabled_only: bool = False) -> List[PlatformConfig]:
        return self.automation_service.list_configs(enabled_only=enabled_only)

    def get_platform_config_for_account(self, account: Account) -> Optional[PlatformConfig]:
        return self.automation_service.find_config_for_account(account)

    def get_platform_config(self, config_id: str) -> Optional[PlatformConfig]:
        return self.automation_service.get_config(config_id)

    def save_platform_config(self, config: PlatformConfig) -> PlatformConfig:
        return self.automation_service.save_config(config)

    def delete_platform_config(self, config_id: str) -> bool:
        return self.automation_service.delete_config(config_id)

    def get_browser_options(self) -> List[Tuple[str, str]]:
        return self.automation_service.browser_options()

    def start_automated_login(self, account: Account,
                              browser_key: str = "auto") -> bool:
        """Inicia el rellenado automático del formulario en segundo plano."""
        if not self.is_session_valid():
            raise AutomationError(
                "La sesión ha expirado. Inicia sesión nuevamente para "
                "automatizar el acceso."
            )
        return self.automation_service.start_login(account, browser_key)

    def stop_automation(self):
        self.automation_service.stop()

    def is_automation_running(self) -> bool:
        return self.automation_service.is_running()

    def shutdown_automation(self):
        self.automation_service.shutdown()

    # ====================== Utilidades ======================

    def refresh_data(self):
        """Fuerza la recarga de datos desde almacenamiento"""
        self.account_manager.load_accounts()