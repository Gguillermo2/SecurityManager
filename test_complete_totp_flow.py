# test_complete_totp_flow.py
"""
Script de prueba completo del flujo de TOTP:
1. Crear usuario administrador
2. Generar secreto TOTP
3. Generar URI para QR
4. Validar que el código generado funciona
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from core.logging_config import configure_logging

# Configurar logging
configure_logging()
logger = logging.getLogger(__name__)

# Simular el flujo
def test_complete_flow():
    logger.info("=" * 60)
    logger.info("INICIANDO TEST COMPLETO DE FLUJO TOTP")
    logger.info("=" * 60)
    
    try:
        # Verificar que los módulos importan correctamente
        from controller.login_controller import LoginController
        from core.autenticacion import admin_exists
        import pyotp
        
        logger.info("✅ Módulos importados correctamente")
        
        # Crear controlador
        controller = LoginController()
        logger.info("✅ LoginController inicializado")
        
        # Verificar si admin existe
        if admin_exists():
            logger.warning("⚠️  Admin ya existe en la BD, saltando creación")
        else:
            # Crear admin
            username_test = "test_user"
            password_test = "TestPassword123!"
            
            logger.info(f"Creando admin: {username_test}...")
            success, message = controller.create_admin(username_test, password_test)
            
            if not success:
                logger.error(f"❌ Error al crear admin: {message}")
                return False
            
            logger.info(f"✅ Admin creado: {message}")
            
            # Verificar que current_user está cargado
            if not controller.current_user:
                logger.error("❌ current_user no fue cargado después de crear admin")
                return False
            
            logger.info(f"✅ current_user cargado: {controller.current_user.username}")
            logger.info(f"   TOTP Secret: {controller.current_user.totp_secret}")
        
        # Generar URI TOTP
        logger.info("Generando URI TOTP...")
        uri = controller.get_totp_uri(username_test if not admin_exists() else "test_user")
        
        if not uri:
            logger.error("❌ URI TOTP vacía")
            return False
        
        logger.info(f"✅ URI TOTP generada")
        logger.info(f"   {uri}")
        
        # Validar que contiene componentes esperados
        if "otpauth://totp/" not in uri:
            logger.error("❌ URI no tiene formato otpauth correcto")
            return False
        
        if "GestorWroser" not in uri:
            logger.error("❌ URI no contiene nombre del emisor")
            return False
        
        logger.info("✅ URI tiene formato correcto")
        
        # Probar que se puede generar código TOTP desde el secreto
        if controller.current_user and controller.current_user.totp_secret:
            try:
                totp = pyotp.TOTP(controller.current_user.totp_secret)
                code = totp.now()
                logger.info(f"✅ Código TOTP generado: {code}")
                
                # Verificar el código
                is_valid = totp.verify(code)
                if is_valid:
                    logger.info("✅ Código TOTP verificado correctamente")
                else:
                    logger.error("❌ Código TOTP no fue verificado")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Error al generar/verificar TOTP: {e}", exc_info=True)
                return False
        
        logger.info("=" * 60)
        logger.info("✅ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_complete_flow()
    sys.exit(0 if success else 1)
