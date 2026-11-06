# Vista/home.py
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QTextEdit, QScrollArea, QSlider,QMessageBox, QApplication,
    QGridLayout
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, QTimer

from controller.home_controller import HomeController
from Modelo.models import AdminUser
from automation.errors import AutomationError
from automation.platform_config import PlatformConfig, STRATEGY_LABELS

logger = logging.getLogger(__name__)

_CLIPBOARD_CLEAR_DELAY_MS = 10_000
_clipboard_clear_timer: QTimer | None = None


def _copy_text_with_expiry(text: str):
    global _clipboard_clear_timer

    clipboard = QApplication.clipboard()
    if _clipboard_clear_timer is not None:
        _clipboard_clear_timer.stop()
        _clipboard_clear_timer.deleteLater()

    clipboard.setText(text)
    timer = QTimer(QApplication.instance())
    timer.setSingleShot(True)
    timer.timeout.connect(
        lambda: clipboard.clear() if clipboard.text() == text else None
    )
    timer.start(_CLIPBOARD_CLEAR_DELAY_MS)
    _clipboard_clear_timer = timer

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

    QPushButton#btn_platforms {
        background-color: #27272a;
        color: #f4f4f5;
        font-size: 11px;
        border: 1px solid #3f3f46;
        border-radius: 5px;
        padding: 5px 10px;
    }
    QPushButton#btn_platforms:hover { background-color: #3f3f46; }

    QPushButton#btn_automation {
        background-color: #0ea5e9;
        color: #ffffff;
        font-size: 12px;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        padding: 6px 14px;
    }
    QPushButton#btn_automation:hover    { background-color: #0284c7; }
    QPushButton#btn_automation:disabled { background-color: #27272a; color: #71717a; }

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
        self._connect_automation_signals()
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

        platforms_btn = QPushButton("⚙  Plataformas")
        platforms_btn.setObjectName("btn_platforms")
        platforms_btn.setCursor(Qt.PointingHandCursor)
        platforms_btn.setToolTip(
            "Administrar dominios, URLs y selectores de las plataformas"
        )
        platforms_btn.clicked.connect(self.open_platforms_manager)
        hl.addWidget(platforms_btn)

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

        self._automation_btn = QPushButton("🌐  Iniciar sesión")
        self._automation_btn.setObjectName("btn_automation")
        self._automation_btn.setCursor(Qt.PointingHandCursor)
        self._automation_btn.setEnabled(False)
        self._automation_btn.setToolTip(
            "Abre el navegador y rellena el formulario de la plataforma"
        )
        self._automation_btn.clicked.connect(self.open_automation_dialog)
        actions.addWidget(self._automation_btn)

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
            self._automation_btn.setEnabled(True)

    def clear_details_panel(self):
        self._show_placeholder()
        self._edit_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)
        self._automation_btn.setEnabled(False)
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
            _copy_text_with_expiry(pwd)
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

    # ====================== Automatización web ======================

    def open_automation_dialog(self):
        if not self.selected_account:
            QMessageBox.warning(self, "Sin selección",
                                "Seleccione una cuenta para iniciar sesión.")
            return
        if not self.controller.is_session_valid():
            QMessageBox.warning(self, "Sesión expirada",
                                "Inicie sesión nuevamente para continuar.")
            self.logout()
            return
        dlg = _AutomationDialog(self, self.controller, self.selected_account)
        dlg.exec()

    def open_platforms_manager(self):
        dlg = _PlatformsManagerDialog(self, self.controller)
        dlg.exec()

    def _connect_automation_signals(self):
        service = self.controller.automation_service
        service.status_changed.connect(self._on_automation_status)
        service.login_ready.connect(self._on_automation_ready)
        service.login_failed.connect(self._on_automation_failed)
        service.browser_closed.connect(self._on_automation_closed)

    def _on_automation_status(self, text: str):
        self._status_lbl.setText(text)

    def _on_automation_ready(self, text: str):
        self._status_lbl.setText(text)
        logger.info("Automatización de login completada correctamente.")

    def _on_automation_failed(self, text: str):
        self._status_lbl.setText(text)
        logger.warning("Automatización de login fallida: %s", text)

    def _on_automation_closed(self):
        self._automation_btn.setEnabled(self.selected_account is not None)
        self._update_status_bar()

    def closeEvent(self, event):
        try:
            self.controller.shutdown_automation()
        except Exception:
            logger.debug("Error cerrando la automatización", exc_info=False)
        super().closeEvent(event)

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
        self.setFixedSize(480, 520)
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

    def _generate_password(self):
        self._password.setText(
            self.parent().controller.suggest_strong_password(
                self._password_length.value()
            )
        )


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
        _copy_text_with_expiry(self._pass_field.text())
        QMessageBox.information(self, "Copiado", "Contraseña copiada al portapapeles.")
        self.accept()


# ====================== Diálogos de automatización ======================


def _format_validation_error(exc: Exception) -> str:
    """Convierte errores de Pydantic/PlatformConfig en texto legible."""
    errors = getattr(exc, "errors", None)
    if callable(errors):
        try:
            messages = []
            for error in errors()[:5]:
                messages.append(f"• {error.get('msg', 'Valor no válido')}")
            if messages:
                return "\n".join(messages)
        except Exception:
            pass
    return str(exc)


class _AutomationDialog(QDialog):
    """Diálogo para lanzar el rellenado automático del formulario."""

    def __init__(self, parent, controller: HomeController, account):
        super().__init__(parent)
        self.controller = controller
        self.service = controller.automation_service
        self.account = account
        self._config = None
        self._connected = False

        self.setWindowTitle("Inicio de sesión automatizado")
        self.setMinimumSize(620, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("🌐  Inicio de sesión automatizado")
        title.setObjectName("section_title")
        layout.addWidget(title)

        subtitle = QLabel(
            "La aplicación abrirá el navegador y rellenará usuario y contraseña. "
            "El envío del formulario y cualquier CAPTCHA/2FA son manuales."
        )
        subtitle.setObjectName("detail_key")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        info = QGridLayout()
        info.setHorizontalSpacing(12)
        info.setVerticalSpacing(6)

        def add_info(row: int, key: str, value_widget: QWidget):
            key_lbl = QLabel(key)
            key_lbl.setObjectName("detail_key")
            key_lbl.setFixedWidth(110)
            info.addWidget(key_lbl, row, 0, Qt.AlignTop)
            info.addWidget(value_widget, row, 1)

        add_info(0, "Plataforma:", QLabel(account.platform))
        add_info(1, "Usuario:", QLabel(account.email_or_username))

        self._config_lbl = QLabel("")
        self._config_lbl.setWordWrap(True)
        add_info(2, "Configuración:", self._config_lbl)

        self._config_btn = QPushButton("⚙  Configurar plataforma")
        self._config_btn.setObjectName("btn_secondary")
        self._config_btn.setCursor(Qt.PointingHandCursor)
        self._config_btn.clicked.connect(self._configure_platform)
        info.addWidget(self._config_btn, 3, 1, Qt.AlignLeft)
        layout.addLayout(info)

        browser_row = QHBoxLayout()
        browser_lbl = QLabel("Navegador:")
        browser_lbl.setObjectName("detail_key")
        browser_lbl.setFixedWidth(110)
        self._browser_combo = QComboBox()
        for key, label in self.service.browser_options():
            self._browser_combo.addItem(label, key)
        browser_row.addWidget(browser_lbl)
        browser_row.addWidget(self._browser_combo, 1)
        layout.addLayout(browser_row)

        security_note = QLabel(
            "🔒  Solo se rellenan campos si la URL es HTTPS y el host coincide "
            "exactamente con el dominio autorizado de la plataforma."
        )
        security_note.setObjectName("detail_key")
        security_note.setWordWrap(True)
        layout.addWidget(security_note)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFixedHeight(140)
        self._log.setPlaceholderText("El progreso de la automatización aparecerá aquí…")
        layout.addWidget(self._log, 1)

        buttons = QHBoxLayout()
        self._start_btn = QPushButton("🌐  Abrir y rellenar")
        self._start_btn.setObjectName("btn_automation")
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.clicked.connect(self._start)

        self._stop_btn = QPushButton("Cerrar navegador")
        self._stop_btn.setObjectName("btn_secondary")
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.clicked.connect(self._stop)

        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("btn_secondary")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)

        buttons.addWidget(self._start_btn)
        buttons.addWidget(self._stop_btn)
        buttons.addStretch()
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        self._refresh_config_info()
        self._connect_signals()
        self._update_buttons()

    # -------------------- Estado de la configuración --------------------

    def _refresh_config_info(self):
        self._config = self.service.find_config_for_account(self.account)
        if self._config is not None:
            self._config_lbl.setText(
                f"{self._config.name} — {self._config.domain}"
            )
            self._config_lbl.setStyleSheet("color: #10b981;")
            self._config_btn.setVisible(False)
        else:
            self._config_lbl.setText(
                f"No hay configuración para '{self.account.platform}'. "
                "Créala para indicar el dominio y los selectores del formulario."
            )
            self._config_lbl.setStyleSheet("color: #f59e0b;")
            self._config_btn.setVisible(True)
        self._update_buttons()

    def _configure_platform(self):
        dlg = _PlatformConfigDialog(
            self,
            default_name=self.account.platform,
        )
        if dlg.exec() == QDialog.Accepted:
            config = dlg.get_config()
            try:
                self.controller.save_platform_config(config)
            except ValueError as exc:
                QMessageBox.warning(
                    self, "No se pudo guardar", _format_validation_error(exc)
                )
                return
            self._append(f"Configuración guardada para '{config.name}'.")
            self._refresh_config_info()

    # -------------------- Acciones --------------------

    def _start(self):
        if self.service.is_running():
            QMessageBox.information(
                self, "Automatización en curso",
                "Ya hay un navegador administrado por la aplicación. "
                "Ciérralo antes de iniciar otra automatización.",
            )
            return

        if self._config is None:
            self._configure_platform()
            if self._config is None:
                return

        browser_key = self._browser_combo.currentData()
        try:
            self.controller.start_automated_login(self.account, browser_key)
        except AutomationError as exc:
            QMessageBox.warning(self, "Automatización no disponible", str(exc))
            self._update_buttons()
            return
        except Exception:
            logger.exception("Error iniciando la automatización")
            QMessageBox.critical(
                self, "Error",
                "No se pudo iniciar la automatización. Revisa los registros.",
            )
            self._update_buttons()
            return

        self._append("Automatización iniciada…")
        self._update_buttons()

    def _stop(self):
        self.service.stop()
        self._append("Solicitando el cierre del navegador…")
        self._update_buttons()

    # -------------------- Señales --------------------

    def _connect_signals(self):
        self.service.status_changed.connect(self._on_status)
        self.service.login_ready.connect(self._on_ready)
        self.service.login_failed.connect(self._on_failed)
        self.service.browser_closed.connect(self._on_closed)
        self._connected = True

    def _disconnect_signals(self):
        if not self._connected:
            return
        for signal, slot in (
            (self.service.status_changed, self._on_status),
            (self.service.login_ready, self._on_ready),
            (self.service.login_failed, self._on_failed),
            (self.service.browser_closed, self._on_closed),
        ):
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass
        self._connected = False

    def _on_status(self, text: str):
        self._append(text)
        self._update_buttons()

    def _on_ready(self, text: str):
        self._append(f"✅  {text}")
        self._update_buttons()
        QMessageBox.information(self, "Formulario completado", text)

    def _on_failed(self, text: str):
        self._append(f"❌  {text}")
        self._update_buttons()
        QMessageBox.warning(self, "Automatización no completada", text)

    def _on_closed(self):
        self._append("Navegador cerrado.")
        self._update_buttons()

    def _update_buttons(self):
        running = self.service.is_running()
        self._start_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        self._browser_combo.setEnabled(not running)
        self._config_btn.setEnabled(not running)

    def _append(self, text: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{stamp}] {text}")

    def done(self, result):
        # Cubre aceptar, rechazar y cierre de ventana: evita que el diálogo
        # oculto siga recibiendo señales de la automatización.
        self._disconnect_signals()
        super().done(result)

    def closeEvent(self, event):
        self._disconnect_signals()
        super().closeEvent(event)


class _PlatformConfigDialog(QDialog):
    """Editor de una configuración de plataforma (sin credenciales)."""

    def __init__(self, parent=None, config: PlatformConfig | None = None,
                 default_name: str = ""):
        super().__init__(parent)
        self._config = config
        self._result: PlatformConfig | None = None

        self.setWindowTitle(
            f"Editar plataforma – {config.name}" if config else "Nueva plataforma"
        )
        self.resize(640, 720)
        self.setModal(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(12)

        title = QLabel("⚙  Configuración de plataforma")
        title.setObjectName("section_title")
        outer.addWidget(title)

        hint = QLabel(
            "Define el dominio HTTPS autorizado, la URL de login y los selectores "
            "del formulario. No se guardan credenciales aquí."
        )
        hint.setObjectName("detail_key")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        form = QVBoxLayout(inner)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)

        def add_field(label_text: str, widget: QWidget, hint_text: str = ""):
            lbl = QLabel(label_text)
            lbl.setObjectName("detail_key")
            form.addWidget(lbl)
            form.addWidget(widget)
            if hint_text:
                hint_lbl = QLabel(hint_text)
                hint_lbl.setObjectName("detail_key")
                hint_lbl.setWordWrap(True)
                hint_lbl.setStyleSheet("color: #71717a; font-size: 11px;")
                form.addWidget(hint_lbl)

        self._name = QLineEdit(config.name if config else default_name)
        self._name.setPlaceholderText("Ej: Gmail, GitHub, Netflix…")
        add_field("Nombre de la plataforma *", self._name)

        self._domain = QLineEdit(config.domain if config else "")
        self._domain.setPlaceholderText("accounts.google.com")
        add_field(
            "Dominio HTTPS autorizado *", self._domain,
            "Comparación exacta de host. No incluyas 'https://' ni rutas.",
        )

        self._alt_domains = QLineEdit(
            ", ".join(config.alt_domains) if config else ""
        )
        self._alt_domains.setPlaceholderText("www.ejemplo.com, ejemplo.com")
        add_field(
            "Dominios alternativos", self._alt_domains,
            "Separados por comas. También se comparan de forma exacta.",
        )

        self._login_url = QLineEdit(config.login_url if config else "https://")
        self._login_url.setPlaceholderText("https://accounts.google.com/signin")
        add_field(
            "URL de inicio de sesión *", self._login_url,
            "Debe usar HTTPS y pertenecer a uno de los dominios autorizados.",
        )

        self._aliases = QLineEdit(", ".join(config.aliases) if config else "")
        self._aliases.setPlaceholderText("gmail, google, correo google")
        add_field(
            "Alias de plataforma", self._aliases,
            "Nombres de cuenta que deben usar esta configuración (separados por comas).",
        )

        self._strategy = QComboBox()
        for key, label in self._strategy_options():
            self._strategy.addItem(label, key)
        if config:
            index = self._strategy.findData(config.strategy)
            self._strategy.setCurrentIndex(max(index, 0))
        add_field("Estrategia de identificación", self._strategy)

        self._username_selectors = QTextEdit()
        self._username_selectors.setFixedHeight(70)
        self._username_selectors.setPlaceholderText('input[type="email"]\n#login_field')
        if config:
            self._username_selectors.setPlainText(
                "\n".join(config.username_selectors)
            )
        add_field(
            "Selectores del campo de usuario *", self._username_selectors,
            "Uno por línea. Se usa el primero visible y editable.",
        )

        self._password_selectors = QTextEdit()
        self._password_selectors.setFixedHeight(70)
        self._password_selectors.setPlaceholderText('input[type="password"]\n#password')
        if config:
            self._password_selectors.setPlainText(
                "\n".join(config.password_selectors)
            )
        add_field(
            "Selectores del campo de contraseña *", self._password_selectors,
            "Uno por línea. Se usa el primero visible y editable.",
        )

        self._submit_selectors = QTextEdit()
        self._submit_selectors.setFixedHeight(55)
        self._submit_selectors.setPlaceholderText('button[type="submit"]')
        if config:
            self._submit_selectors.setPlainText(
                "\n".join(config.submit_selectors)
            )
        add_field(
            "Selectores del botón de envío (opcional)", self._submit_selectors,
            "Solo informativo: la aplicación nunca pulsa el botón de envío.",
        )

        self._enabled = QComboBox()
        self._enabled.addItem("Sí", True)
        self._enabled.addItem("No", False)
        if config and not config.enabled:
            self._enabled.setCurrentIndex(1)
        add_field("Automatización activa", self._enabled)

        self._notes = QTextEdit()
        self._notes.setFixedHeight(60)
        if config and config.notes:
            self._notes.setPlainText(config.notes)
        add_field("Notas", self._notes)

        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Guardar")
        save_btn.setObjectName("btn_primary")
        save_btn.clicked.connect(self._save)
        buttons.addWidget(cancel_btn)
        buttons.addStretch()
        buttons.addWidget(save_btn)
        outer.addLayout(buttons)

    @staticmethod
    def _strategy_options():
        from automation.automation_service import AutomationService

        return AutomationService.strategy_options()

    def _save(self):
        try:
            self._result = self._collect()
        except ValueError as exc:
            QMessageBox.warning(
                self, "Configuración no válida", _format_validation_error(exc)
            )
            return
        self.accept()

    def _collect(self) -> PlatformConfig:
        data = {
            "name": self._name.text().strip(),
            "domain": self._domain.text().strip(),
            "alt_domains": [
                part.strip()
                for part in self._alt_domains.text().split(",")
                if part.strip()
            ],
            "login_url": self._login_url.text().strip(),
            "username_selectors": [
                line.strip()
                for line in self._username_selectors.toPlainText().splitlines()
                if line.strip()
            ],
            "password_selectors": [
                line.strip()
                for line in self._password_selectors.toPlainText().splitlines()
                if line.strip()
            ],
            "submit_selectors": [
                line.strip()
                for line in self._submit_selectors.toPlainText().splitlines()
                if line.strip()
            ],
            "strategy": self._strategy.currentData(),
            "aliases": [
                part.strip()
                for part in self._aliases.text().split(",")
                if part.strip()
            ],
            "enabled": bool(self._enabled.currentData()),
            "notes": self._notes.toPlainText().strip() or None,
        }
        if self._config is not None:
            data["id"] = self._config.id
            data["created_at"] = self._config.created_at
        return PlatformConfig(**data)

    def get_config(self) -> PlatformConfig:
        return self._result


class _PlatformsManagerDialog(QDialog):
    """Listado y mantenimiento de configuraciones de plataformas."""

    def __init__(self, parent, controller: HomeController):
        super().__init__(parent)
        self.controller = controller
        self._row_map: dict[int, str] = {}

        self.setWindowTitle("Plataformas de automatización")
        self.resize(720, 480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("⚙  Plataformas configuradas")
        title.setObjectName("section_title")
        layout.addWidget(title)

        hint = QLabel(
            "Cada plataforma define su dominio autorizado, URL de login y "
            "selectores. Las contraseñas siguen cifradas en las cuentas."
        )
        hint.setObjectName("detail_key")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Plataforma", "Dominio", "Estrategia", "Activa"]
        )
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.doubleClicked.connect(lambda _: self._edit())
        layout.addWidget(self._table, 1)

        buttons = QHBoxLayout()
        new_btn = QPushButton("＋  Nueva")
        new_btn.setObjectName("btn_new")
        new_btn.clicked.connect(self._add)
        edit_btn = QPushButton("✏  Editar")
        edit_btn.setObjectName("btn_edit")
        edit_btn.clicked.connect(self._edit)
        delete_btn = QPushButton("🗑  Eliminar")
        delete_btn.setObjectName("btn_delete")
        delete_btn.clicked.connect(self._delete)
        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("btn_secondary")
        close_btn.clicked.connect(self.accept)

        buttons.addWidget(new_btn)
        buttons.addWidget(edit_btn)
        buttons.addWidget(delete_btn)
        buttons.addStretch()
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        self._refresh()

    def _refresh(self):
        configs = self.controller.get_platform_configs()
        self._table.setRowCount(0)
        self._row_map = {}
        for row, config in enumerate(configs):
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(config.name))
            self._table.setItem(row, 1, QTableWidgetItem(config.domain))
            self._table.setItem(
                row, 2,
                QTableWidgetItem(STRATEGY_LABELS.get(config.strategy, config.strategy)),
            )
            self._table.setItem(row, 3, QTableWidgetItem("Sí" if config.enabled else "No"))
            self._row_map[row] = config.id

    def _selected_id(self) -> str | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        return self._row_map.get(row)

    def _add(self):
        dlg = _PlatformConfigDialog(self)
        if dlg.exec() == QDialog.Accepted:
            try:
                self.controller.save_platform_config(dlg.get_config())
            except ValueError as exc:
                QMessageBox.warning(
                    self, "No se pudo guardar", _format_validation_error(exc)
                )
                return
            self._refresh()

    def _edit(self):
        config_id = self._selected_id()
        if not config_id:
            QMessageBox.warning(self, "Sin selección",
                                "Seleccione una plataforma para editar.")
            return
        config = self.controller.get_platform_config(config_id)
        if config is None:
            QMessageBox.warning(self, "No encontrada",
                                "La configuración ya no existe.")
            self._refresh()
            return
        dlg = _PlatformConfigDialog(self, config=config)
        if dlg.exec() == QDialog.Accepted:
            try:
                self.controller.save_platform_config(dlg.get_config())
            except ValueError as exc:
                QMessageBox.warning(
                    self, "No se pudo guardar", _format_validation_error(exc)
                )
                return
            self._refresh()

    def _delete(self):
        config_id = self._selected_id()
        if not config_id:
            QMessageBox.warning(self, "Sin selección",
                                "Seleccione una plataforma para eliminar.")
            return
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Eliminar esta configuración de plataforma?\n"
            "Las cuentas guardadas no se verán afectadas.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.controller.delete_platform_config(config_id):
                self._refresh()
            else:
                QMessageBox.critical(
                    self, "Error", "No se pudo eliminar la configuración."
                )
