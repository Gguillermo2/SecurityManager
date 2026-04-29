# test_login_security.py
"""
Script de prueba para verificar el sistema de seguridad de login.
Prueba la funcionalidad de límite de intentos y bloqueo temporal.
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging
from core.logging_config import configure_logging
configure_logging()

# Inicializar BD
from core.almacenamiento import initialize_database
initialize_database()

# Importar funciones de prueba
from core.login_attempts import (
    is_user_locked_out,
    record_failed_login_attempt,
    record_successful_login_attempt,
    get_remaining_attempts,
    MAX_FAILED_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES
)

# Importar controlador
from controller.login_controller import LoginController

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_result(test_name, passed, details=""):
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"  {status}: {test_name}")
    if details:
        print(f"           {details}")

def test_login_attempts_recording():
    """Prueba 1: Verificar grabación de intentos."""
    print_header("TEST 1: Grabación de Intentos")
    
    test_user = "test_user_1"
    
    # Registrar algunos intentos fallidos
    for i in range(3):
        record_failed_login_attempt(test_user)
        time.sleep(0.1)
    
    remaining = get_remaining_attempts(test_user)
    expected_remaining = MAX_FAILED_ATTEMPTS - 3
    
    passed = remaining == expected_remaining
    print_result(
        "Registrar 3 intentos fallidos",
        passed,
        f"Intentos restantes: {remaining} (esperado: {expected_remaining})"
    )
    
    return passed

def test_lockout_activation():
    """Prueba 2: Verificar activación de bloqueo."""
    print_header("TEST 2: Activación de Bloqueo")
    
    test_user = "test_user_2"
    
    # Registrar 4 intentos para activar bloqueo
    for i in range(MAX_FAILED_ATTEMPTS):
        record_failed_login_attempt(test_user)
        time.sleep(0.1)
    
    is_locked, message = is_user_locked_out(test_user)
    
    passed = is_locked
    print_result(
        f"Usuario bloqueado después de {MAX_FAILED_ATTEMPTS} intentos",
        passed,
        f"Bloqueado: {is_locked}, Mensaje: {message[:50]}..."
    )
    
    return passed

def test_successful_login_clears_attempts():
    """Prueba 3: Login exitoso limpia intentos."""
    print_header("TEST 3: Login Exitoso Limpia Intentos")
    
    test_user = "test_user_3"
    
    # Registrar 2 intentos fallidos
    record_failed_login_attempt(test_user)
    record_failed_login_attempt(test_user)
    
    remaining_before = get_remaining_attempts(test_user)
    
    # Simular login exitoso
    record_successful_login_attempt(test_user)
    
    remaining_after = get_remaining_attempts(test_user)
    expected_after = MAX_FAILED_ATTEMPTS
    
    passed = remaining_after == expected_after
    print_result(
        "Intentos limpiados después de login exitoso",
        passed,
        f"Antes: {remaining_before}, Después: {remaining_after} (esperado: {expected_after})"
    )
    
    return passed

def test_controller_integration():
    """Prueba 4: Integración con LoginController."""
    print_header("TEST 4: Integración con LoginController")
    
    controller = LoginController()
    
    # Las credenciales exactas dependen de lo que exista en BD
    # Para esta prueba, usamos valores que probablemente fallen
    success, user, key, message = controller.authenticate("nonexistent_user", "wrongpass")
    
    # Debe fallar en la primera vez (intento 1 de 4)
    passed = not success and "Intentos restantes: 3" in message
    print_result(
        "Controller maneja incorrectamente credenciales",
        passed,
        f"Éxito: {success}, Mensaje: {message[:50]}..."
    )
    
    return passed

def test_remaining_attempts_calculation():
    """Prueba 5: Cálculo correcto de intentos restantes."""
    print_header("TEST 5: Cálculo de Intentos Restantes")
    
    test_user = "test_user_5"
    
    results = []
    for expected_remaining in [4, 3, 2, 1]:
        remaining = get_remaining_attempts(test_user)
        results.append(remaining)
        
        if remaining > 0:
            record_failed_login_attempt(test_user)
            time.sleep(0.1)
    
    expected_sequence = [4, 3, 2, 1]
    passed = results == expected_sequence
    
    print_result(
        "Secuencia de intentos correcta",
        passed,
        f"Secuencia: {results}, Esperado: {expected_sequence}"
    )
    
    return passed

def run_all_tests():
    """Ejecuta todas las pruebas."""
    print_header("🔐 PRUEBAS DE SEGURIDAD DE LOGIN")
    print(f"Configuración:")
    print(f"  - Máximo de intentos: {MAX_FAILED_ATTEMPTS}")
    print(f"  - Duración de bloqueo: {LOCKOUT_DURATION_MINUTES} minutos")
    print(f"  - Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        test_login_attempts_recording,
        test_lockout_activation,
        test_successful_login_clears_attempts,
        test_remaining_attempts_calculation,
        test_controller_integration,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n  ❌ ERROR EN PRUEBA: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Resumen
    print_header("📊 RESUMEN DE PRUEBAS")
    passed = sum(results)
    total = len(results)
    print(f"  Pruebas pasadas: {passed}/{total}")
    
    if passed == total:
        print(f"\n  ✅ ¡TODAS LAS PRUEBAS PASARON! Sistema listo.")
    else:
        print(f"\n  ⚠️  {total - passed} prueba(s) fallaron.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
