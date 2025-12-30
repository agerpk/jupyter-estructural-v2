"""
Script de prueba para verificar que la aplicación puede iniciarse
"""

try:
    print("🔍 Importando módulos principales...")
    
    # Importar configuración
    from config.app_config import APP_TITLE, APP_PORT, DEBUG_MODE
    print("✅ Configuración importada")
    
    # Importar layout
    from views.main_layout import crear_layout
    print("✅ Layout importado")
    
    # Importar AppState
    from models.app_state import AppState
    print("✅ AppState importado")
    
    # Probar importación de controladores uno por uno
    controladores = [
        "navigation_controller",
        "file_controller", 
        "estructura_controller",
        "parametros_controller",
        "calculo_controller",
        "ui_controller",
        "cables_controller",
        "geometria_controller",
        "mecanica_controller",
        "seleccion_poste_controller",
        "arboles_controller",
        "calcular_todo_controller",
        "home_controller",
        "nuevo_controller",
        "consola_controller",
        "fundacion_controller",
        "comparar_cables_controller"
    ]
    
    for controlador in controladores:
        try:
            exec(f"from controllers import {controlador}")
            print(f"✅ {controlador} importado")
        except Exception as e:
            print(f"❌ Error importando {controlador}: {e}")
    
    print("\n🔍 Probando creación de app Dash...")
    import dash
    import dash_bootstrap_components as dbc
    
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )
    print("✅ App Dash creada")
    
    print("\n🔍 Probando creación de layout...")
    layout = crear_layout()
    print("✅ Layout creado")
    
    app.layout = layout
    print("✅ Layout asignado")
    
    print("\n🔍 Probando registro de callbacks...")
    # Solo probar algunos controladores críticos
    try:
        from controllers import navigation_controller
        navigation_controller.register_callbacks(app)
        print("✅ navigation_controller registrado")
    except Exception as e:
        print(f"❌ Error registrando navigation_controller: {e}")
    
    try:
        from controllers import ui_controller
        ui_controller.register_callbacks(app)
        print("✅ ui_controller registrado")
    except Exception as e:
        print(f"❌ Error registrando ui_controller: {e}")
    
    print("\n✅ Prueba completada - La aplicación debería funcionar")
    
except Exception as e:
    print(f"❌ Error crítico: {e}")
    import traceback
    traceback.print_exc()