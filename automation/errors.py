# automation/errors.py
"""Excepciones seguras del módulo de automatización.

Los mensajes de estas excepciones están pensados para mostrarse al usuario:
nunca deben contener credenciales ni fragmentos del DOM.
"""


class AutomationError(Exception):
    """Error controlado durante la automatización."""


class AutomationCancelled(AutomationError):
    """El usuario canceló la automatización."""


class FormNotFoundError(AutomationError):
    """No se encontró el formulario esperado en la página autorizada."""


class BrowserLaunchError(AutomationError):
    """No se pudo iniciar el navegador solicitado."""
