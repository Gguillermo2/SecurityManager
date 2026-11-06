# automation/__init__.py
"""
Módulo de automatización de inicio de sesión con Playwright.

Componentes:
    browser_manager    → apertura y administración de navegadores.
    dom_inspector      → localización de campos del formulario.
    login_automation   → flujo de rellenado con validación de dominio.
    platform_config    → configuraciones por plataforma en SQLite.
    automation_service → integración con Qt/PySide6 y AccountManager.

Playwright se importa de forma diferida: la aplicación arranca aunque no esté
instalado, mostrando un error controlado al intentar automatizar.
"""

__all__ = [
    "automation_service",
    "browser_manager",
    "dom_inspector",
    "login_automation",
    "platform_config",
]
