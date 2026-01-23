"""
Aplicación principal Plotly Dash para diseño de estructuras de transmisión
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json
import os
import base64
import datetime
from pathlib import Path
import pandas as pd
import datetime

# Importar componentes propios
from components.menu import crear_menu_archivo, crear_menu_editar
from components.vista_home import crear_vista_home
from components.vista_configuracion import crear_vista_configuracion
from components.vista_ajuste_parametros import crear_vista_ajuste_parametros
from components.vista_eliminar_estructura import crear_vista_eliminar_estructura

from utils.estructura_manager import EstructuraManager
from utils.cable_manager import CableManager
from utils.validaciones import validar_estructura_json

# Inicializar la app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Diseño de Estructuras de Transmisión"
)

# Rutas de archivos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PLANTILLA_PATH = DATA_DIR / "plantilla.estructura.json"
CABLES_PATH = DATA_DIR / "cables.json"
ACTUAL_PATH = DATA_DIR / "actual.estructura.json"

# Inicializar managers
estructura_manager = EstructuraManager(DATA_DIR)
cable_manager = CableManager(CABLES_PATH)

# Variables globales de estado
estructura_actual = estructura_manager.cargar_estructura(PLANTILLA_PATH)
titulo_actual = estructura_actual.get("TITULO", "Nueva Estructura")

# Layout principal
app.layout = html.Div([
    # Almacenamiento de estado
    dcc.Store(id='estructura-actual', data=estructura_actual),
    dcc.Store(id='titulo-actual', data=titulo_actual),
    dcc.Store(id='vista-actual', data='home'),
    dcc.Store(id='cables-disponibles', data=cable_manager.obtener_cables()),
    dcc.Store(id='notificacion-temporal'),
    
    # URL para descargas
    dcc.Download(id="descargar-archivo"),
    
    # Upload para cargar archivos
    dcc.Upload(
        id='upload-estructura',
        children=html.Div(['Arrastrar o ', html.A('Seleccionar Archivo')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
            'display': 'none'  # Oculto, se activa mediante botón
        },
        multiple=False
    ),
    
    # Barra de navegación superior
    dbc.Navbar(
        dbc.Container([
            # Logo/Title
            dbc.NavbarBrand("Diseño de Estructuras", className="ms-2"),
            
            # Menús
            crear_menu_archivo(),
            crear_menu_editar(),
            
            # Indicador de estructura actual
            dbc.Nav([
                dbc.NavItem(
                    dbc.NavLink(
                        f"Estructura: {titulo_actual}",
                        id="indicador-estructura",
                        disabled=True,
                        style={'color': '#6c757d', 'font-weight': 'bold'}
                    )
                )
            ], className="ms-auto"),
            
            # Botón de ayuda
            dbc.Button(
                html.I(className="bi bi-question-circle"),
                id="btn-ayuda",
                color="link",
                className="ms-2",
                style={'color': '#6c757d'}
            )
        ]),
        color="light",
        dark=False,
        className="mb-4"
    ),
    
    # Contenedor principal
    dbc.Container([
        # Barra de progreso (oculta por defecto)
        dbc.Progress(
            id="progreso-calculo",
            value=0,
            striped=True,
            animated=True,
            style={'display': 'none'},
            className="mb-3"
        ),
        
        # Área de notificaciones
        dbc.Toast(
            id="toast-notificacion",
            header="Notificación",
            is_open=False,
            dismissable=True,
            icon="info",
            className="mb-3"
        ),
        
        # Contenido dinámico
        html.Div(id="contenido-principal")
    ], fluid=True, style={'padding': '20px'})
])

# Callbacks para navegación
@app.callback(
    Output("contenido-principal", "children"),
    Output("vista-actual", "data"),
    Input("menu-nueva-estructura", "n_clicks"),
    Input("menu-cargar-estructura", "n_clicks"),
    Input("menu-cargar-desde-pc", "n_clicks"),
    Input("menu-guardar-estructura", "n_clicks"),
    Input("menu-guardar-como", "n_clicks"),
    Input("menu-guardar-plantilla", "n_clicks"),
    Input("menu-ajustar-parametros", "n_clicks"),
    Input("menu-eliminar-estructura", "n_clicks"),
    Input("btn-volver-home", "n_clicks"),
    State("vista-actual", "data"),
    prevent_initial_call=True
)
def cambiar_vista(n1, n2, n3, n4, n5, n6, n7, n8, n9, vista_actual):
    ctx = dash.callback_context
    if not ctx.triggered:
        return crear_vista_home(), "home"
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    vistas = {
        "menu-nueva-estructura": ("configuracion", crear_vista_configuracion),
        "menu-cargar-estructura": ("cargar_db", crear_vista_home),  # Cambiará con modal
        "menu-cargar-desde-pc": ("cargar_pc", crear_vista_home),    # Cambiará con upload
        "menu-guardar-estructura": ("guardar", crear_vista_home),   # Ejecuta guardado
        "menu-guardar-como": ("guardar_como", crear_vista_home),    # Modal para guardar como
        "menu-guardar-plantilla": ("guardar_plantilla", crear_vista_home),
        "menu-ajustar-parametros": ("ajustar", crear_vista_ajuste_parametros),
        "menu-eliminar-estructura": ("eliminar", crear_vista_eliminar_estructura),
        "btn-volver-home": ("home", crear_vista_home)
    }
    
    if button_id in vistas:
        vista_nombre, vista_func = vistas[button_id]
        return vista_func(), vista_nombre
    
    return crear_vista_home(), "home"

# Callback para actualizar estructura actual
@app.callback(
    Output("estructura-actual", "data"),
    Output("titulo-actual", "data"),
    Output("indicador-estructura", "children"),
    Output("toast-notificacion", "is_open"),
    Output("toast-notificacion", "header"),
    Output("toast-notificacion", "children"),
    Input("guardar-parametros", "n_clicks"),
    Input("upload-estructura", "contents"),
    State("upload-estructura", "filename"),
    State("estructura-actual", "data"),
    State("titulo-actual", "data"),
    State({"type": "param-input", "index": ALL}, "id"),
    State({"type": "param-input", "index": ALL}, "value"),
    prevent_initial_call=True
)
def actualizar_estructura(guardar_clicks, upload_contents, filename, 
                         estructura_data, titulo_actual, inputs_ids, inputs_values):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, False, "", ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Guardar desde vista de ajuste de parámetros
    if trigger_id == "guardar-parametros":
        # Actualizar estructura con valores de inputs
        nueva_estructura = estructura_data.copy()
        
        for input_id, value in zip(inputs_ids, inputs_values):
            if value is not None:
                # Extraer la clave del parámetro del ID
                param_key = input_id['index']
                # Convertir tipos según corresponda
                if isinstance(nueva_estructura.get(param_key), bool):
                    value = bool(value)
                elif isinstance(nueva_estructura.get(param_key), int):
                    try:
                        value = int(float(value))
                    except:
                        value = int(value) if value else 0
                elif isinstance(nueva_estructura.get(param_key), float):
                    try:
                        value = float(value)
                    except:
                        value = float(value) if value else 0.0
                
                nueva_estructura[param_key] = value
        
        # Guardar en archivo actual
        estructura_manager.guardar_estructura(nueva_estructura, ACTUAL_PATH)
        
        mensaje = f"Estructura '{nueva_estructura.get('TITULO')}' actualizada correctamente"
        return (
            nueva_estructura,
            nueva_estructura.get('TITULO'),
            f"Estructura: {nueva_estructura.get('TITULO')}",
            True,
            "✅ Guardado Exitoso",
            mensaje
        )
    
    # Cargar desde upload
    elif trigger_id == "upload-estructura" and upload_contents:
        try:
            # Decodificar archivo
            content_type, content_string = upload_contents.split(',')
            decoded = base64.b64decode(content_string)
            
            # Verificar extensión
            if not filename.endswith('.estructura.json'):
                return (
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    True,
                    "❌ Error",
                    "El archivo debe tener extensión .estructura.json"
                )
            
            # Cargar JSON
            estructura_cargada = json.loads(decoded.decode('utf-8'))
            
            # Validar estructura
            if not validar_estructura_json(estructura_cargada):
                return (
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    True,
                    "❌ Error",
                    "Archivo de estructura inválido o corrupto."
                )
            
            # Guardar como actual
            estructura_manager.guardar_estructura(estructura_cargada, ACTUAL_PATH)
            
            mensaje = f"Estructura '{estructura_cargada.get('TITULO')}' cargada correctamente"
            return (
                estructura_cargada,
                estructura_cargada.get('TITULO'),
                f"Estructura: {estructura_cargada.get('TITULO')}",
                True,
                "✅ Carga Exitosa",
                mensaje
            )
            
        except Exception as e:
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                True,
                "❌ Error",
                f"Error al cargar archivo: {str(e)}"
            )
    
    return dash.no_update, dash.no_update, dash.no_update, False, "", ""

# Callback para cargar estructura desde DB
@app.callback(
    Output("estructura-actual", "data", allow_duplicate=True),
    Output("titulo-actual", "data", allow_duplicate=True),
    Output("indicador-estructura", "children", allow_duplicate=True),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Input("btn-cargar-db", "n_clicks"),
    State("select-estructura-db", "value"),
    prevent_initial_call=True
)
def cargar_desde_db(n_clicks, nombre_archivo):
    if not nombre_archivo:
        return dash.no_update, dash.no_update, dash.no_update, True, "⚠️ Advertencia", "Seleccione una estructura"
    
    try:
        ruta_archivo = DATA_DIR / nombre_archivo
        estructura_cargada = estructura_manager.cargar_estructura(ruta_archivo)
        
        # Guardar como actual
        estructura_manager.guardar_estructura(estructura_cargada, ACTUAL_PATH)
        
        mensaje = f"Estructura '{estructura_cargada.get('TITULO')}' cargada desde base de datos"
        return (
            estructura_cargada,
            estructura_cargada.get('TITULO'),
            f"Estructura: {estructura_cestructura_cargada.get('TITULO')}",
            True,
            "✅ Carga Exitosa",
            mensaje
        )
    except Exception as e:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            True,
            "❌ Error",
            f"Error al cargar: {str(e)}"
        )

# Callback para guardar estructura
@app.callback(
    Output("descargar-archivo", "data"),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Input("menu-guardar-estructura", "n_clicks"),
    Input("btn-guardar-db", "n_clicks"),
    Input("btn-guardar-pc", "n_clicks"),
    Input("btn-guardar-como-confirmar", "n_clicks"),
    Input("btn-guardar-plantilla-confirmar", "n_clicks"),
    State("estructura-actual", "data"),
    State("titulo-actual", "data"),
    State("input-titulo-nuevo", "value"),
    prevent_initial_call=True
)
def guardar_estructura(guardar_clicks, guardar_db, guardar_pc, guardar_como, 
                      guardar_plantilla, estructura_data, titulo_actual, titulo_nuevo):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, False, "", ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        # Guardar en base de datos (local)
        if trigger_id in ["menu-guardar-estructura", "btn-guardar-db"]:
            archivo_nombre = f"{titulo_actual}.estructura.json"
            ruta = DATA_DIR / archivo_nombre
            estructura_manager.guardar_estructura(estructura_data, ruta)
            
            mensaje = f"Estructura guardada en base de datos como '{archivo_nombre}'"
            return (
                dash.no_update,
                True,
                "✅ Guardado Exitoso",
                mensaje
            )
        
        # Guardar en PC (descargar)
        elif trigger_id == "btn-guardar-pc":
            archivo_nombre = f"{titulo_actual}.estructura.json"
            json_str = json.dumps(estructura_data, indent=2, ensure_ascii=False)
            
            mensaje = f"Descargando '{archivo_nombre}'"
            return (
                dict(content=json_str, filename=archivo_nombre),
                True,
                "⬇️ Descargando",
                mensaje
            )
        
        # Guardar como (con nuevo título)
        elif trigger_id == "btn-guardar-como-confirmar" and titulo_nuevo:
            # Actualizar título en estructura
            estructura_data["TITULO"] = titulo_nuevo
            archivo_nombre = f"{titulo_nuevo}.estructura.json"
            ruta = DATA_DIR / archivo_nombre
            estructura_manager.guardar_estructura(estructura_data, ruta)
            
            mensaje = f"Guardado como '{archivo_nombre}'"
            return (
                dash.no_update,
                True,
                "✅ Guardado Como",
                mensaje
            )
        
        # Guardar como plantilla
        elif trigger_id == "btn-guardar-plantilla-confirmar":
            estructura_manager.guardar_estructura(estructura_data, PLANTILLA_PATH)
            
            mensaje = "Plantilla actualizada correctamente"
            return (
                dash.no_update,
                True,
                "✅ Plantilla Guardada",
                mensaje
            )
    
    except Exception as e:
        return (
            dash.no_update,
            True,
            "❌ Error",
            f"Error al guardar: {str(e)}"
        )
    
    return dash.no_update, False, "", ""

# Callback para eliminar estructura
@app.callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Input("btn-eliminar-confirmar", "n_clicks"),
    State("select-estructura-eliminar", "value"),
    prevent_initial_call=True
)
def eliminar_estructura(n_clicks, nombre_archivo):
    if not nombre_archivo:
        return True, "⚠️ Advertencia", "Seleccione una estructura para eliminar"
    
    try:
        ruta_archivo = DATA_DIR / nombre_archivo
        
        # No permitir eliminar actual o plantilla
        if nombre_archivo == "actual.estructura.json":
            return True, "❌ Error", "No se puede eliminar la estructura actual"
        if nombre_archivo == "plantilla.estructura.json":
            return True, "❌ Error", "No se puede eliminar la plantilla"
        
        if ruta_archivo.exists():
            ruta_archivo.unlink()
            return True, "✅ Eliminado", f"Estructura '{nombre_archivo}' eliminada"
        else:
            return True, "⚠️ Advertencia", f"Archivo '{nombre_archivo}' no encontrado"
    
    except Exception as e:
        return True, "❌ Error", f"Error al eliminar: {str(e)}"

# Callback para mostrar/ocultar upload
@app.callback(
    Output("upload-estructura", "style"),
    Input("menu-cargar-desde-pc", "n_clicks"),
    State("upload-estructura", "style"),
    prevent_initial_call=True
)
def mostrar_upload(n_clicks, estilo_actual):
    if n_clicks:
        nuevo_estilo = estilo_actual.copy()
        nuevo_estilo['display'] = 'block'
        return nuevo_estilo
    return estilo_actual

# Inicializar estructura actual si no existe
if not ACTUAL_PATH.exists():
    estructura_manager.guardar_estructura(estructura_actual, ACTUAL_PATH)

if __name__ == '__main__':
    app.run(debug=True, port=8050)