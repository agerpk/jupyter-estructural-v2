"""Script de prueba para verificar la arquitectura MVC"""

import sys
from pathlib import Path

def test_imports():
    """Verificar que todos los módulos se importan correctamente"""
    
    print("🔍 Verificando imports...")
    
    try:
        # Config
        from config.app_config import APP_TITLE, DATA_DIR, THEME
        print("✅ config.app_config")
        
        # Models
        from models.app_state import AppState
        print("✅ models.app_state")
        
        # Views
        from views.main_layout import crear_layout
        print("✅ views.main_layout")
        
        # Controllers
        from controllers import navigation_controller
        from controllers import file_controller
        from controllers import estructura_controller
        from controllers import parametros_controller
        from controllers import calculo_controller
        from controllers import ui_controller
        print("✅ controllers (todos)")
        
        print("\n✅ Todos los imports exitosos")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en imports: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_state():
    """Verificar que AppState funciona como Singleton"""
    
    print("\n🔍 Verificando AppState Singleton...")
    
    try:
        from models.app_state import AppState
        
        state1 = AppState()
        state2 = AppState()
        
        if state1 is state2:
            print("✅ AppState es Singleton (misma instancia)")
        else:
            print("❌ AppState NO es Singleton")
            return False
        
        # Verificar atributos
        assert hasattr(state1, 'estructura_manager')
        assert hasattr(state1, 'cable_manager')
        assert hasattr(state1, 'calculo_objetos')
        assert hasattr(state1, 'calculo_mecanico')
        print("✅ AppState tiene todos los managers")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en AppState: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Verificar configuración"""
    
    print("\n🔍 Verificando configuración...")
    
    try:
        from config.app_config import (
            APP_TITLE, APP_PORT, DEBUG_MODE,
            DATA_DIR, CABLES_PATH, ARCHIVO_ACTUAL,
            THEME, APP_STYLES, ARCHIVOS_PROTEGIDOS
        )
        
        print(f"  APP_TITLE: {APP_TITLE}")
        print(f"  APP_PORT: {APP_PORT}")
        print(f"  DATA_DIR: {DATA_DIR}")
        print(f"  THEME colors: {len(THEME)} definidos")
        print(f"  ARCHIVOS_PROTEGIDOS: {ARCHIVOS_PROTEGIDOS}")
        
        print("✅ Configuración cargada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False


def test_structure():
    """Verificar estructura de directorios"""
    
    print("\n🔍 Verificando estructura de directorios...")
    
    required_dirs = [
        "config",
        "models",
        "views",
        "controllers",
        "components",
        "utils"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ NO EXISTE")
            all_exist = False
    
    return all_exist


def main():
    """Ejecutar todas las pruebas"""
    
    print("=" * 60)
    print("PRUEBAS DE ARQUITECTURA MVC")
    print("=" * 60)
    
    results = []
    
    results.append(("Estructura de directorios", test_structure()))
    results.append(("Imports", test_imports()))
    results.append(("Configuración", test_config()))
    results.append(("AppState Singleton", test_app_state()))
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("La arquitectura MVC está correctamente implementada")
        print("\nPara ejecutar la aplicación:")
        print("  python app.py")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("Revisar los errores arriba")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
