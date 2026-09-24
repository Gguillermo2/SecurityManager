# Vista/home.py
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QTextEdit, QScrollArea, QSlider, QMessageBox, QApplication
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, QTimer

from controller.home_controller import HomeController
from Modelo.models import AdminUser

logger = logging.getLogger(__name__)

# ─────────────────────────── QSS Moderno & Pulido ────────────────────────────
HOME_QSS = """
    QMainWindow { 
        background-color: #121214; 
    }
    
    QWidget { 
        color: #e4e4e7; 
        font-family: 'Segoe UI', -apple-system, sans-serif;
    }

    /* Encabezado superior */
    QFrame#header { 
        background-color: #18181b; 
        border-bottom: 1px solid #27272a;
    }
    QLabel#header_title { 
        color: #f4f4f5; 
        font-size: 15px; 
        font-weight: 600; 
    }
    QLabel#header_user  { 
        color: #a1a1aa; 
        font-size: 12px; 
    }

    /* Paneles de contenido */
    QFrame#left_panel, QFrame#right_panel { 
        background-color: #18181b; 
        border: 1px solid #27272a;
        border-radius: 8px; 
    }

    QLabel#section_title { 
        color: #f4f4f5; 
        font-size: 14px; 
        font-weight: 600; 
    }
    QLabel#detail_key    { 
        color: #a1a1aa; 
        font-size: 12px; 
    }
    QLabel#detail_value  { 
        color: #f4f4f5; 
        font-size: 12px; 
        font-weight: 500; 
    }
    QLabel#placeholder   { 
        color: #71717a; 
        font-size: 13px; 
    }

    /* Inputs y Combos */
    QLineEdit {
        background-color: #27272a; 
        color: #f4f4f5;
        border: 1px solid #3f3f46; 
        border-radius: 6px;
        padding: 6px 12px; 
        font-size: 12px;
    }
    QLineEdit:focus { 
        border: 1px solid #6366f1; 
    }

    QComboBox {
        background-color: #27272a; 
        color: #f4f4f5;
        border: 1px solid #3f3f46; 
        border-radius: 6px;
        padding: 5px 10px; 
        font-size: 12px;
    }
    QComboBox::drop-down { 
        border: none; 
        width: 20px; 
    }
    QComboBox QAbstractItemView {
        background-color: #27272a; 
        color: #f4f4f5;
        selection-background-color: #6366f1;
        border: 1px solid #3f3f46;
    }

    /* Tabla */
    QTableWidget {
        background-color: #18181b; 
        color: #e4e4e7;
        border: 1px solid #27272a; 
        border-radius: 6px;
        gridline-color: #27272a; 
        font-size: 12px;
    }
    QTableWidget::item { 
        padding: 6px 10px; 
        border-bottom: 1px solid #27272a;
    }
    QTableWidget::item:selected { 
        background-color: #312e81; 
        color: #ffffff; 
    }
    QHeaderView::section {
        background-color: #27272a; 
        color: #a1a1aa;
        border: none; 
        padding: 8px 10px;
        font-size: 11px; 
        font-weight: 600;
    }

    /* Botones */
    QPushButton#btn_new {
        background-color: #10b981; 
        color: #ffffff;
        font-size: 12px; 
        font-weight: 600;
        border: none; 
        border-radius: 6px; 
        padding: 6px 14px;
    }
    QPushButton#btn_new:hover { background-color: #059669; }

    QPushButton#btn_logout {
        background-color: #ef4444; 
        color: #ffffff;
        font-size: 11px; 
        border: none; 
        border-radius: 5px; 
        padding: 5px 12px;
    }
    QPushButton#btn_logout:hover { background-color: #dc2626; }

    QPushButton#btn_edit {
        background-color: #3b82f6; 
        color: #ffffff;
        font-size: 12px; 
        border: none; 
        border-radius: 6px; 
        padding: 6px 14px;
    }
    QPushButton#btn_edit:hover    { background-color: #2563eb; }
    QPushButton#btn_edit:disabled { background-color: #27272a; color: #71717a; }

    QPushButton#btn_delete {
        background-color: #ef4444; 
        color: #ffffff;
        font-size: 12px; 
        border: none; 
        border-radius: 6px; 
        padding: 6px 14px;
    }
    QPushButton#btn_delete:hover    { background-color: #dc2626; }
    QPushButton#btn_delete:disabled { background-color: #27272a; color: #71717a; }

    QPushButton#btn_gen_pass {
        background-color: #8b5cf6; 
        color: #ffffff;
        font-size: 12px; 
        border: none; 
        border-radius: 6px; 
        padding: 6px 14px;
    }
    QPushButton#btn_gen_pass:hover { background-color: #7c3aed; }

    QPushButton#btn_show_pass {
        background-color: #3f3f46; 
        color: #ffffff;
        font-size: 11px; 
        border: none; 
        border-radius: 4px; 
        padding: 2px 8px;
    }
    QPushButton#btn_show_pass:hover { background-color: #52525b; }

    QPushButton#btn_primary {
        background-color: #6366f1; 
        color: #ffffff;
        font-size: 12px; 
        font-weight: 600;
        border: none; 
        border-radius: 6px; 
        padding: 8px 18px;
    }
    QPushButton#btn_primary:hover { background-color: #4f46e5; }

    QPushButton#btn_secondary {
        background-color: #27272a; 
        color: #f4f4f5;
        font-size: 12px; 
        border: 1px solid #3f3f46; 
        border-radius: 6px; 
        padding: 8px 18px;
    }
    QPushButton#btn_secondary:hover { background-color: #3f3f46; }

    /* Barra de Estado */
    QFrame#status_bar { 
        background-color: #18181b; 
        border-top: 1px solid #27272a;
    }
    QLabel#status_text { 
        color: #a1a1aa; 
        font-size: 11px; 
    }

    /* Modal / Dialog */
    QDialog { background-color: #18181b; }
    QTextEdit {
        background-color: #27272a; 
        color: #f4f4f5;
        border: 1px solid #3f3f46; 
        border-radius: 6px;
        font-size: 12px; 
        padding: 6px;
    }
    QScrollBar:vertical {
        background-color: #18181b; 
        width: 8px; 
        border-radius: 4px;
    }
    QScrollBar::handle:vertical { 
        background-color: #3f3f46; 
        border-radius: 4px; 
    }
"""

def start_home(admin_user: AdminUser, fernet_key: bytes):
    window = HomeWindow(admin_user, fernet_key)
    window.show()
    return window


class HomeWindow(QMainWindow):
    def __init__(self, admin_user: AdminUser, fernet_key: bytes):
        super().__init__()
        self.controller = HomeController(admin_user, fernet_key)
        self.selected_account = None
        self._pass_visible = False

        self.setWindowTitle("Gestor de Contraseñas – Panel Principal")
        self.setMinimumSize(900, 620)
        self.resize(1100, 700)
        self.setStyleSheet(HOME_QSS)

        self._build_ui()
        self.refresh_accounts_list()
        self._start_session_timer()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Header como QFrame para un control de bordes y fondo perfecto
        vbox.addWidget(self._build_header())

        # Contenedor central con padding para separar paneles
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([650, 400])

        center_layout.addWidget(splitter)
        vbox.addWidget(center_container, 1)

        # Status Bar como QFrame
        vbox.addWidget(self._build_status_bar())

    def _build_header(self) -> QWidget:
        h = QFrame()
        h.setObjectName("header")
        h.setFixedHeight(50)
        hl = QHBoxLayout(h)
        hl.setContentsMargins(16, 0, 16, 0)

        title = QLabel("🔐  Gestor de Contraseñas")
        title.setObjectName("header_title")
        hl.addWidget(title)
        hl.addStretch()

        user_lbl = QLabel(f"👤  {self.controller.admin_user.username}")
        user_lbl.setObjectName("header_user")
        hl.addWidget(user_lbl)

        logout_btn = QPushButton("Cerrar Sesión")
        logout_btn.setObjectName("btn_logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        hl.addWidget(logout_btn)
        return h

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("left_panel")
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(14, 14, 14, 14)
        vbox.setSpacing(10)

        top = QHBoxLayout()
        lbl = QLabel("Cuentas Guardadas")
        lbl.setObjectName("section_title")
        top.addWidget(lbl)
        top.addStretch()
        new_btn = QPushButton("＋  Nueva")
        new_btn.setObjectName("btn_new")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self.show_add_account_dialog)
        top.addWidget(new_btn)
        vbox.addLayout(top)

        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  Buscar plataforma o usuario…")
        self._search_input.textChanged.connect(self.filter_accounts)
        search_row.addWidget(self._search_input, 3)

        self._category_combo = QComboBox()
        self._category_combo.addItems(self.controller.get_all_categories())
        self._category_combo.currentTextChanged.connect(self.filter_accounts)
        search_row.addWidget(self._category_combo, 2)
        vbox.addLayout(search_row)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Plataforma", "Usuario / Email", "Categoría"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.itemSelectionChanged.connect(self.on_account_select)
        self._table.doubleClicked.connect(lambda _: self.show_password())
        vbox.addWidget(self._table, 1)
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("right_panel")
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.setSpacing(12)

        title = QLabel("Detalles de la Cuenta")
        title.setObjectName("section_title")
        vbox.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #27272a;")
        vbox.addWidget(sep)

        self._details_scroll = QScrollArea()
        self._details_scroll.setWidgetResizable(True)
        self._details_scroll.setFrameShape(QFrame.NoFrame)
        self._details_scroll.setStyleSheet("QScrollArea{background:transparent;}")
        self._details_inner = QWidget()
        self._details_inner.setStyleSheet("background:transparent;")
        self._details_layout = QVBoxLayout(self._details_inner)
        self._details_layout.setContentsMargins(0, 0, 0, 0)
        self._details_layout.setSpacing(8)
        self._details_scroll.setWidget(self._details_inner)
        vbox.addWidget(self._details_scroll, 1)

        self._show_placeholder()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #27272a;")
        vbox.addWidget(sep2)

        actions = QHBoxLayout()
        self._edit_btn = QPushButton("✏  Editar")
        self._edit_btn.setObjectName("btn_edit")
        self._edit_btn.setCursor(Qt.PointingHandCursor)
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self.edit_account)
        actions.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("🗑  Eliminar")
        self._delete_btn.setObjectName("btn_delete")
        self._delete_btn.setCursor(Qt.PointingHandCursor)
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self.delete_account)
        actions.addWidget(self._delete_btn)

        actions.addStretch()

        gen_btn = QPushButton("🔑  Generar")
        gen_btn.setObjectName("btn_gen_pass")
        gen_btn.setCursor(Qt.PointingHandCursor)
        gen_btn.clicked.connect(self.generate_password)
        actions.addWidget(gen_btn)

        vbox.addLayout(actions)
        return panel

    def _build_status_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("status_bar")
        bar.setFixedHeight(28)
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(12, 0, 12, 0)

        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("status_text")
        hl.addWidget(self._status_lbl)
        hl.addStretch()

        self._time_lbl = QLabel("")
        self._time_lbl.setObjectName("status_text")
        hl.addWidget(self._time_lbl)

        clock = QTimer(self)
        clock.timeout.connect(self._update_clock)
        clock.start(1000)
        self._update_clock()
        return bar

    def _clear_details(self):
        while self._details_layout.count():
            item = self._details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_placeholder(self):
        self._clear_details()
        lbl = QLabel("Seleccione una cuenta\npara ver los detalles")
        lbl.setObjectName("placeholder")
        lbl.setAlignment(Qt.AlignCenter)
        self._details_layout.addStretch()
        self._details_layout.addWidget(lbl)
        self._details_layout.addStretch()

    def show_account_details(self):
        if not self.selected_account:
            return
        self._clear_details()
        self._pass_visible = False
        acc = self.selected_account

        def _row(key: str, value: str):
            w = QWidget()
            w.setStyleSheet("background:transparent;")
            hl = QHBoxLayout(w)
            hl.setContentsMargins(0, 2, 0, 2)
            k = QLabel(key)
            k.setObjectName("detail_key")
            k.setFixedWidth(110)
            v = QLabel(value)
            v.setObjectName("detail_value")
            v.setWordWrap(True)
            v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            hl.addWidget(k)
            hl.addWidget(v, 1)
            return w

        self._details_layout.addWidget(_row("Plataforma:", acc.platform))
        self._details_layout.addWidget(_row("Usuario / Email:", acc.email_or_username))
        self._details_layout.addWidget(_row("Categoría:", acc.category or "—"))

        pw = QWidget()
        pw.setStyleSheet("background:transparent;")
        phl = QHBoxLayout(pw)
        phl.setContentsMargins(0, 2, 0, 2)
        pk = QLabel("Contraseña:")
        pk.setObjectName("detail_key")
        pk.setFixedWidth(110)
        self._pass_value_lbl = QLabel("● ● ● ● ● ● ● ● ●")
        self._pass_value_lbl.setObjectName("detail_value")
        self._pass_value_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        toggle_btn = QPushButton("👁")
        toggle_btn.setObjectName("btn_show_pass")
        toggle_btn.setFixedSize(32, 24)
        toggle_btn.setCursor(Qt.PointingHandCursor)
        toggle_btn.clicked.connect(self.toggle_password)
        phl.addWidget(pk)
        phl.addWidget(self._pass_value_lbl, 1)
        phl.addWidget(toggle_btn)
        self._details_layout.addWidget(pw)

        if acc.notes:
            notes_lbl = QLabel("Notas:")
            notes_lbl.setObjectName("detail_key")
            self._details_layout.addWidget(notes_lbl)
            notes_box = QTextEdit()
            notes_box.setPlainText(acc.notes)
            notes_box.setReadOnly(True)
            notes_box.setFixedHeight(72)
            self._details_layout.addWidget(notes_box)

        if acc.created_at:
            self._details_layout.addWidget(_row("Creada:", acc.created_at[:10]))
        if acc.updated_at:
            self._details_layout.addWidget(_row("Actualizada:", acc.updated_at[:10]))

        self._details_layout.addStretch()

    def toggle_password(self):
        if not self.selected_account:
            return
        if not self._pass_visible:
            pwd = self.controller.get_decrypted_password(self.selected_account.id)
            self._pass_value_lbl.setText(pwd)
            self._pass_visible = True
        else:
            self._pass_value_lbl.setText("● ● ● ● ● ● ● ● ●")
            self._pass_visible = False

    def refresh_accounts_list(self):
        accounts = self.controller.get_filtered_accounts(
            search=self._search_input.text(),
            category=self._category_combo.currentText()
        )
        self._table.setRowCount(0)
        self._row_id_map: dict[int, str] = {}

        for i, acc in enumerate(accounts):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(acc.platform))
            self._table.setItem(i, 1, QTableWidgetItem(acc.email_or_username))
            self._table.setItem(i, 2, QTableWidgetItem(acc.category or ""))
            self._row_id_map[i] = acc.id

        self._update_status_bar()

        current = self._category_combo.currentText()
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        self._category_combo.addItems(self.controller.get_all_categories())
        idx = self._category_combo.findText(current)
        self._category_combo.setCurrentIndex(max(idx, 0))
        self._category_combo.blockSignals(False)

    def filter_accounts(self):
        self.refresh_accounts_list()

    def on_account_select(self):
        row = self._table.currentRow()
        if row < 0:
            return
        account_id = self._row_id_map.get(row)
        if not account_id:
            return
        self.selected_account = self.controller.select_account(account_id)
        if self.selected_account:
            self.show_account_details()
            self._edit_btn.setEnabled(True)
            self._delete_btn.setEnabled(True)

    def clear_details_panel(self):
        self._show_placeholder()
        self._edit_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)
        self.selected_account = None

    def show_password(self):
        if not self.selected_account:
            return
        pwd = self.controller.get_decrypted_password(self.selected_account.id)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Contraseña – {self.selected_account.platform}")
        dlg.setFixedSize(380, 180)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(QLabel(f"🔑  {self.selected_account.platform}"))
        pass_field = QLineEdit(pwd)
        pass_field.setReadOnly(True)
        pass_field.setAlignment(Qt.AlignCenter)
        pass_field.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 14px; letter-spacing: 2px;"
        )
        layout.addWidget(pass_field)

        def copy_and_close():
            QApplication.clipboard().setText(pwd)
            QMessageBox.information(dlg, "Copiado", "Contraseña copiada al portapapeles.")
            dlg.accept()

        copy_btn = QPushButton("📋  Copiar al portapapeles")
        copy_btn.setObjectName("btn_primary")
        copy_btn.clicked.connect(copy_and_close)
        layout.addWidget(copy_btn)
        dlg.exec()

    def show_add_account_dialog(self):
        dlg = _AccountDialog(self, title="Nueva Cuenta")
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not all([data["platform"], data["user"], data["password"]]):
                QMessageBox.warning(self, "Campos incompletos",
                                    "Plataforma, usuario y contraseña son obligatorios.")
                return
            try:
                self.controller.create_account(
                    platform=data["platform"],
                    email_or_username=data["user"],
                    password=data["password"],
                    category=data["category"],
                    notes=data["notes"],
                )
                self.refresh_accounts_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar:\n{str(e)}")

    def edit_account(self):
        if not self.selected_account:
            QMessageBox.warning(self, "Sin selección",
                                "Seleccione una cuenta para editar.")
            return
        acc = self.selected_account
        dlg = _AccountDialog(
            self,
            title=f"Editar – {acc.platform}",
            platform=acc.platform,
            user=acc.email_or_username,
            category=acc.category or "General",
            notes=acc.notes or "",
        )
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not all([data["platform"], data["user"]]):
                QMessageBox.warning(self, "Campos incompletos",
                                    "Plataforma y usuario son obligatorios.")
                return
            try:
                success = self.controller.update_account(
                    account_id=acc.id,
                    platform=data["platform"],
                    email_or_username=data["user"],
                    password=data["password"] if data["password"] else None,
                    category=data["category"],
                    notes=data["notes"],
                )
                if success:
                    self.refresh_accounts_list()
                    self.selected_account = self.controller.get_account_by_id(acc.id)
                    if self.selected_account:
                        self.show_account_details()
                else:
                    QMessageBox.information(self, "Sin cambios",
                                            "No se detectaron cambios que guardar.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al actualizar:\n{str(e)}")

    def delete_account(self):
        if not self.selected_account:
            return
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar la cuenta de '{self.selected_account.platform}'?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.controller.delete_account(self.selected_account.id):
                self.clear_details_panel()
                self.refresh_accounts_list()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la cuenta.")

    def generate_password(self):
        dlg = _PasswordGeneratorDialog(self, self.controller)
        dlg.exec()

    def _update_status_bar(self):
        summary = self.controller.get_accounts_summary()
        parts = [f"Total: {summary['total']}"]
        for cat, count in summary["by_category"].items():
            parts.append(f"{cat}: {count}")
        self._status_lbl.setText("  •  ".join(parts))

    def _update_clock(self):
        self._time_lbl.setText(datetime.now().strftime("%H:%M:%S"))

    def mousePressEvent(self, event):
        self._refresh_session_activity()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self._refresh_session_activity()
        super().keyPressEvent(event)

    def _refresh_session_activity(self):
        if self.controller.is_session_valid():
            self.controller.session_manager.refresh_session()
            logger.debug("Sesión renovada por actividad del usuario")

    def _start_session_timer(self):
        t = QTimer(self)
        t.timeout.connect(self.check_session)
        t.start(60_000)

    def check_session(self):
        if not self.controller.is_session_valid():
            QMessageBox.warning(self, "Sesión expirada",
                                "Su sesión ha expirado. Inicie sesión nuevamente.")
            self.logout()

    def logout(self):
        self.controller.logout()
        self.close()
        from Vista.login import start_login
        win = start_login(lambda u, k: start_home(u, k))
        win.show()


class _AccountDialog(QDialog):
    CATEGORIES = ["General", "Redes Sociales", "Bancos", "Correo", "Videojuegos", "Otros"]

    def __init__(self, parent=None, title="Cuenta",
                 platform="", user="", category="General", notes=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(480, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("section_title")
        layout.addWidget(lbl_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #3f3f46;")
        layout.addWidget(sep)

        def add_field(label_text: str, widget: QWidget):
            lbl = QLabel(label_text)
            lbl.setObjectName("detail_key")
            layout.addWidget(lbl)
            layout.addWidget(widget)

        self._platform = QLineEdit(platform)
        self._platform.setPlaceholderText("Ej: Gmail, Netflix, Banco…")
        add_field("Plataforma *", self._platform)

        self._user = QLineEdit(user)
        self._user.setPlaceholderText("usuario@correo.com o nombre de usuario")
        add_field("Usuario / Email *", self._user)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setPlaceholderText(
            "Nueva contraseña  (vacío = sin cambio)" if platform else "Contraseña *"
        )
        add_field("Contraseña", self._password)

        self._category = QComboBox()
        self._category.addItems(self.CATEGORIES)
        idx = self._category.findText(category)
        self._category.setCurrentIndex(max(idx, 0))
        add_field("Categoría", self._category)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Notas adicionales (opcional)…")
        self._notes.setFixedHeight(80)
        if notes:
            self._notes.setPlainText(notes)
        add_field("Notas", self._notes)

        layout.addStretch()

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Guardar")
        save_btn.setObjectName("btn_primary")
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def get_data(self) -> dict:
        return {
            "platform": self._platform.text().strip(),
            "user": self._user.text().strip(),
            "password": self._password.text().strip(),
            "category": self._category.currentText(),
            "notes": self._notes.toPlainText().strip(),
        }


class _PasswordGeneratorDialog(QDialog):
    def __init__(self, parent, controller: HomeController):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Generador de Contraseñas")
        self.setFixedSize(400, 230)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("🔑  Generar Contraseña Fuerte")
        title.setObjectName("section_title")
        layout.addWidget(title)

        length_row = QHBoxLayout()
        self._length_lbl = QLabel("Longitud: 16")
        self._length_lbl.setObjectName("detail_key")
        self._length_lbl.setFixedWidth(100)
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(8, 32)
        self._slider.setValue(16)
        self._slider.setStyleSheet("""
            QSlider::groove:horizontal { background:#3f3f46; height:4px; border-radius:2px; }
            QSlider::handle:horizontal  { background:#6366f1; width:14px; height:14px;
                                          border-radius:7px; margin:-5px 0; }
            QSlider::sub-page:horizontal { background:#6366f1; height:4px; border-radius:2px; }
        """)
        self._slider.valueChanged.connect(self._on_length_change)
        length_row.addWidget(self._length_lbl)
        length_row.addWidget(self._slider)
        layout.addLayout(length_row)

        self._pass_field = QLineEdit()
        self._pass_field.setReadOnly(True)
        self._pass_field.setAlignment(Qt.AlignCenter)
        self._pass_field.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 13px; letter-spacing: 2px;"
        )
        layout.addWidget(self._pass_field)

        btn_row = QHBoxLayout()
        regen_btn = QPushButton("🔄  Generar otra")
        regen_btn.setObjectName("btn_secondary")
        regen_btn.clicked.connect(self._generate)
        copy_btn = QPushButton("📋  Copiar y cerrar")
        copy_btn.setObjectName("btn_primary")
        copy_btn.clicked.connect(self._copy_and_close)
        btn_row.addWidget(regen_btn)
        btn_row.addWidget(copy_btn)
        layout.addLayout(btn_row)

        self._generate()

    def _on_length_change(self, value: int):
        self._length_lbl.setText(f"Longitud: {value}")
        self._generate()

    def _generate(self):
        self._pass_field.setText(
            self.controller.suggest_strong_password(self._slider.value())
        )

    def _copy_and_close(self):
        QApplication.clipboard().setText(self._pass_field.text())
        QMessageBox.information(self, "Copiado", "Contraseña copiada al portapapeles.")
        self.accept()