#!/usr/bin/env python3
"""
Script de verificación para despliegue en Render
Verifica que todos los archivos y configuraciones estén listos
"""

import os
import sys
from pathlib import Path

# Cambiar al directorio del script
script_dir = Path(__file__).parent
os.chdir(script_dir)

def verificar_archivos_requeridos():
    """Verificar que existan todos los archivos necesarios para Render"""
    archivos_requeridos = [
        "app.py",
        "Procfile", 
        "requirements.txt",
        "runtime.txt",
        ".gitignore"
    ]
    
    print("Verificando archivos requeridos...")
    for archivo in archivos_requeridos:
        if Path(archivo).exists():
            print(f"  OK {archivo}")
        else:
            print(f"  ERROR {archivo} - FALTANTE")
            return False
    return True

def verificar_procfile():
    """Verificar contenido del Procfile"""
    print("\nVerificando Procfile...")
    try:
        with open("Procfile", "r") as f:
            contenido = f.read().strip()
        
        if "gunicorn app:server" in contenido:
            print("  OK Procfile configurado correctamente")
            return True
        else:
            print("  ERROR Procfile no contiene comando gunicorn correcto")
            return False
    except Exception as e:
        print(f"  ERROR leyendo Procfile: {e}")
        return False

def verificar_requirements():
    """Verificar requirements.txt"""
    print("\nVerificando requirements.txt...")
    dependencias_criticas = [
        "dash",
        "dash-bootstrap-components", 
        "pandas",
        "numpy",
        "matplotlib",
        "plotly",
        "gunicorn"
    ]
    
    try:
        with open("requirements.txt", "r") as f:
            contenido = f.read()
        
        for dep in dependencias_criticas:
            if dep in contenido:
                print(f"  OK {dep}")
            else:
                print(f"  ERROR {dep} - FALTANTE")
                return False
        return True
    except Exception as e:
        print(f"  ERROR leyendo requirements.txt: {e}")
        return False

def verificar_runtime():
    """Verificar runtime.txt"""
    print("\nVerificando runtime.txt...")
    try:
        with open("runtime.txt", "r") as f:
            version = f.read().strip()
        
        if version.startswith("python-3."):
            print(f"  OK Python version: {version}")
            return True
        else:
            print(f"  ERROR Version Python invalida: {version}")
            return False
    except Exception as e:
        print(f"  ERROR leyendo runtime.txt: {e}")
        return False

def verificar_app_py():
    """Verificar configuracion en app.py"""
    print("\nVerificando app.py...")
    try:
        with open("app.py", "r") as f:
            contenido = f.read()
        
        checks = [
            ("server = app.server", "Servidor Flask expuesto"),
            ("host='0.0.0.0'", "Host configurado para produccion"),
            ("APP_PORT", "Puerto configurable")
        ]
        
        for check, descripcion in checks:
            if check in contenido:
                print(f"  OK {descripcion}")
            else:
                print(f"  ERROR {descripcion} - NO ENCONTRADO")
                return False
        return True
    except Exception as e:
        print(f"  ERROR leyendo app.py: {e}")
        return False

def verificar_estructura_directorios():
    """Verificar estructura de directorios"""
    print("\nVerificando estructura de directorios...")
    directorios_requeridos = [
        "config",
        "components", 
        "controllers",
        "models",
        "utils",
        "views",
        "data"
    ]
    
    for directorio in directorios_requeridos:
        if Path(directorio).is_dir():
            print(f"  OK {directorio}/")
        else:
            print(f"  ERROR {directorio}/ - FALTANTE")
            return False
    return True

def verificar_version():
    """Verificar que la version este actualizada a 1.0"""
    print("\nVerificando version...")
    try:
        # Verificar en menu.py
        with open("components/menu.py", "r", encoding="utf-8") as f:
            contenido_menu = f.read()
        
        if "Versión 1.0" in contenido_menu:
            print("  OK Version 1.0 en modal 'Acerca de'")
        else:
            print("  ERROR Version no actualizada en modal")
            return False
            
        # Verificar en app_config.py
        with open("config/app_config.py", "r", encoding="utf-8") as f:
            contenido_config = f.read()
            
        if "v1.0" in contenido_config:
            print("  OK Version 1.0 en titulo de aplicacion")
        else:
            print("  AVISO Version no visible en titulo (opcional)")
            
        return True
    except Exception as e:
        print(f"  ERROR verificando version: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("VERIFICACION PARA DESPLIEGUE EN RENDER")
    print("=" * 50)
    
    verificaciones = [
        verificar_archivos_requeridos,
        verificar_procfile,
        verificar_requirements,
        verificar_runtime,
        verificar_app_py,
        verificar_estructura_directorios,
        verificar_version
    ]
    
    resultados = []
    for verificacion in verificaciones:
        resultado = verificacion()
        resultados.append(resultado)
    
    print("\n" + "=" * 50)
    if all(resultados):
        print("VERIFICACION EXITOSA!")
        print("La aplicación está lista para desplegar en Render")
        print("\nPróximos pasos:")
        print("1. Hacer commit de todos los cambios")
        print("2. Push al repositorio de GitHub")
        print("3. Conectar repositorio en Render.com")
        print("4. Configurar como Web Service")
        print("5. Desplegar")
        return 0
    else:
        print("VERIFICACION FALLIDA")
        print("Corrige los errores antes de desplegar")
        return 1

if __name__ == "__main__":
    sys.exit(main())