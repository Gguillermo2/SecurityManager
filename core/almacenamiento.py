# core/almacenamiento.py
import os
import sqlite3
import logging
from typing import List, Optional, Dict
from pathlib import Path
from contextlib import contextmanager
from Modelo.models import Account

logger = logging.getLogger(__name__)

def get_appdata_dir() -> Path:
    """Obtiene y garantiza la existencia del directorio de datos de la app en AppData."""
    appdata = os.getenv('APPDATA') or os.path.expanduser('~')
    app_dir = Path(appdata) / "GestorDeCuentasWroser"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


# Ruta al archivo de base de datos SQLite
DB_PATH = get_appdata_dir() / "database.db"


# ====================== CONEXIÓN ======================

@contextmanager
def get_connection():
    """
    Context manager que abre una conexión SQLite, la entrega al bloque
    y hace commit + cierre automático. En caso de excepción hace rollback.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # Filas accesibles por nombre de columna
    conn.execute("PRAGMA foreign_keys = ON") # Integridad referencial
    conn.execute("PRAGMA journal_mode = WAL") # Mejor rendimiento en escrituras
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ====================== INICIALIZACIÓN DE TABLAS ======================

def initialize_database():
    """
    Crea las tablas si no existen. Seguro para llamar en cada arranque
    (usa CREATE TABLE IF NOT EXISTS).
    """
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS admin_user (
                id              INTEGER PRIMARY KEY CHECK (id = 1),  -- Solo un admin
                username        TEXT    NOT NULL UNIQUE,
                password        TEXT    NOT NULL,                    -- Hash bcrypt
                totp_secret     TEXT,
                fernet_key_salt TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS accounts (
                id                  TEXT PRIMARY KEY,
                platform            TEXT NOT NULL,
                email_or_username   TEXT NOT NULL,
                password            TEXT NOT NULL,                   -- Cifrada con Fernet
                category            TEXT NOT NULL DEFAULT 'General',
                notes               TEXT,
                created_at          TEXT,
                updated_at          TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_accounts_platform
                ON accounts (platform COLLATE NOCASE);

            CREATE INDEX IF NOT EXISTS idx_accounts_category
                ON accounts (category);
        """)
    logger.info(f"Base de datos inicializada en: {DB_PATH}")


# ====================== CRUD USUARIO ADMIN ======================

def save_admin_user(username: str, password: str,
                    totp_secret: str, fernet_key_salt: str):
    """
    Inserta o reemplaza el usuario administrador (solo puede existir uno).
    """
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO admin_user (id, username, password, totp_secret, fernet_key_salt)
            VALUES (1, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username        = excluded.username,
                password        = excluded.password,
                totp_secret     = excluded.totp_secret,
                fernet_key_salt = excluded.fernet_key_salt
        """, (username, password, totp_secret, fernet_key_salt))
    logger.info("Usuario administrador guardado en la base de datos.")


def load_admin_user() -> Optional[Dict]:
    """
    Carga el usuario administrador. Retorna un dict con sus campos
    o None si aún no existe.
    """
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM admin_user WHERE id = 1").fetchone()
    if row:
        return dict(row)
    return None


# ====================== CRUD CUENTAS ======================

def save_account(account: Account):
    """
    Inserta una cuenta nueva en la base de datos.
    La contraseña ya debe venir cifrada con Fernet.
    """
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO accounts
                (id, platform, email_or_username, password, category, notes,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account.id,
            account.platform,
            account.email_or_username,
            account.password,
            account.category,
            account.notes,
            account.created_at,
            account.updated_at,
        ))
    logger.debug(f"Cuenta '{account.platform}' guardada (id={account.id})")


def update_account_db(account_id: str, fields: Dict):
    """
    Actualiza los campos indicados en el dict `fields` para la cuenta con ese id.
    Solo actualiza los campos presentes en el dict (actualización parcial).
    """
    if not fields:
        return

    allowed = {"platform", "email_or_username", "password",
               "category", "notes", "updated_at"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return

    set_clause = ", ".join(f"{col} = ?" for col in filtered)
    values = list(filtered.values()) + [account_id]

    with get_connection() as conn:
        conn.execute(
            f"UPDATE accounts SET {set_clause} WHERE id = ?",
            values
        )
    logger.debug(f"Cuenta id={account_id} actualizada: {list(filtered.keys())}")


def delete_account_db(account_id: str) -> bool:
    """Elimina la cuenta con el id dado. Retorna True si se eliminó algo."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    deleted = cursor.rowcount > 0
    if deleted:
        logger.debug(f"Cuenta id={account_id} eliminada.")
    return deleted


def load_accounts_data() -> List[Account]:
    """
    Carga todas las cuentas desde SQLite.
    Las contraseñas siguen cifradas; el descifrado ocurre en AccountManager.
    """
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM accounts ORDER BY platform COLLATE NOCASE").fetchall()

    accounts = []
    for row in rows:
        row_dict = dict(row)
        if not row_dict.get("password"):
            logger.warning(f"Contraseña vacía para: {row_dict.get('platform', 'Desconocida')}")
            continue
        accounts.append(Account(**row_dict))

    logger.info(f"{len(accounts)} cuenta(s) cargadas exitosamente.")
    print(f"✅ {len(accounts)} cuenta(s) cargadas exitosamente.")
    return accounts


def get_filtered_accounts_db(search: str = "", category: str = "Todas") -> List[Account]:
    """
    Filtra cuentas directamente en SQLite (más eficiente que hacerlo en Python).
    """
    query = "SELECT * FROM accounts WHERE 1=1"
    params: list = []

    if category and category != "Todas":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (platform LIKE ? OR email_or_username LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])

    query += " ORDER BY platform COLLATE NOCASE"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [Account(**dict(row)) for row in rows]


def get_categories_db() -> List[str]:
    """Retorna la lista de categorías únicas existentes en la BD."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM accounts WHERE category IS NOT NULL ORDER BY category"
        ).fetchall()
    return [row[0] for row in rows]


def get_accounts_summary_db() -> Dict:
    """Resumen estadístico para la barra de estado."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        rows = conn.execute(
            "SELECT category, COUNT(*) as cnt FROM accounts GROUP BY category ORDER BY category"
        ).fetchall()
    by_category = {row["category"]: row["cnt"] for row in rows}
    return {"total": total, "by_category": by_category}


def get_account_by_id_db(account_id: str) -> Optional[Account]:
    """Busca una cuenta por su UUID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row:
        return Account(**dict(row))
    return None