# test_qr_generation.py
"""
Script de prueba para verificar que los códigos QR de TOTP se generan correctamente
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pyotp
import qrcode
from io import BytesIO

def test_qr_generation():
    """Prueba la generación de código QR TOTP"""
    
    # Generar un secreto TOTP
    secret = pyotp.random_base32()
    print(f"✅ Secreto TOTP generado: {secret}")
    print(f"   Longitud: {len(secret)} caracteres")
    
    # Verificar que el secreto es válido para pyotp
    try:
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        print(f"✅ Código TOTP actual válido: {current_code}")
    except Exception as e:
        print(f"❌ Error al generar código TOTP: {e}")
        return False
    
    # Generar URI para provisioning (escaneo QR)
    try:
        username = "testuser@gestor"
        uri = totp.provisioning_uri(name=username, issuer_name="GestorWroser")
        print(f"✅ URI de provisioning generada:")
        print(f"   {uri}")
        
        # Verificar que contiene elementos clave
        if "secret=" not in uri or "GestorWroser" not in uri:
            print("❌ URI no contiene elementos esperados")
            return False
            
    except Exception as e:
        print(f"❌ Error al generar URI: {e}")
        return False
    
    # Generar código QR
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=5,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar para inspección visual
        qr_path = "test_qr.png"
        img.save(qr_path)
        print(f"✅ Código QR guardado en: {qr_path}")
        
        # Verificar que no está vacío
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio_size = len(bio.getvalue())
        print(f"✅ Tamaño del QR: {bio_size} bytes (válido: > 100 bytes)")
        
        if bio_size < 100:
            print("❌ QR demasiado pequeño, posiblemente vacío")
            return False
            
    except Exception as e:
        print(f"❌ Error al generar QR: {e}")
        return False
    
    print("\n✅ TODAS LAS PRUEBAS PASARON")
    return True

if __name__ == "__main__":
    test_qr_generation()
