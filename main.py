# main.py
import sys
from PySide6.QtWidgets import QApplication

from core.logging_config import configure_logging
from core.almacenamiento import initialize_database
from Vista.login import start_login
from Vista.home import start_home


def on_login_success(admin_user, fernet_key):
    """Callback que recibe el controlador de login cuando la auth es exitosa."""
    start_home(admin_user, fernet_key)


def main():
    configure_logging()
    initialize_database()   # Crea las tablas SQLite si no existen

    app = QApplication(sys.argv)
    app.setApplicationName("GestorWroser")

    # Fuente base
    font = app.font()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)

    login_window = start_login(on_login_success)
    login_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()