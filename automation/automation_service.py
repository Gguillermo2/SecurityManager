# automation/automation_service.py
"""
Integración entre la automatización Playwright y la aplicación PySide6.

- Recupera las credenciales exclusivamente desde `AccountManager`.
- Ejecuta Playwright en un QThread (nunca en el hilo de la interfaz).
- Expone señales Qt seguras (solo texto, nunca credenciales).
"""
from __future__ import annotations

import logging
import threading
from typing import List, Optional, Tuple

from PySide6.QtCore import QObject, QThread, Signal

from automation.browser_manager import BrowserManager
from automation.errors import AutomationError
from automation.login_automation import LoginAutomation, LoginSession
from automation.platform_config import (
    STRATEGIES,
    STRATEGY_LABELS,
    PlatformConfig,
    PlatformConfigRepository,
)
from Modelo.models import Account
from core.account_manager import AccountManager

logger = logging.getLogger(__name__)

_DECRYPT_ERROR_SENTINEL = "[Error al descifrar]"


class _LoginWorker(QThread):
    """Hilo de trabajo que ejecuta Playwright y mantiene el navegador abierto."""

    status = Signal(str)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        account_id: str,
        username: str,
        config: PlatformConfig,
        browser_key: str,
        password_provider,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._account_id = account_id
        self._username = username
        self._config = config
        self._browser_key = browser_key
        self._password_provider = password_provider
        self._cancel = threading.Event()

    def cancel(self) -> None:
        """Solicita el cierre ordenado del navegador."""
        self._cancel.set()

    def run(self) -> None:  # noqa: D401 - método de QThread
        session: Optional[LoginSession] = None
        password = ""
        try:
            password = self._password_provider(self._account_id) or ""
            if not password or password.startswith(_DECRYPT_ERROR_SENTINEL):
                raise AutomationError(
                    "No se pudo recuperar la contraseña de la cuenta. "
                    "Verifica que la sesión siga activa."
                )

            automation = LoginAutomation()
            session = automation.run(
                config=self._config,
                username=self._username,
                password=password,
                browser_key=self._browser_key,
                status_cb=self.status.emit,
                cancel_event=self._cancel,
            )

            result = session.result
            self.succeeded.emit(
                f"Formulario completado en {result.host} con {result.browser}. "
                "Envía el formulario manualmente en el navegador."
            )

            # Mantener el navegador abierto hasta que el usuario lo cierre o
            # solicite cerrarlo desde la aplicación.
            while not self._cancel.is_set() and session.is_open():
                self.msleep(400)

        except AutomationError as exc:
            if self._cancel.is_set():
                logger.info("Automatización cancelada por el usuario.")
            else:
                logger.warning(
                    "Automatización fallida (%s): %s",
                    self._config.name,
                    type(exc).__name__,
                )
                self.failed.emit(str(exc))
        except Exception:
            logger.exception(
                "Error inesperado en la automatización (%s)", self._config.name
            )
            self.failed.emit(
                "Error inesperado durante la automatización. "
                "Revisa los registros de la aplicación."
            )
        finally:
            password = ""
            self._password_provider = None
            if session is not None:
                try:
                    session.close()
                except Exception:
                    pass
            self.status.emit("Automatización finalizada.")


class AutomationService(QObject):
    """Fachada de automatización consumida por `HomeController`."""

    status_changed = Signal(str)
    login_ready = Signal(str)
    login_failed = Signal(str)
    browser_closed = Signal()

    def __init__(
        self,
        account_manager: AccountManager,
        repository: Optional[PlatformConfigRepository] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._account_manager = account_manager
        self.repository = repository or PlatformConfigRepository()
        self._worker: Optional[_LoginWorker] = None

    # -------------------- Plataformas --------------------

    @staticmethod
    def browser_options() -> List[Tuple[str, str]]:
        return [("auto", "Automático (recomendado)")] + BrowserManager.available_options()

    @staticmethod
    def strategy_options() -> List[Tuple[str, str]]:
        return [(strategy, STRATEGY_LABELS[strategy]) for strategy in STRATEGIES]

    def list_configs(self, enabled_only: bool = False) -> List[PlatformConfig]:
        return self.repository.list_configs(enabled_only=enabled_only)

    def get_config(self, config_id: str) -> Optional[PlatformConfig]:
        return self.repository.get(config_id)

    def find_config_for_account(self, account: Account) -> Optional[PlatformConfig]:
        return self.repository.find_for_platform(account.platform)

    def save_config(self, config: PlatformConfig) -> PlatformConfig:
        return self.repository.save(config)

    def delete_config(self, config_id: str) -> bool:
        return self.repository.delete(config_id)

    # -------------------- Estado --------------------

    def is_running(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    # -------------------- Ejecución --------------------

    def start_login(self, account: Account, browser_key: str = "auto") -> bool:
        """
        Lanza la automatización en un hilo aparte.

        La contraseña se descifra dentro del hilo de trabajo mediante
        `AccountManager.get_decrypted_password`, nunca en la interfaz.
        """
        if self.is_running():
            raise AutomationError(
                "Ya hay una automatización en curso. Ciérrala antes de iniciar otra."
            )

        config = self.find_config_for_account(account)
        if config is None:
            raise AutomationError(
                f"No hay una configuración de automatización para "
                f"'{account.platform}'. Añádela desde el gestor de plataformas."
            )
        if not config.enabled:
            raise AutomationError(
                f"La configuración de '{config.name}' está desactivada."
            )
        if not account.email_or_username:
            raise AutomationError("La cuenta no tiene usuario/email guardado.")

        worker = _LoginWorker(
            account_id=account.id,
            username=account.email_or_username,
            config=config,
            browser_key=browser_key,
            password_provider=self._account_manager.get_decrypted_password,
            parent=self,
        )
        worker.status.connect(self.status_changed)
        worker.succeeded.connect(self.login_ready)
        worker.failed.connect(self.login_failed)
        worker.finished.connect(self._on_worker_finished)

        self._worker = worker
        worker.start()
        return True

    def stop(self) -> None:
        """Solicita el cierre del navegador y detiene la automatización."""
        worker = self._worker
        if worker is not None and worker.isRunning():
            worker.cancel()

    def shutdown(self) -> None:
        """Cierre ordenado al salir de la aplicación."""
        worker = self._worker
        if worker is not None:
            worker.cancel()
            worker.wait(5_000)

    def _on_worker_finished(self) -> None:
        worker = self.sender()
        if worker is self._worker:
            self._worker = None
        if worker is not None:
            try:
                worker.deleteLater()
            except Exception:
                pass
        self.browser_closed.emit()
