# automation/platform_config.py
"""
Configuraciones independientes por plataforma para la automatización de login.

Cada plataforma define su propio dominio HTTPS autorizado, URL de inicio de
sesión y selectores. Las configuraciones se persisten en SQLite para que el
usuario pueda personalizarlas y añadir plataformas nuevas sin tocar el código
de automatización.

Este módulo NO contiene lógica de Playwright ni credenciales.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
import unicodedata
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator

from core.almacenamiento import get_connection, initialize_platform_configs_table

logger = logging.getLogger(__name__)

# Estrategias de identificación admitidas para los selectores.
STRATEGY_AUTO = "auto"
STRATEGY_CSS = "css"
STRATEGY_LABEL = "label"
STRATEGY_PLACEHOLDER = "placeholder"
STRATEGY_ROLE = "role"

STRATEGIES = (
    STRATEGY_AUTO,
    STRATEGY_CSS,
    STRATEGY_LABEL,
    STRATEGY_PLACEHOLDER,
    STRATEGY_ROLE,
)

STRATEGY_LABELS = {
    STRATEGY_AUTO: "Automática (CSS → placeholder → label)",
    STRATEGY_CSS: "CSS",
    STRATEGY_LABEL: "Etiqueta (label)",
    STRATEGY_PLACEHOLDER: "Placeholder",
    STRATEGY_ROLE: "Rol accesible (textbox)",
}

_HOST_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"(?!-)[a-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[a-z0-9-]{1,63}(?<!-))*$"
)
_MAX_SELECTOR_LEN = 500


class PlatformConfigError(ValueError):
    """Error de validación de una configuración de plataforma."""


def normalize_host(value: str) -> str:
    """
    Normaliza un host para comparaciones EXACTAS.

    - Acepta un host o una URL completa (se extrae el hostname).
    - Pasa a minúsculas, elimina el punto final y espacios.
    - Convierte dominios internacionales a IDNA (punycode).
    """
    raw = (value or "").strip()
    if not raw:
        raise PlatformConfigError("El dominio es obligatorio.")

    if "://" in raw:
        parsed = urlsplit(raw)
        raw = parsed.hostname or ""

    host = raw.strip().lower().rstrip(".")
    if not host:
        raise PlatformConfigError("El dominio no es válido.")

    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise PlatformConfigError("El dominio contiene caracteres no válidos.") from exc

    if not _HOST_RE.match(host):
        raise PlatformConfigError(
            "El dominio no es válido. Usa solo el host, por ejemplo "
            "'accounts.google.com'."
        )
    return host


def validate_https_url(url: str) -> str:
    """Valida que una URL use HTTPS y no incluya credenciales embebidas."""
    raw = (url or "").strip()
    if not raw:
        raise PlatformConfigError("La URL de inicio de sesión es obligatoria.")

    parsed = urlsplit(raw)
    if parsed.scheme.lower() != "https":
        raise PlatformConfigError("La URL de inicio de sesión debe usar HTTPS.")
    if not parsed.hostname:
        raise PlatformConfigError("La URL de inicio de sesión no tiene un host válido.")
    if parsed.username or parsed.password:
        raise PlatformConfigError("La URL no debe incluir usuario ni contraseña.")

    return raw


def host_from_url(url: str) -> Optional[str]:
    """Devuelve el host normalizado de una URL, o None si no es http(s)."""
    try:
        parsed = urlsplit(url or "")
    except ValueError:
        return None
    if parsed.scheme.lower() not in ("http", "https"):
        return None
    host = parsed.hostname
    if not host:
        return None
    try:
        return normalize_host(host)
    except PlatformConfigError:
        return None


def _normalize_token(value: str) -> str:
    """Normaliza un nombre de plataforma para comparaciones tolerantes."""
    text = unicodedata.normalize("NFKD", (value or "").strip().lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch for ch in text if ch.isalnum())


def _clean_selector_list(values: Iterable[str], label: str) -> List[str]:
    cleaned: List[str] = []
    for value in values:
        selector = (value or "").strip()
        if not selector:
            continue
        if "\x00" in selector:
            raise PlatformConfigError(f"{label}: un selector contiene caracteres no válidos.")
        if len(selector) > _MAX_SELECTOR_LEN:
            raise PlatformConfigError(
                f"{label}: un selector supera los {_MAX_SELECTOR_LEN} caracteres."
            )
        if selector not in cleaned:
            cleaned.append(selector)
    if not cleaned:
        raise PlatformConfigError(f"{label}: se requiere al menos un selector.")
    return cleaned


class PlatformConfig(BaseModel):
    """Configuración de automatización para una plataforma concreta."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: str
    alt_domains: List[str] = Field(default_factory=list)
    login_url: str
    username_selectors: List[str] = Field(default_factory=list)
    password_selectors: List[str] = Field(default_factory=list)
    submit_selectors: List[str] = Field(default_factory=list)
    strategy: str = STRATEGY_AUTO
    aliases: List[str] = Field(default_factory=list)
    enabled: bool = True
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        name = (value or "").strip()
        if not name:
            raise PlatformConfigError("El nombre de la plataforma es obligatorio.")
        if len(name) > 120:
            raise PlatformConfigError("El nombre de la plataforma es demasiado largo.")
        return name

    @field_validator("domain")
    @classmethod
    def _validate_domain(cls, value: str) -> str:
        return normalize_host(value)

    @field_validator("alt_domains", mode="before")
    @classmethod
    def _coerce_alt_domains(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [part for part in re.split(r"[,\s]+", value) if part]
        return list(value)

    @field_validator("login_url")
    @classmethod
    def _validate_login_url(cls, value: str) -> str:
        return validate_https_url(value)

    @field_validator("username_selectors", "password_selectors", mode="before")
    @classmethod
    def _coerce_required_selectors(cls, value: Any, info) -> List[str]:
        if isinstance(value, str):
            value = value.splitlines()
        if value is None:
            value = []
        label = (
            "Selectores del campo de usuario"
            if info.field_name == "username_selectors"
            else "Selectores del campo de contraseña"
        )
        return _clean_selector_list(value, label)

    @field_validator("submit_selectors", mode="before")
    @classmethod
    def _coerce_submit_selectors(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = value.splitlines()
        cleaned = []
        for selector in value:
            selector = (selector or "").strip()
            if selector and "\x00" not in selector and len(selector) <= _MAX_SELECTOR_LEN:
                if selector not in cleaned:
                    cleaned.append(selector)
        return cleaned

    @field_validator("strategy")
    @classmethod
    def _validate_strategy(cls, value: str) -> str:
        strategy = (value or "").strip().lower()
        if strategy not in STRATEGIES:
            raise PlatformConfigError(
                f"Estrategia no válida. Usa una de: {', '.join(STRATEGIES)}."
            )
        return strategy

    @field_validator("aliases", mode="before")
    @classmethod
    def _coerce_aliases(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [part.strip() for part in value.split(",")]
        aliases: List[str] = []
        for alias in value:
            alias = (alias or "").strip()
            if alias and alias not in aliases:
                aliases.append(alias)
        return aliases

    @model_validator(mode="after")
    def _validate_consistency(self) -> "PlatformConfig":
        normalized_alt: List[str] = []
        for alt in self.alt_domains:
            try:
                host = normalize_host(alt)
            except PlatformConfigError as exc:
                raise PlatformConfigError(
                    f"Dominio alternativo no válido: {alt!r}."
                ) from exc
            if host != self.domain and host not in normalized_alt:
                normalized_alt.append(host)
        self.alt_domains = normalized_alt

        login_host = host_from_url(self.login_url)
        if login_host is None:
            raise PlatformConfigError("La URL de inicio de sesión no es válida.")
        if login_host not in self.allowed_hosts:
            raise PlatformConfigError(
                "La URL de inicio de sesión debe pertenecer al dominio autorizado "
                f"({self.domain})."
            )
        return self

    # -------------------- Consultas de seguridad --------------------

    @property
    def allowed_hosts(self) -> List[str]:
        """Hosts exactos permitidos: dominio principal + alternativos."""
        return [self.domain, *self.alt_domains]

    def allows_url(self, url: str) -> bool:
        """
        True solo si la URL es HTTPS y su host coincide EXACTAMENTE con un
        dominio autorizado. No se aceptan sufijos ni subdominios implícitos.
        """
        raw = (url or "").strip()
        if not raw:
            return False
        try:
            parsed = urlsplit(raw)
        except ValueError:
            return False
        if parsed.scheme.lower() != "https":
            return False
        if not parsed.hostname:
            return False
        # Rechazar URLs con credenciales embebidas (p. ej. host@evil.com).
        if parsed.username or parsed.password:
            return False
        try:
            host = normalize_host(parsed.hostname)
        except PlatformConfigError:
            return False
        return host in self.allowed_hosts

    def matches_platform(self, platform: str) -> bool:
        """
        Indica si el nombre de plataforma de una cuenta corresponde a esta
        configuración (por nombre, alias o dominio escrito como plataforma).
        """
        token = _normalize_token(platform)
        if not token:
            return False

        candidates = {_normalize_token(self.name)}
        candidates.update(_normalize_token(alias) for alias in self.aliases)
        if token in candidates:
            return True

        raw = (platform or "").strip().lower()
        if "://" in raw or "." in raw:
            try:
                return normalize_host(raw) in self.allowed_hosts
            except PlatformConfigError:
                return False
        return False


# ====================== REPOSITORIO SQLITE ======================


def _row_to_config(row: sqlite3.Row) -> Optional[PlatformConfig]:
    """Convierte una fila SQLite en PlatformConfig, ignorando filas corruptas."""
    try:
        data: Dict[str, Any] = {
            "id": row["id"],
            "name": row["name"],
            "domain": row["domain"],
            "alt_domains": json.loads(row["alt_domains"] or "[]"),
            "login_url": row["login_url"],
            "username_selectors": json.loads(row["username_selectors"] or "[]"),
            "password_selectors": json.loads(row["password_selectors"] or "[]"),
            "submit_selectors": json.loads(row["submit_selectors"] or "[]"),
            "strategy": row["strategy"] or STRATEGY_CSS,
            "aliases": json.loads(row["aliases"] or "[]"),
            "enabled": bool(row["enabled"]),
            "notes": row["notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        return PlatformConfig(**data)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        logger.warning("Configuración de plataforma inválida en BD: %s", type(exc).__name__)
        return None


class PlatformConfigRepository:
    """CRUD de configuraciones de plataforma sobre la base SQLite existente."""

    def __init__(self, seed_defaults: bool = True):
        initialize_platform_configs_table()
        if seed_defaults:
            self.seed_defaults()

    # -------------------- Lectura --------------------

    def list_configs(self, enabled_only: bool = False) -> List[PlatformConfig]:
        query = "SELECT * FROM platform_configs"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name COLLATE NOCASE"

        with get_connection() as conn:
            rows = conn.execute(query).fetchall()

        configs: List[PlatformConfig] = []
        for row in rows:
            config = _row_to_config(row)
            if config is not None:
                configs.append(config)
        return configs

    def get(self, config_id: str) -> Optional[PlatformConfig]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM platform_configs WHERE id = ?", (config_id,)
            ).fetchone()
        return _row_to_config(row) if row else None

    def get_by_name(self, name: str) -> Optional[PlatformConfig]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM platform_configs WHERE name = ? COLLATE NOCASE",
                ((name or "").strip(),),
            ).fetchone()
        return _row_to_config(row) if row else None

    def find_for_platform(self, platform: str) -> Optional[PlatformConfig]:
        """
        Busca la configuración que corresponde a una plataforma.

        Prioriza coincidencias por nombre/alias y luego por dominio escrito
        como nombre de plataforma. Solo considera configuraciones activas.
        """
        configs = self.list_configs(enabled_only=True)
        for config in configs:
            if config.matches_platform(platform):
                return config
        return None

    # -------------------- Escritura --------------------

    def save(self, config: PlatformConfig) -> PlatformConfig:
        """Inserta o actualiza una configuración (upsert por id)."""
        now = datetime.now().isoformat()
        if not config.created_at:
            config.created_at = now
        config.updated_at = now

        values = (
            config.id,
            config.name,
            config.domain,
            json.dumps(config.alt_domains, ensure_ascii=False),
            config.login_url,
            json.dumps(config.username_selectors, ensure_ascii=False),
            json.dumps(config.password_selectors, ensure_ascii=False),
            json.dumps(config.submit_selectors, ensure_ascii=False),
            config.strategy,
            json.dumps(config.aliases, ensure_ascii=False),
            1 if config.enabled else 0,
            config.notes,
            config.created_at,
            config.updated_at,
        )

        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO platform_configs (
                        id, name, domain, alt_domains, login_url,
                        username_selectors, password_selectors, submit_selectors,
                        strategy, aliases, enabled, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name                = excluded.name,
                        domain              = excluded.domain,
                        alt_domains         = excluded.alt_domains,
                        login_url           = excluded.login_url,
                        username_selectors  = excluded.username_selectors,
                        password_selectors  = excluded.password_selectors,
                        submit_selectors    = excluded.submit_selectors,
                        strategy            = excluded.strategy,
                        aliases             = excluded.aliases,
                        enabled             = excluded.enabled,
                        notes               = excluded.notes,
                        updated_at          = excluded.updated_at
                    """,
                    values,
                )
        except sqlite3.IntegrityError as exc:
            raise PlatformConfigError(
                "Ya existe una plataforma con ese nombre."
            ) from exc

        logger.info(
            "Configuración de plataforma guardada: '%s' (%s)", config.name, config.domain
        )
        return config

    def delete(self, config_id: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM platform_configs WHERE id = ?", (config_id,)
            )
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Configuración de plataforma eliminada: id=%s", config_id)
        return deleted

    # -------------------- Datos iniciales --------------------

    def seed_defaults(self) -> int:
        """
        Inserta configuraciones iniciales solo si la tabla está vacía.

        Así se respetan las plataformas que el usuario haya eliminado y sus
        ajustes personalizados. Usa ON CONFLICT(name) DO NOTHING como defensa
        adicional ante ejecuciones concurrentes.
        """
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT COUNT(*) FROM platform_configs"
            ).fetchone()[0]
        if existing:
            return 0

        inserted = 0
        for data in DEFAULT_PLATFORM_CONFIGS:
            try:
                config = PlatformConfig(**data)
            except ValueError as exc:
                logger.error(
                    "Configuración inicial inválida para %r: %s",
                    data.get("name"),
                    type(exc).__name__,
                )
                continue

            now = datetime.now().isoformat()
            try:
                with get_connection() as conn:
                    cursor = conn.execute(
                        """
                        INSERT INTO platform_configs (
                            id, name, domain, alt_domains, login_url,
                            username_selectors, password_selectors, submit_selectors,
                            strategy, aliases, enabled, notes, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(name) DO NOTHING
                        """,
                        (
                            config.id,
                            config.name,
                            config.domain,
                            json.dumps(config.alt_domains, ensure_ascii=False),
                            config.login_url,
                            json.dumps(config.username_selectors, ensure_ascii=False),
                            json.dumps(config.password_selectors, ensure_ascii=False),
                            json.dumps(config.submit_selectors, ensure_ascii=False),
                            config.strategy,
                            json.dumps(config.aliases, ensure_ascii=False),
                            1 if config.enabled else 0,
                            config.notes,
                            now,
                            now,
                        ),
                    )
                    if cursor.rowcount > 0:
                        inserted += 1
            except sqlite3.IntegrityError:
                logger.debug("Configuración inicial ya existente: %s", config.name)

        if inserted:
            logger.info("%s configuración(es) de plataforma iniciales insertadas.", inserted)
        return inserted


# ====================== CONFIGURACIONES INICIALES ======================
# Nota: los selectores son un punto de partida editable desde la interfaz.
# Nunca incluyen credenciales; las contraseñas viven cifradas en `accounts`.

DEFAULT_PLATFORM_CONFIGS: List[Dict[str, Any]] = [
    {
        "name": "Google",
        "domain": "accounts.google.com",
        "aliases": ["google", "gmail", "correo google", "google workspace"],
        "login_url": "https://accounts.google.com/signin",
        "username_selectors": ['input[type="email"]', 'input[name="identifier"]'],
        "password_selectors": ['input[type="password"]', 'input[name="Passwd"]'],
        "strategy": STRATEGY_AUTO,
        "notes": "Puede mostrar el formulario en dos pasos.",
    },
    {
        "name": "GitHub",
        "domain": "github.com",
        "aliases": ["github", "git hub"],
        "login_url": "https://github.com/login",
        "username_selectors": ["#login_field", 'input[name="login"]'],
        "password_selectors": ["#password", 'input[name="password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Microsoft",
        "domain": "login.microsoftonline.com",
        "aliases": ["microsoft", "outlook", "hotmail", "office 365", "microsoft 365"],
        "login_url": "https://login.microsoftonline.com/",
        "username_selectors": ['input[type="email"]', 'input[name="loginfmt"]'],
        "password_selectors": ['input[type="password"]', 'input[name="passwd"]'],
        "strategy": STRATEGY_AUTO,
        "notes": "Puede mostrar el formulario en dos pasos.",
    },
    {
        "name": "Netflix",
        "domain": "www.netflix.com",
        "aliases": ["netflix"],
        "login_url": "https://www.netflix.com/login",
        "username_selectors": ["#id_userLoginId", 'input[name="userLoginId"]'],
        "password_selectors": ["#id_password", 'input[name="password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Facebook",
        "domain": "www.facebook.com",
        "aliases": ["facebook", "meta", "fb"],
        "login_url": "https://www.facebook.com/login",
        "username_selectors": ["#email", 'input[name="email"]'],
        "password_selectors": ["#pass", 'input[name="pass"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "X",
        "domain": "x.com",
        "alt_domains": ["www.x.com", "twitter.com", "www.twitter.com"],
        "aliases": ["x", "twitter"],
        "login_url": "https://x.com/i/flow/login",
        "username_selectors": ['input[autocomplete="username"]', 'input[name="text"]'],
        "password_selectors": ['input[name="password"]', 'input[autocomplete="current-password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Amazon",
        "domain": "www.amazon.com",
        "alt_domains": ["amazon.com"],
        "aliases": ["amazon"],
        "login_url": "https://www.amazon.com/ap/signin",
        "username_selectors": ["#ap_email", 'input[name="email"]'],
        "password_selectors": ["#ap_password", 'input[name="password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Steam",
        "domain": "store.steampowered.com",
        "aliases": ["steam"],
        "login_url": "https://store.steampowered.com/login/",
        "username_selectors": ["#input_username", 'input[type="text"]'],
        "password_selectors": ["#input_password", 'input[type="password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Spotify",
        "domain": "accounts.spotify.com",
        "aliases": ["spotify"],
        "login_url": "https://accounts.spotify.com/login",
        "username_selectors": ["#login-username", 'input[name="username"]'],
        "password_selectors": ["#login-password", 'input[name="password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Discord",
        "domain": "discord.com",
        "aliases": ["discord"],
        "login_url": "https://discord.com/login",
        "username_selectors": ['input[name="email"]', 'input[type="email"]'],
        "password_selectors": ['input[name="password"]', 'input[type="password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Twitch",
        "domain": "www.twitch.tv",
        "aliases": ["twitch"],
        "login_url": "https://www.twitch.tv/login",
        "username_selectors": ["#login-username", 'input[name="username"]'],
        "password_selectors": ["#password-input", 'input[name="password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Instagram",
        "domain": "www.instagram.com",
        "aliases": ["instagram", "ig"],
        "login_url": "https://www.instagram.com/accounts/login/",
        "username_selectors": ['input[name="username"]'],
        "password_selectors": ['input[name="password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "LinkedIn",
        "domain": "www.linkedin.com",
        "aliases": ["linkedin"],
        "login_url": "https://www.linkedin.com/login",
        "username_selectors": ["#username", 'input[name="session_key"]'],
        "password_selectors": ["#password", 'input[name="session_password"]'],
        "strategy": STRATEGY_AUTO,
    },
    {
        "name": "Reddit",
        "domain": "www.reddit.com",
        "aliases": ["reddit"],
        "login_url": "https://www.reddit.com/login/",
        "username_selectors": ["#login-username", 'input[name="username"]'],
        "password_selectors": ["#login-password", 'input[name="password"]'],
        "strategy": STRATEGY_AUTO,
    },
]
