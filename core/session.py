# core/session.py
from datetime import datetime, timedelta
from typing import Optional
import logging

from Modelo.models import AdminUser

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.current_user: Optional[AdminUser] = None
        self.fernet_key: Optional[bytes] = None
        self.session_start: Optional[datetime] = None
        self.session_timeout: timedelta = timedelta(minutes=5)  # Duración de la sesión en minutos
        
    def start_session(self, user: AdminUser, fernet_key: bytes):
        self.current_user = user
        self.fernet_key = fernet_key
        self.session_start = datetime.now()
        
    def is_session_valid(self) -> bool:
        if not self.session_start:
            return False
        return datetime.now() - self.session_start < self.session_timeout
    
    def refresh_session(self):
        """Renueva la sesión actualizando el tiempo de inicio a la hora actual."""
        if self.current_user:
            self.session_start = datetime.now()
            logger.debug(f"Sesión renovada para usuario: {self.current_user.username}")
        
    def end_session(self):
        self.current_user = None
        self.fernet_key = None
        self.session_start = None
        logger.info("Sesión finalizada")