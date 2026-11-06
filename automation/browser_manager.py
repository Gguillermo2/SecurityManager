# automation/browser_manager.py
"""
Apertura y administración de navegadores mediante Playwright.

Diseñado para Chromium y sus derivados (Brave, Chrome, Edge). La estructura
permite añadir Firefox sin cambiar la lógica de automatización.

Playwright se importa de forma diferida para que la aplicación PySide6 pueda
arrancar aunque Playwright no esté instalado.
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple

from automation.errors import BrowserLaunchError

if TYPE_CHECKING:  # pragma: no cover - solo para tipado
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

_WINDOWS = sys.platform.startswith("win")
_MACOS = sys.platform == "darwin"


@dataclass(frozen=True)
class BrowserOption:
    """Descriptor de un navegador soportado."""

    key: str
    label: str
    engine: str  # "chromium" | "firefox"
    channel: Optional[str] = None
    executable_paths: Tuple[str, ...] = ()


BROWSER_OPTIONS: Tuple[BrowserOption, ...] = (
    BrowserOption(
        key="brave",
        label="Brave",
        engine="chromium",
        channel="brave",
        executable_paths=(
            r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "brave-browser",
            "brave",
        ),
    ),
    BrowserOption(
        key="chrome",
        label="Google Chrome",
        engine="chromium",
        channel="chrome",
        executable_paths=(
            r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
            r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
        ),
    ),
    BrowserOption(
        key="edge",
        label="Microsoft Edge",
        engine="chromium",
        channel="msedge",
        executable_paths=(
            r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe",
            r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "microsoft-edge",
            "microsoft-edge-stable",
        ),
    ),
    BrowserOption(
        key="chromium",
        label="Chromium (Playwright)",
        engine="chromium",
    ),
    BrowserOption(
        key="firefox",
        label="Firefox (Playwright)",
        engine="firefox",
    ),
)

_OPTIONS_BY_KEY: Dict[str, BrowserOption] = {
    option.key: option for option in BROWSER_OPTIONS
}

# Orden de preferencia para la opción "automático".
_AUTO_ORDER: Sequence[str] = ("brave", "chrome", "edge", "chromium")


def _expand_candidate(path: str) -> Optional[str]:
    """Expande variables de entorno y resuelve binarios del PATH."""
    expanded = os.path.expandvars(os.path.expanduser(path))
    if os.path.isabs(expanded):
        return expanded if os.path.isfile(expanded) else None
    return shutil.which(expanded)


def resolve_executable(option: BrowserOption) -> Optional[str]:
    """Devuelve la primera ruta existente del navegador, si la hay."""
    for candidate in option.executable_paths:
        resolved = _expand_candidate(candidate)
        if resolved:
            return resolved
    return None


class BrowserSession:
    """Sesión activa de navegador que se mantiene abierta para el usuario."""

    def __init__(
        self,
        playwright: "Playwright",
        browser: "Browser",
        context: "BrowserContext",
        option: BrowserOption,
    ):
        self._playwright = playwright
        self._browser = browser
        self._context = context
        self.option = option
        self._closed = False

    @property
    def browser_key(self) -> str:
        return self.option.key

    @property
    def browser_label(self) -> str:
        return self.option.label

    def new_page(self) -> "Page":
        return self._context.new_page()

    def is_open(self) -> bool:
        """True mientras el navegador siga conectado y con alguna pestaña."""
        if self._closed:
            return False
        try:
            if not self._browser.is_connected():
                return False
            return len(self._context.pages) > 0
        except Exception:
            return False

    def close(self) -> None:
        """Cierra contexto, navegador y driver sin propagar errores."""
        if self._closed:
            return
        self._closed = True
        for closer in (
            getattr(self._context, "close", None),
            getattr(self._browser, "close", None),
            getattr(self._playwright, "stop", None),
        ):
            if closer is None:
                continue
            try:
                closer()
            except Exception:
                logger.debug("Error cerrando recurso de navegador", exc_info=False)


class BrowserManager:
    """
    Inicia un navegador visible y devuelve una `BrowserSession`.

    Importante: usa la API síncrona de Playwright, por lo que debe ejecutarse
    en un hilo de trabajo (QThread), nunca en el hilo de la interfaz.
    """

    def __init__(
        self,
        headless: bool = False,
        timeout_ms: int = 30_000,
        slow_mo_ms: int = 0,
    ):
        self.headless = headless
        self.timeout_ms = max(1_000, timeout_ms)
        self.slow_mo_ms = max(0, slow_mo_ms)

    @staticmethod
    def available_options() -> List[Tuple[str, str]]:
        """Lista (clave, etiqueta) para poblar la interfaz."""
        return [(option.key, option.label) for option in BROWSER_OPTIONS]

    def start(self, browser_key: str = "auto") -> BrowserSession:
        """
        Abre el navegador solicitado.

        Para Brave/Chrome/Edge se intenta primero el `channel` de Playwright y,
        si no está disponible, se usa la ruta del ejecutable instalado.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserLaunchError(
                "Playwright no está instalado. Ejecuta:\n"
                "  pip install playwright\n"
                "  python -m playwright install chromium"
            ) from exc

        candidates = self._resolve_candidates(browser_key)
        playwright = None
        errors: List[str] = []

        try:
            playwright = sync_playwright().start()
            for option in candidates:
                try:
                    browser = self._launch_engine(playwright, option)
                    context = browser.new_context(ignore_https_errors=False)
                    context.set_default_timeout(self.timeout_ms)
                    context.set_default_navigation_timeout(self.timeout_ms)

                    logger.info(
                        "Navegador iniciado: %s (headless=%s)",
                        option.label,
                        self.headless,
                    )
                    return BrowserSession(
                        playwright=playwright,
                        browser=browser,
                        context=context,
                        option=option,
                    )
                except Exception as exc:
                    errors.append(f"{option.label}: {type(exc).__name__}")
                    logger.debug(
                        "No se pudo iniciar %s: %s",
                        option.label,
                        type(exc).__name__,
                    )
        except BrowserLaunchError:
            raise
        except Exception as exc:
            errors.append(type(exc).__name__)
            logger.error(
                "Error iniciando Playwright: %s", type(exc).__name__, exc_info=True
            )

        if playwright is not None:
            try:
                playwright.stop()
            except Exception:
                pass

        detail = ", ".join(errors) if errors else "sin detalles"
        raise BrowserLaunchError(
            "No se pudo iniciar ningún navegador compatible. "
            "Instala Brave, Google Chrome o Microsoft Edge, o ejecuta "
            "'python -m playwright install chromium'.\n"
            f"Intentos: {detail}"
        )

    # -------------------- Internos --------------------

    @staticmethod
    def _resolve_candidates(browser_key: str) -> List[BrowserOption]:
        key = (browser_key or "auto").strip().lower()
        if key == "auto":
            return [_OPTIONS_BY_KEY[name] for name in _AUTO_ORDER]
        option = _OPTIONS_BY_KEY.get(key)
        if option is None:
            raise BrowserLaunchError(
                f"Navegador no soportado: {browser_key!r}. "
                f"Opciones: auto, {', '.join(_OPTIONS_BY_KEY)}."
            )
        return [option]

    def _launch_engine(self, playwright: "Playwright", option: BrowserOption) -> "Browser":
        engine = getattr(playwright, option.engine)
        launch_kwargs = {"headless": self.headless}
        if self.slow_mo_ms:
            launch_kwargs["slow_mo"] = self.slow_mo_ms

        executable = resolve_executable(option)

        # 1) Canal oficial de Playwright (Chrome/Edge y, si existe, Brave).
        if option.channel:
            try:
                return engine.launch(channel=option.channel, **launch_kwargs)
            except Exception as exc:
                logger.debug(
                    "Canal '%s' no disponible (%s); probando ejecutable.",
                    option.channel,
                    type(exc).__name__,
                )

        # 2) Ejecutable instalado detectado en el sistema.
        if executable:
            return engine.launch(executable_path=executable, **launch_kwargs)

        # 3) Navegador incluido por Playwright (requiere `playwright install`).
        return engine.launch(**launch_kwargs)
