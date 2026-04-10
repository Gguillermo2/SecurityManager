from core.account_manager  import AccountManager

FERNET_KEY = "clave"

def test_busqeuda():
    manager = AccountManager(FERNET_KEY)