# Vista/login.py
import io
import logging
import qrcode
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtGui import QPixmap, QImage, QFont, QIcon
from PySide6.QtCore import Qt, QSize

from controller.login_controller import LoginController
#from Controladores.login_controller import LoginController

logger = logging.getLogger(__name__)

# ─────────────────────────── QSS Global ────────────────────────────
LOGIN_QSS = """
    QMainWindow, QWidget#root {
        background-color: #1e1e1e;
    }
    QWidget#card {
        background-color: #252525;
        border-radius: 12px;
    }
    QLabel#title {
        color: #ffffff;
        font-size: 20px;
        font-weight: bold;
    }
    QLabel#subtitle {
        color: #aaaaaa;
        font-size: 12px;
    }
    QLabel#field_label {
        color: #aaaaaa;
        font-size: 12px;
    }
    QLineEdit {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3a3a3a;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 13px;
    }
    QLineEdit:focus {
        border: 1px solid #0d9488;
    }
    QPushButton#primary_btn {
        background-color: #0d9488;
        color: #ffffff;
        font-size: 13px;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 12px 24px;
    }
    QPushButton#primary_btn:hover  { background-color: #0f9f93; }
    QPushButton#primary_btn:pressed { background-color: #0a7a70; }
    QPushButton#link_btn {
        background: transparent;
        color: #0d9488;
        font-size: 12px;
        border: none;
        text-decoration: underline;
    }
    QPushButton#link_btn:hover { color: #0f9f93; }
    QLabel#totp_input_box {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3a3a3a;
        border-radius: 6px;
        font-size: 28px;
        font-weight: bold;
        letter-spacing: 8px;
    }
"""


# ══════════════════════════════════════════════════════════════════════
#  Función pública de entrada (compatible con main.py)
# ══════════════════════════════════════════════════════════════════════

def start_login(on_success_callback):
    """
    Punto de entrada desde main.py.
    Crea y muestra la ventana de login; on_success_callback(admin_user, fernet_key).
    """
    window = LoginWindow(on_success_callback)
    window.show()
    return window
# ══════════════════════════════════════════════════════════════════════
#  Ventana principal de Login
# ══════════════════════════════════════════════════════════════════════

class LoginWindow(QMainWindow):
    def __init__(self, on_success_callback):
        super().__init__()
        self.on_success = on_success_callback
        self.controller = LoginController()

        self.setWindowTitle("Gestor de Contraseñas – Login")
        self.setFixedSize(480, 620)
        self.setStyleSheet(LOGIN_QSS)

        # Widget raíz
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        self._root_layout = QVBoxLayout(root)
        self._root_layout.setContentsMargins(0, 0, 0, 0)

        # Decidir pantalla inicial
        if not self.controller.admin_exists():
            self._show_create_admin_screen()
        else:
            self._show_login_screen()

    # ──────────────────── helpers de layout ──────────────────────────

    def _clear_window(self):
        """Elimina todos los widgets del layout raíz."""
        while self._root_layout.count():
            item = self._root_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_card(self, parent_layout) -> tuple[QWidget, QVBoxLayout]:
        """Crea el panel central con bordes redondeados y lo agrega al layout."""
        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(40, 40, 40, 40)

        card = QWidget()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(14)

        wrapper.addStretch()
        wrapper.addWidget(card)
        wrapper.addStretch()

        container = QWidget()
        container.setLayout(wrapper)
        parent_layout.addWidget(container)
        return card, card_layout

    @staticmethod
    def _label(text: str, object_name: str = "field_label",
            alignment=Qt.AlignLeft) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName(object_name)
        lbl.setAlignment(alignment)
        return lbl

    @staticmethod
    def _field(placeholder: str = "", password: bool = False) -> QLineEdit:
        entry = QLineEdit()
        entry.setPlaceholderText(placeholder)
        if password:
            entry.setEchoMode(QLineEdit.Password)
        return entry

    @staticmethod
    def _primary_button(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("primary_btn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return btn

    # ──────────────────── PANTALLA CREAR ADMIN ───────────────────────

    def _show_create_admin_screen(self):
        self._clear_window()
        _, layout = self._make_card(self._root_layout)

        # Ícono y título
        layout.addWidget(self._label("🔐", "title", Qt.AlignCenter))
        layout.addWidget(self._label("Crear Administrador", "title", Qt.AlignCenter))
        layout.addWidget(self._label(
            "Configure su cuenta para comenzar",
            "subtitle", Qt.AlignCenter
        ))
        layout.addSpacing(10)

        # Campos
        layout.addWidget(self._label("Nombre de usuario"))
        self._ca_username = self._field("Ej: mi_usuario")
        layout.addWidget(self._ca_username)

        layout.addWidget(self._label("Contraseña maestra"))
        self._ca_password = self._field("Mínimo 8 caracteres", password=True)
        layout.addWidget(self._ca_password)

        layout.addSpacing(8)

        btn = self._primary_button("Crear cuenta y continuar")
        btn.clicked.connect(self._create_admin)
        layout.addWidget(btn)

        # Enter = submit
        self._ca_password.returnPressed.connect(self._create_admin)

    def _create_admin(self):
        username = self._ca_username.text().strip()
        password = self._ca_password.text().strip()

        success, message = self.controller.create_admin(username, password)
        if success:
            QMessageBox.information(self, "Cuenta creada", message)
            self._show_totp_qr(username)
        else:
            QMessageBox.critical(self, "Error", message)

    # ──────────────────── PANTALLA QR TOTP ───────────────────────────

    def _show_totp_qr(self, username: str):
        self._clear_window()
        _, layout = self._make_card(self._root_layout)

        layout.addWidget(self._label("Configurar Autenticador TOTP", "title", Qt.AlignCenter))
        layout.addWidget(self._label(
            "Escanee el QR con Google Authenticator, Authy u otra app compatible.",
            "subtitle", Qt.AlignCenter
        ))
        layout.addSpacing(10)

        uri = self.controller.get_totp_uri(username)
        if not uri:
            logger.error("URI TOTP vacío al intentar generar el QR.")
            QMessageBox.critical(self, "Error", "No se pudo generar el código QR.\nIntente de nuevo.")
            self._show_create_admin_screen()
            return

        # Generar imagen QR
        try:
            qr = qrcode.QRCode(version=1,
                               error_correction=qrcode.constants.ERROR_CORRECT_L,
                               box_size=6, border=4)
            qr.add_data(uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            bio = io.BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)

            qimage = QImage.fromData(bio.read())
            pixmap = QPixmap.fromImage(qimage).scaled(
                220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            qr_label = QLabel()
            qr_label.setPixmap(pixmap)
            qr_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(qr_label)

        except Exception as e:
            logger.error(f"Error al generar QR: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al generar código QR:\n{str(e)}")
            self._show_create_admin_screen()
            return

        # Clave manual
        secret = (self.controller.current_user.totp_secret
                if self.controller.current_user else "")
        layout.addWidget(self._label("O ingrese manualmente:", "field_label", Qt.AlignCenter))
        secret_lbl = QLabel(secret)
        secret_lbl.setObjectName("subtitle")
        secret_lbl.setAlignment(Qt.AlignCenter)
        secret_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(secret_lbl)

        layout.addSpacing(8)
        btn = self._primary_button("Continuar al Login →")
        btn.clicked.connect(self._show_login_screen)
        layout.addWidget(btn)

    # ──────────────────── PANTALLA LOGIN ─────────────────────────────

    def _show_login_screen(self):
        self._clear_window()
        _, layout = self._make_card(self._root_layout)

        layout.addWidget(self._label("🔐", "title", Qt.AlignCenter))
        layout.addWidget(self._label("Gestor de Contraseñas", "title", Qt.AlignCenter))
        layout.addWidget(self._label(
            "Ingrese sus credenciales para continuar",
            "subtitle", Qt.AlignCenter
        ))
        layout.addSpacing(16)

        # Separador visual
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #3a3a3a;")
        layout.addWidget(sep)
        layout.addSpacing(8)

        layout.addWidget(self._label("Usuario"))
        self._lg_username = self._field("Su nombre de usuario")
        layout.addWidget(self._lg_username)

        layout.addWidget(self._label("Contraseña maestra"))
        self._lg_password = self._field("••••••••", password=True)
        layout.addWidget(self._lg_password)

        layout.addSpacing(12)
        btn = self._primary_button("Iniciar Sesión")
        btn.clicked.connect(self._attempt_login)
        layout.addWidget(btn)

        self._lg_password.returnPressed.connect(self._attempt_login)
        self._lg_username.returnPressed.connect(self._lg_password.setFocus)

    def _attempt_login(self):
        username = self._lg_username.text().strip()
        password = self._lg_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Campos incompletos",
                                "Por favor complete todos los campos.")
            return

        success, _, _, error_message = self.controller.authenticate(username, password)
        if success:
            self._show_totp_screen()
        else:
            # Mostrar mensaje de error específico (bloqueo, credenciales incorrectas, etc)
            QMessageBox.critical(self, "Error de autenticación", error_message)
            self._lg_password.clear()
            self._lg_password.setFocus()

    # ──────────────────── PANTALLA TOTP ──────────────────────────────

    def _show_totp_screen(self):
        self._clear_window()
        _, layout = self._make_card(self._root_layout)

        layout.addWidget(self._label("🛡️", "title", Qt.AlignCenter))
        layout.addWidget(self._label("Verificación en dos pasos", "title", Qt.AlignCenter))
        layout.addWidget(self._label(
            "Ingrese el código de 6 dígitos de su aplicación de autenticación.",
            "subtitle", Qt.AlignCenter
        ))
        layout.addSpacing(20)

        self._totp_entry = QLineEdit()
        self._totp_entry.setObjectName("totp_input_box")
        self._totp_entry.setAlignment(Qt.AlignCenter)
        self._totp_entry.setMaxLength(6)
        self._totp_entry.setPlaceholderText("000000")
        self._totp_entry.setFixedHeight(64)
        layout.addWidget(self._totp_entry)

        layout.addSpacing(16)
        btn = self._primary_button("Verificar Código")
        btn.clicked.connect(self._verify_totp)
        layout.addWidget(btn)

        # Volver al login
        back_btn = QPushButton("← Volver al login")
        back_btn.setObjectName("link_btn")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._show_login_screen)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        self._totp_entry.returnPressed.connect(self._verify_totp)
        self._totp_entry.setFocus()

    def _verify_totp(self):
        code = self._totp_entry.text().strip()
        if not code:
            QMessageBox.warning(self, "Campo vacío", "Por favor ingrese el código.")
            return

        if self.controller.verify_totp_code(code):
            QMessageBox.information(self, "¡Bienvenido!",
                                    "Autenticación completada exitosamente.")
            self.close()
            if self.on_success:
                self.on_success(self.controller.current_user,
                                self.controller.fernet_key)
        else:
            QMessageBox.critical(self, "Código incorrecto",
                                "El código TOTP es incorrecto o ha expirado.")
            self._totp_entry.clear()
            self._totp_entry.setFocus()