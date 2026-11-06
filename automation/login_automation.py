# automation/login_automation.py
"""
Ejecución del proceso automatizado de inicio de sesión.

Flujo:
  1. Validar HTTPS y dominio exacto ANTES de abrir el navegador.
  2. Abrir el navegador visible.
  3. Navegar a la URL de login configurada.
  4. Revalidar el host tras posibles redirecciones.
  5. Localizar los campos con los selectores de la plataforma.
  6. Rellenar usuario y contraseña.
  7. Dejar el navegador abierto para que el usuario envíe el formulario y
     complete CAPTCHA/TOTP/2FA manualmente.

La automatización NUNCA envía el formulario ni resuelve verificaciones.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Callable, Optional

from automation.browser_manager import BrowserManager, BrowserSession
from automation.dom_inspector import DomInspector, LoginFields
from automation.errors import AutomationCancelled, AutomationError, FormNotFoundError
from automation.platform_config import PlatformConfig, host_from_url

logger = logging.getLogger(__name__)

StatusCallback = Optional[Callable[[str], None]]


@dataclass(frozen=True)
class AutomationResult:
    """Resultado seguro (sin credenciales) de una automatización correcta."""

    platform: str
    host: str
    browser: str
    username_filled: bool
    password_filled: bool
    challenge_detected: bool
    submit_selectors: int = 0


class LoginSession:
    """Navegador abierto tras rellenar el formulario."""

    def __init__(self, browser_session: BrowserSession, result: AutomationResult):
        self._browser_session = browser_session
        self.result = result

    @property
    def browser_label(self) -> str:
        return self._browser_session.browser_label

    def is_open(self) -> bool:
        return self._browser_session.is_open()

    def close(self) -> None:
        self._browser_session.close()


class LoginAutomation:
    """Orquesta la apertura del navegador y el rellenado del formulario."""

    def __init__(
        self,
        inspector: Optional[DomInspector] = None,
        timeout_ms: int = 30_000,
        headless: bool = False,
    ):
        self.inspector = inspector or DomInspector()
        self.timeout_ms = max(5_000, timeout_ms)
        self.headless = headless

    # -------------------- API pública --------------------

    def run(
        self,
        config: PlatformConfig,
        username: str,
        password: str,
        browser_key: str = "auto",
        status_cb: StatusCallback = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> LoginSession:
        """
        Abre el navegador y rellena el formulario.

        Devuelve una `LoginSession` con el navegador aún abierto. Lanza
        `AutomationError` (o subclases) si algo no se puede verificar.
        """
        self._emit(status_cb, f"Validando destino seguro: {config.domain}…")
        self._validate_target(config.login_url, config, "URL de inicio de sesión")
        if not username or not password:
            raise AutomationError(
                "La cuenta no tiene usuario o contraseña almacenados."
            )
        if cancel_event is not None and cancel_event.is_set():
            raise AutomationCancelled("Automatización cancelada por el usuario.")

        manager = BrowserManager(headless=self.headless, timeout_ms=self.timeout_ms)
        session: Optional[BrowserSession] = None

        try:
            self._emit(status_cb, "Abriendo el navegador…")
            session = manager.start(browser_key)
            self._emit(status_cb, f"Navegador abierto: {session.browser_label}")

            page = session.new_page()
            try:
                page.bring_to_front()
            except Exception:
                pass

            self._emit(status_cb, f"Navegando a {config.login_url}…")
            page.goto(
                config.login_url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms,
            )

            # Seguridad: una redirección no puede sacarnos del dominio autorizado.
            self._validate_target(page.url, config, "redirección del navegador")
            self._emit(
                status_cb,
                f"Dominio verificado: {host_from_url(page.url) or config.domain}",
            )

            self._emit(status_cb, "Buscando el formulario de inicio de sesión…")
            fields = self.inspector.wait_for_login_form(
                page,
                config,
                timeout_ms=self.timeout_ms,
                require_password=False,
                cancel_event=cancel_event,
            )

            username_filled = False
            password_filled = False

            if fields.username is not None:
                self._check_cancel(cancel_event)
                self._validate_fields_target(fields, config)
                fields.username.fill(username)
                username_filled = True

            # Formulario en dos pasos (usuario → contraseña).
            if fields.password is None:
                self._emit(
                    status_cb,
                    "Formulario en dos pasos detectado; esperando el campo de contraseña…",
                )
                fields = self.inspector.wait_for_login_form(
                    page,
                    config,
                    timeout_ms=self.timeout_ms,
                    require_password=True,
                    cancel_event=cancel_event,
                )
                self._check_cancel(cancel_event)
                self._validate_target(page.url, config, "página actual")
                self._validate_fields_target(fields, config)
                if fields.username is not None and not self._field_has_value(fields.username):
                    fields.username.fill(username)

            if fields.password is None:
                raise FormNotFoundError(
                    "No se encontró el campo de contraseña configurado."
                )

            # Última verificación justo antes de introducir la contraseña.
            self._check_cancel(cancel_event)
            self._validate_target(page.url, config, "página actual")
            self._validate_fields_target(fields, config)

            self._emit(status_cb, "Rellenando la contraseña…")
            fields.password.fill(password)
            password_filled = True

            if not self._field_has_value(fields.password):
                raise AutomationError(
                    "El campo de contraseña no aceptó el valor introducido."
                )

            try:
                fields.password.focus()
            except Exception:
                pass

            challenge = self.inspector.detect_challenge(page)
            page_info = self.inspector.describe_page(page)
            logger.info(
                "Formulario completado en %s (%s) con %s",
                page_info.get("host") or config.domain,
                config.name,
                session.browser_label,
            )

            if challenge:
                self._emit(
                    status_cb,
                    "Se detectó una verificación adicional (CAPTCHA/2FA). "
                    "Complétala manualmente en el navegador.",
                )
            self._emit(
                status_cb,
                "Formulario completado. Revisa los datos y pulsa el botón de "
                "inicio de sesión manualmente.",
            )

            result = AutomationResult(
                platform=config.name,
                host=page_info.get("host") or config.domain,
                browser=session.browser_label,
                username_filled=username_filled,
                password_filled=password_filled,
                challenge_detected=challenge,
                submit_selectors=len(config.submit_selectors),
            )
            return LoginSession(session, result)

        except AutomationError:
            if session is not None:
                session.close()
            raise
        except Exception as exc:
            if session is not None:
                session.close()
            safe_message = self._safe_error(exc, username, password)
            logger.error(
                "Error en la automatización de login: %s", type(exc).__name__
            )
            raise AutomationError(safe_message) from exc

    # -------------------- Seguridad --------------------

    @staticmethod
    def _validate_target(url: str, config: PlatformConfig, stage: str) -> None:
        """
        Exige HTTPS y coincidencia EXACTA de host antes de continuar.

        Se usa tanto para la URL configurada como para la URL final tras
        redirecciones y para el marco que contiene el formulario.
        """
        if not config.enabled:
            raise AutomationError("La configuración de esta plataforma está desactivada.")
        if not config.allows_url(url):
            raise AutomationError(
                f"{stage}: el destino no es HTTPS o no pertenece al dominio "
                f"autorizado ({config.domain}). Se canceló el rellenado."
            )

    def _validate_fields_target(
        self, fields: LoginFields, config: PlatformConfig
    ) -> None:
        if fields.frame_url and fields.frame_url.startswith(("http://", "https://")):
            self._validate_target(fields.frame_url, config, "marco del formulario")

    @staticmethod
    def _field_has_value(locator) -> bool:
        try:
            return bool(locator.input_value())
        except Exception:
            return True  # si no se puede leer, no se bloquea el flujo

    @staticmethod
    def _check_cancel(cancel_event: Optional[threading.Event]) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise AutomationCancelled("Automatización cancelada por el usuario.")

    @staticmethod
    def _safe_error(exc: Exception, username: str, password: str) -> str:
        """Construye un mensaje de error sin credenciales."""
        message = f"{type(exc).__name__}: {exc}"
        for secret in (password, username):
            if secret:
                message = message.replace(secret, "***")
        message = message[:300]
        return f"No se pudo completar la automatización. {message}"

    @staticmethod
    def _emit(callback: StatusCallback, message: str) -> None:
        logger.info(message)
        if callback is not None:
            try:
                callback(message)
            except Exception:
                logger.debug("Error en callback de estado", exc_info=False)
