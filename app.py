"""
Aplicación principal - Arquitectura MVC
AGP - Análisis General de Postaciones
"""

import dash
import dash_bootstrap_components as dbc
import json
from datetime import datetime
from pathlib import Path

# Iniciar captura de consola ANTES de cualquier otra cosa
from utils.console_capture import get_console_capture
console_capture = get_console_capture()
console_capture.start()

from config.app_config import APP_TITLE, APP_PORT, DEBUG_MODE, APP_STYLES, DATA_DIR, CABLES_PATH
from views.main_layout import crear_layout
from models.app_state import AppState

# Importar controladores
from controllers import (
    navigation_controller,
    file_controller,
    estructura_controller,
    parametros_controller,
    calculo_controller,
    ui_controller,
    cables_controller,
    geometria_controller,
    mecanica_controller,
    seleccion_poste_controller,
    arboles_controller,
    calcular_todo_controller,
    home_controller,
    nuevo_controller,
    borrar_cache_controller,
    consola_controller,
    comparar_cables_controller,
    fundacion_controller
)

# Inicializar la aplicación Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = APP_TITLE
server = app.server  # Exponer el servidor Flask para Gunicorn

# Desactivar hot reload completamente
app.config.suppress_callback_exceptions = True
if hasattr(app, '_dev_tools'):
    app._dev_tools.hot_reload = False
    app._dev_tools.ui = False

# Aplicar estilos personalizados
app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            {APP_STYLES}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
'''

# Configurar layout
app.layout = crear_layout()

# Registrar todos los controladores
navigation_controller.register_callbacks(app)
file_controller.register_callbacks(app)
estructura_controller.register_callbacks(app)
parametros_controller.register_callbacks(app)
calculo_controller.register_callbacks(app)
ui_controller.register_callbacks(app)
cables_controller.register_callbacks(app)
geometria_controller.register_callbacks(app)
mecanica_controller.register_callbacks(app)
seleccion_poste_controller.register_callbacks(app)
arboles_controller.register_callbacks(app)
calcular_todo_controller.register_callbacks(app)
home_controller.register_callbacks(app)
nuevo_controller.register_callbacks(app)
consola_controller.register_callbacks(app)
fundacion_controller.registrar_callbacks_fundacion(app)
comparar_cables_controller.registrar_callbacks_comparar_cables(app)
# borrar_cache_controller no requiere register_callbacks - usa decorador @callback directo


def inicializar_datos():
    """Inicializar datos base de la aplicación"""
    
    state = AppState()
    
    # Crear directorio data si no existe
    DATA_DIR.mkdir(exist_ok=True)
    
    # Asegurar que exista el archivo de cables
    if not CABLES_PATH.exists():
        cables_base = {
            "AlAc 435/55": {
                "nombre": "Aluminio-Acero 435/55",
                "diametro": 27.7,
                "seccion": 435.0,
                "peso": 1.441
            },
            "OPGW FiberHome 24FO 58mm2": {
                "nombre": "OPGW FiberHome 24FO 58mm²",
                "diametro": 11.5,
                "seccion": 58.0,
                "peso": 0.418
            }
        }
        CABLES_PATH.write_text(json.dumps(cables_base, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Asegurar que exista el archivo de plantilla
    if not state.estructura_manager.plantilla_path.exists():
        estructura_base = {
            "TIPO_ESTRUCTURA": "Suspensión Recta",
            "Zona_climatica": "D",
            "exposicion": "C",
            "clase": "C",
            "TITULO": "Plantilla por Defecto",
            "cable_conductor_id": "AlAc 435/55",
            "cable_guardia_id": "OPGW FiberHome 24FO 58mm2",
            "Vmax": 38.9,
            "Vmed": 15.56,
            "Vtormenta": 20,
            "t_hielo": 0.01,
            "Q": 0.0613,
            "Zco": 13,
            "Zcg": 13,
            "Zca": 13,
            "Zes": 10,
            "Cf_cable": 1,
            "Cf_guardia": 1,
            "Cf_cadena": 0.9,
            "Cf_estructura": 0.9,
            "L_vano": 400,
            "alpha": 0,
            "theta": 45,
            "A_cadena": 0.03,
            "PCADENA": 10.5,
            "PESTRUCTURA": 3900,
            "A_estr_trans": 2.982,
            "A_estr_long": 4.482,
            "FORZAR_N_POSTES": 1,
            "FORZAR_ORIENTACION": "No",
            "PRIORIDAD_DIMENSIONADO": "altura_libre",
            "TENSION": 220,
            "Zona_estructura": "Rural",
            "Lk": 2.5,
            "ANG_APANTALLAMIENTO": 30,
            "AJUSTAR_POR_ALTURA_MSNM": True,
            "METODO_ALTURA_MSNM": "AEA 3%/300m",
            "Altura_MSNM": 3000,
            "DISPOSICION": "triangular",
            "TERNA": "Doble",
            "CANT_HG": 2,
            "HG_CENTRADO": False,
            "ALTURA_MINIMA_CABLE": 6.5,
            "LONGITUD_MENSULA_MINIMA_CONDUCTOR": 1.3,
            "LONGITUD_MENSULA_MINIMA_GUARDIA": 0.2,
            "HADD": 0.4,
            "HADD_ENTRE_AMARRES": 0.2,
            "HADD_HG": 1.5,
            "HADD_LMEN": 0.5,
            "ANCHO_CRUCETA": 0.3,
            "AUTOAJUSTAR_LMENHG": True,
            "DIST_REPOSICIONAR_HG": 0.1,
            "MOSTRAR_C2": False,
            "SALTO_PORCENTUAL": 0.05,
            "PASO_AFINADO": 0.005,
            "OBJ_CONDUCTOR": "FlechaMin",
            "OBJ_GUARDIA": "TiroMin",
            "RELFLECHA_MAX_GUARDIA": 0.95,
            "RELFLECHA_SIN_VIENTO": True,
            "ZOOM_CABEZAL": 0.95,
            "REEMPLAZAR_TITULO_GRAFICO": False,
            "Vn": 220,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
            "version": "1.0",
            "fecha_modificacion": datetime.now().isoformat()
        }
        state.estructura_manager.guardar_estructura(estructura_base, state.estructura_manager.plantilla_path)


if __name__ == '__main__':
    inicializar_datos()
    app.run(debug=DEBUG_MODE, port=APP_PORT, host='0.0.0.0')
