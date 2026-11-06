# automation/dom_inspector.py
"""
Inspección del DOM para localizar formularios de inicio de sesión.

Solo se buscan campos dentro de marcos cuyo host esté autorizado por la
configuración de la plataforma. No se resuelven CAPTCHA ni verificaciones
adicionales.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional, Sequence

from automation.errors import AutomationCancelled, FormNotFoundError
from automation.platform_config import (
    STRATEGY_AUTO,
    STRATEGY_CSS,
    STRATEGY_LABEL,
    STRATEGY_PLACEHOLDER,
    STRATEGY_ROLE,
    PlatformConfig,
    host_from_url,
)

if TYPE_CHECKING:  # pragma: no cover - solo para tipado
    from playwright.sync_api import Frame, Locator, Page

logger = logging.getLogger(__name__)

# Indicadores habituales de verificación adicional. Se informan al usuario,
# nunca se intentan resolver.
CHALLENGE_SELECTORS: Sequence[str] = (
    'iframe[src*="recaptcha"]',
    'iframe[src*="hcaptcha"]',
    'iframe[src*="turnstile"]',
    'iframe[src*="challenges.cloudflare.com"]',
    'input[name*="captcha" i]',
    'input[id*="captcha" i]',
    '[class*="captcha" i]',
    'input[autocomplete="one-time-code"]',
)

_STRATEGY_ORDER = (
    STRATEGY_CSS,
    STRATEGY_PLACEHOLDER,
    STRATEGY_LABEL,
    STRATEGY_ROLE,
)


@dataclass(frozen=True)
class LoginFields:
    """Campos localizados y el marco autorizado que los contiene."""

    frame: "Frame"
    frame_url: str
    username: Optional["Locator"] = None
    password: Optional["Locator"] = None


class DomInspector:
    """Localiza campos de login usando los selectores de la configuración."""

    def __init__(self, poll_interval_ms: int = 400):
        self.poll_interval_ms = max(100, poll_interval_ms)

    # -------------------- Búsqueda principal --------------------

    def wait_for_login_form(
        self,
        page: "Page",
        config: PlatformConfig,
        timeout_ms: int,
        require_password: bool = True,
        cancel_event: Optional[threading.Event] = None,
    ) -> LoginFields:
        """
        Espera hasta `timeout_ms` a que aparezca el formulario configurado.

        Con `require_password=False` se acepta un formulario en dos pasos:
        un campo de usuario dentro de un <form> y sin campo de contraseña.
        """
        deadline_ms = timeout_ms
        elapsed = 0

        while elapsed <= deadline_ms:
            if cancel_event is not None and cancel_event.is_set():
                raise AutomationCancelled("Automatización cancelada por el usuario.")

            fields = self.find_login_form(
                page, config, require_password=require_password
            )
            if fields is not None:
                return fields

            if elapsed >= deadline_ms:
                break
            page.wait_for_timeout(self.poll_interval_ms)
            elapsed += self.poll_interval_ms

        if require_password:
            raise FormNotFoundError(
                "No se encontró el formulario de inicio de sesión configurado "
                "para esta plataforma."
            )
        raise FormNotFoundError(
            "No se encontró el campo de usuario configurado para esta plataforma."
        )

    def find_login_form(
        self,
        page: "Page",
        config: PlatformConfig,
        require_password: bool = True,
    ) -> Optional[LoginFields]:
        """Busca los campos en el marco principal y en marcos autorizados."""
        for frame in self._candidate_frames(page, config):
            try:
                username = self._find_field(
                    frame, config.username_selectors, config.strategy
                )
                password = self._find_field(
                    frame, config.password_selectors, config.strategy
                )
            except Exception as exc:  # DOM cambiante o marco destruido
                logger.debug("Error inspeccionando marco: %s", type(exc).__name__)
                continue

            if username is None:
                continue
            if password is None:
                if require_password:
                    continue
                # Formulario en dos pasos: solo se acepta si el usuario está
                # dentro de un <form> (evita rellenar buscadores u otros campos).
                if not self._is_inside_form(username):
                    continue
                return LoginFields(
                    frame=frame,
                    frame_url=self._safe_frame_url(frame),
                    username=username,
                    password=None,
                )

            # Con usuario y contraseña configurados y visibles, se considera un
            # formulario de login fiable (muchas SPA no usan <form>).
            return LoginFields(
                frame=frame,
                frame_url=self._safe_frame_url(frame),
                username=username,
                password=password,
            )
        return None

    # -------------------- Marcos --------------------

    def _candidate_frames(
        self, page: "Page", config: PlatformConfig
    ) -> List["Frame"]:
        try:
            frames = list(page.frames)
        except Exception:
            frames = []
        try:
            main_frame = page.main_frame
        except Exception:
            main_frame = frames[0] if frames else None

        ordered: List["Frame"] = []
        if main_frame is not None:
            ordered.append(main_frame)
        ordered.extend(frame for frame in frames if frame is not main_frame)

        return [frame for frame in ordered if self._frame_allowed(frame, config)]

    @staticmethod
    def _frame_allowed(frame: "Frame", config: PlatformConfig) -> bool:
        """
        Un marco solo es apto si su host está autorizado.

        Los marcos `about:blank`/`about:srcdoc` se permiten porque no tienen
        un origen externo propio; cualquier marco http(s) debe coincidir de
        forma exacta con el dominio configurado.
        """
        url = DomInspector._safe_frame_url(frame)
        if not url:
            return False
        if url.startswith(("about:blank", "about:srcdoc")):
            return True
        if url.startswith(("http://", "https://")):
            return config.allows_url(url)
        return False

    @staticmethod
    def _safe_frame_url(frame: "Frame") -> str:
        try:
            return frame.url or ""
        except Exception:
            return ""

    # -------------------- Campos --------------------

    def _find_field(
        self, frame: "Frame", selectors: Iterable[str], strategy: str
    ) -> Optional["Locator"]:
        strategies = (
            _STRATEGY_ORDER if strategy == STRATEGY_AUTO else (strategy,)
        )

        for current in strategies:
            for selector in selectors:
                locator = self._build_locator(frame, selector, current)
                if locator is None:
                    continue
                if self._is_usable(locator):
                    return locator

        # Último recurso: si la estrategia configurada no era CSS, se intenta
        # interpretar el mismo selector como CSS (los selectores suelen ser CSS).
        if strategy != STRATEGY_CSS:
            for selector in selectors:
                locator = self._build_locator(frame, selector, STRATEGY_CSS)
                if locator is not None and self._is_usable(locator):
                    return locator
        return None

    @staticmethod
    def _build_locator(
        frame: "Frame", selector: str, strategy: str
    ) -> Optional["Locator"]:
        try:
            if strategy == STRATEGY_LABEL:
                return frame.get_by_label(selector)
            if strategy == STRATEGY_PLACEHOLDER:
                return frame.get_by_placeholder(selector)
            if strategy == STRATEGY_ROLE:
                return frame.get_by_role("textbox", name=selector)
            return frame.locator(selector)
        except Exception:
            return None

    @staticmethod
    def _is_usable(locator: "Locator") -> bool:
        """Comprueba que el localizador apunte a un campo visible y editable."""
        try:
            if locator.count() == 0:
                return False
            first = locator.first
            return first.is_visible() and first.is_editable()
        except Exception:
            return False

    @staticmethod
    def _is_inside_form(locator: "Locator") -> bool:
        try:
            return locator.locator("xpath=ancestor::form").count() > 0
        except Exception:
            return False

    # -------------------- Diagnóstico seguro --------------------

    @staticmethod
    def detect_challenge(page: "Page") -> bool:
        """Detecta CAPTCHA/TOTP visibles. No intenta resolverlos."""
        for selector in CHALLENGE_SELECTORS:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except Exception:
                continue
        return False

    @staticmethod
    def describe_page(page: "Page") -> dict:
        """
        Devuelve información no sensible de la página para logs/diagnóstico.

        No incluye HTML, valores de campos ni credenciales.
        """
        info = {"url": "", "host": "", "title": "", "frames": 0}
        try:
            url = page.url or ""
            info["url"] = url
            info["host"] = host_from_url(url) or ""
        except Exception:
            pass
        try:
            info["title"] = (page.title() or "")[:120]
        except Exception:
            pass
        try:
            info["frames"] = len(page.frames)
        except Exception:
            pass
        return info
