import uuid
from pydantic import BaseModel, Field
from typing import Optional

class AdminUser(BaseModel):
    username: str
    password: str 
    password_2fa: Optional[str] = None 

    fernet_key_salt: str

class Login(BaseModel):
    Nombre_user: str
    password : str  
    code : Optional[int] = None 


class Account(BaseModel):
    id: str  = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str
    email_or_username: str
    password: str
    category: str  # Nueva: videojuegos, correo, streaming, productividad
    notes: Optional[str] = None  # Para notas adicionales
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TwoFactorCode(BaseModel):
    code: str
    created_at: float  # timestamp
    expires_at: float  # timestamp
    is_used: bool = False
