# core/account_manager.py
from typing import List, Optional
from datetime import datetime
from Modelo.models import Account
from core.almacenamiento import save_accounts_data, load_accounts_data
from core.seguridad import generate_strong_password, encrypt_data_fernet, decrypt_data_fernet

class AccountManager:
    """Gestor CRUD para las cuentas de usuario"""
    
    def __init__(self, fernet_key: bytes):
        self.fernet_key = fernet_key
        self.accounts: List[Account] = []
        self.load_accounts()
    
    def load_accounts(self):
        """Carga todas las cuentas desde el almacenamiento"""
        self.accounts = load_accounts_data(self.fernet_key)
    
    def save_all_accounts(self):
        """Guarda todas las cuentas en el almacenamiento"""
        save_accounts_data(self.accounts, self.fernet_key)
    
    def create_account(self, platform: str, email_or_username: str, 
                    password: str, category: str, notes: str = "") -> Account:
        """Crea una nueva cuenta"""
        encrypted_password = encrypt_data_fernet(password, self.fernet_key)
        new_account = Account(
            platform=platform,
            email_or_username=email_or_username,
            password=encrypted_password,
            category=category,
            notes=notes,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.accounts.append(new_account)
        self.save_all_accounts()
        return new_account
    
    def get_account_byID(self, account_id: str) -> Optional[Account]:
        return next((acc for acc in self.accounts if acc.id == account_id), None)
    
    def update_account(self, account_id: str, **kwargs)-> bool:
        account = self.get_account_byID(account_id)
        if not account:
            return False 
        if 'password' in kwargs and kwargs['password'] is not None:
            kwargs['password'] = encrypt_data_fernet(kwargs['password'], self.fernet_key)
        for field, value in kwargs.items():
            if value is not None:
                setattr(account, field, value)
        
        account.updated_at = datetime.now().isoformat()
        self.save_all_accounts()
        return True
    
    def delete_account(self, account_id: str)-> bool:
        account =  self.get_account_byID(account_id)
        if not account:
            return False
        
        self.accounts.remove(account)
        self.save_all_accounts()
        return True


    def get_accounts_by_category(self, category: str) -> List[Account]:
        """Obtiene todas las cuentas de una categoría"""
        return [acc for acc in self.accounts 
                if acc.category.lower() == category.lower()]
    

    
    def search_accounts(self, query: str) -> List[Account]:
        """Busca cuentas por texto en plataforma o usuario/email"""
        query = query.lower()
        return [acc for acc in self.accounts 
                if query in acc.platform.lower() or 
                    query in acc.email_or_username.lower()]
    
    def get_decrypted_password(self, account_id: str) -> str:
        account = self.get_account_byID(account_id)
        if not account:
            return ""

        try:
            return decrypt_data_fernet(account.password, self.fernet_key)
        except Exception:
            return account.password
    
    def get_filtered_accounts(self, search: str = "", category: str = "Todas") -> List[Account]:
        """Obtiene cuentas filtradas por búsqueda y categoría"""
        accounts = self.accounts.copy()
        if category != "Todas":
            accounts = [acc for acc in accounts if acc.category == category]
        if search:
            search = search.lower()
            accounts = [
                acc for acc in accounts
                if search in acc.platform.lower()
                or search in acc.email_or_username.lower()
            ]
        return accounts
    
    def suggest_strong_password(self, length: int = 16) -> str:
        """Sugiere una contraseña fuerte"""
        return generate_strong_password(
            length=length,
            use_uppercase=True,
            use_lowercase=True,
            use_digits=True,
            use_symbols=True
        )
    
    def get_all_categories(self) -> List[str]:
        """Obtiene todas las categorías únicas"""
        categories = set(acc.category for acc in self.accounts)
        return sorted(list(categories))
    
    def get_accounts_summary(self) -> dict:
        """Obtiene un resumen de las cuentas"""
        summary = {
            'total': len(self.accounts),
            'by_category': {}
        }
        
        for category in self.get_all_categories():
            summary['by_category'][category] = len(
                self.get_accounts_by_category(category)
            )
        
        return summary