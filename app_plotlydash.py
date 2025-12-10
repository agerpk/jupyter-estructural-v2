"""
Aplicación principal de visualización y gestión de estructuras
"""

import dash
from dash import html, dcc, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import json
import os
from datetime import datetime
from pathlib import Path

# Importar componentes personalizados
from components.menu import (
    crear_menu_archivo, 
    crear_menu_editar,
    crear_menu_calcular,
    crear_modal_cargar_db, 
    crear_modal_guardar_como,
    crear_modal_guardar_plantilla,
    crear_modal_nueva_estructura
)
from components.vista_home import crear_vista_home
from components.vista_ajuste_parametros import crear_vista_ajuste_parametros
from components.vista_eliminar_estructura import crear_vista_eliminar_estructura
from components.vista_configuracion import crear_vista_configuracion
from components.vista_calculo_mecanico import crear_vista_calculo_mecanico, crear_tabla_estados_climaticos

# Importar utilidades
from utils.cable_manager import CableManager
from utils.estructura_manager import EstructuraManager
from utils.validaciones import validar_estructura_json, validar_nombre_archivo
from utils.calculo_objetos import CalculoObjetosAEA
from utils.calculo_mecanico_cables import CalculoMecanicoCables
from utils.plot_flechas import crear_grafico_flechas

# Inicializar la aplicación Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = "AGP - Análisis General de Postaciones"

# Estilos personalizados
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #0e1012 !important;
                color: #d1d5db !important;
            }
            .navbar {
                background-color: #0e1012 !important;
            }
            .container-fluid, .container {
                background-color: #0e1012 !important;
            }
            .card {
                background-color: #1a1d21 !important;
                border-color: #2d3139 !important;
                color: #d1d5db !important;
            }
            .modal-content {
                background-color: #1a1d21 !important;
                color: #d1d5db !important;
            }
            .form-control, .form-select {
                background-color: #1a1d21 !important;
                border-color: #2d3139 !important;
                color: #d1d5db !important;
            }
            .btn-primary {
                background-color: #2084f2 !important;
                border-color: #2084f2 !important;
            }
            .badge {
                background-color: #2084f2 !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


# Inicializar managers
data_dir = Path("data")
cables_path = data_dir / "cables.json"
estructura_manager = EstructuraManager(data_dir)
cable_manager = CableManager(cables_path)
calculo_objetos = CalculoObjetosAEA()
calculo_mecanico = CalculoMecanicoCables(calculo_objetos)

# Ruta del archivo actual
archivo_actual = Path("actual.estructura.json")

# Cargar estructura actual o plantilla por defecto
def cargar_estructura_actual():
    """Cargar la estructura actual o la plantilla por defecto"""
    try:
        if archivo_actual.exists():
            return estructura_manager.cargar_estructura(archivo_actual)
    except Exception as e:
        print(f"Error cargando estructura actual: {e}")
    
    # Cargar plantilla por defecto
    estructura = estructura_manager.cargar_plantilla()
    
    # Guardar como actual
    estructura_manager.guardar_estructura(estructura, archivo_actual)
    
    return estructura

# Layout principal
app.layout = html.Div([
    # Almacenamiento de estado
    dcc.Store(id="estructura-actual", data=cargar_estructura_actual()),
    dcc.Store(id="estructuras-disponibles", data=estructura_manager.listar_estructuras()),
    
    # Barra de navegación superior
    dbc.Navbar(
        dbc.Container([
            # Logo y botón INICIO
            dbc.Row([
                dbc.Col(html.I(className="fas fa-bolt fa-2x text-warning"), width="auto"),
                dbc.Col(
                    dbc.Button(
                        "INICIO",
                        id="btn-inicio",
                        color="link",
                        className="text-white fw-bold",
                        style={"textDecoration": "none", "fontSize": "1.25rem"}
                    ),
                    width="auto"
                ),
            ], align="center", className="g-0"),
            
            # Menús
            dbc.Nav([
                crear_menu_archivo(),
                crear_menu_editar(),
                crear_menu_calcular(),
            ], navbar=True),
            
            # Información de estructura actual
            dbc.Nav([
                dbc.NavItem(
                    dbc.Badge(
                        id="badge-estructura-actual",
                        color="info",
                        className="ms-2"
                    )
                ),
            ], navbar=True, className="ms-auto"),
        ]),
        color="dark",
        dark=True,
        className="mb-4",
    ),
    
    # Contenedor principal
    dbc.Container([
        # Modal para cargar desde DB
        crear_modal_cargar_db(estructura_manager.listar_estructuras()),
        
        # Modal para guardar como
        crear_modal_guardar_como(""),
        
        # Modal para guardar plantilla
        crear_modal_guardar_plantilla(),

        # Modal para nueva estructura
        crear_modal_nueva_estructura(),

        # Área de contenido principal
        html.Div(id="contenido-principal", children=crear_vista_home()),
    ], fluid=True),
    
    # Toasts para notificaciones
    dbc.Toast(
        id="toast-notificacion",
        header="Notificación",
        is_open=False,
        dismissable=True,
        duration=4000,
        className="position-fixed top-0 end-0 m-3",
        style={"zIndex": 1000},
    ),
    
    # Componente para cargar archivos (para cargar desde computadora)
    dcc.Upload(
        id="upload-estructura",
        children=html.Div(["Arrastra o ", html.A("Selecciona un archivo")]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
            'display': 'none'  # Oculto, se activa desde el menú
        },
        multiple=False,
        accept='.json,.estructura.json'
    ),
    dcc.Download(id="download-estructura"),


])

# ============================================================================
# CALLBACKS PARA NAVEGACIÓN
# ============================================================================

@app.callback(
    Output("contenido-principal", "children"),
    Input("btn-inicio", "n_clicks"),
    Input({"type": "btn-volver", "index": ALL}, "n_clicks"),
    Input("menu-ajustar-parametros", "n_clicks"),
    Input("menu-eliminar-estructura", "n_clicks"),
    Input("menu-nueva-estructura", "n_clicks"),
    Input("menu-guardar-estructura", "n_clicks"),
    Input("menu-calculo-mecanico", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def navegar_vistas(n_clicks_inicio, btn_volver_clicks, n_clicks_ajustar, 
                   n_clicks_eliminar, n_clicks_nueva, n_clicks_guardar, n_clicks_cmc, estructura_actual):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return crear_vista_home()
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Navegación a Inicio
    if trigger_id == "btn-inicio":
        return crear_vista_home()
    
    # Navegación a Ajustar Parámetros
    elif trigger_id == "menu-ajustar-parametros":
        cables_disponibles = cable_manager.obtener_cables()
        return crear_vista_ajuste_parametros(estructura_actual, cables_disponibles)
    
    elif trigger_id == "menu-eliminar-estructura":
        return crear_vista_eliminar_estructura()
    
    elif trigger_id == "menu-calculo-mecanico":
        return crear_vista_calculo_mecanico(estructura_actual)
    
    # Botones Volver
    elif "btn-volver" in trigger_id:
        try:
            trigger_json = json.loads(trigger_id.replace("'", '"'))
            if trigger_json.get("type") == "btn-volver":
                return crear_vista_home()
                
        except:
            pass
    
    # Nueva Estructura - ahora se maneja en un callback separado
    elif trigger_id == "menu-nueva-estructura":
        return dash.no_update
    
    # Guardar Estructura - ahora se maneja en un callback separado
    elif trigger_id == "menu-guardar-estructura":
        return dash.no_update

    return crear_vista_home()

# ============================================================================
# CALLBACKS PARA OPERACIONES DE ARCHIVO
# ============================================================================

@app.callback(
    Output("modal-cargar-db", "is_open"),
    Input("menu-cargar-estructura", "n_clicks"),
    Input("btn-cancelar-db", "n_clicks"),
    Input("btn-cargar-db", "n_clicks"),
    State("modal-cargar-db", "is_open"),
    prevent_initial_call=True
)
def toggle_modal_cargar_db(abrir, cancelar, cargar, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "menu-cargar-estructura":
        return True
    elif trigger_id in ["btn-cancelar-db", "btn-cargar-db"]:
        return False
    
    return is_open
# Callback para actualizar lista de estructuras al abrir modal
@app.callback(
    Output("select-estructura-db", "options"),
    Input("modal-cargar-db", "is_open"),
    prevent_initial_call=True
)
def actualizar_lista_estructuras_modal(is_open):
    if is_open:
        estructuras = estructura_manager.listar_estructuras()
        return [{"label": e, "value": e} for e in estructuras]
    return dash.no_update

@app.callback(
    Output("modal-guardar-como", "is_open"),
    Output("input-titulo-nuevo", "value"),
    Input("menu-guardar-como", "n_clicks"),
    Input("btn-cancelar-como", "n_clicks"),
    Input("btn-guardar-como-confirmar", "n_clicks"),
    State("modal-guardar-como", "is_open"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def toggle_modal_guardar_como(abrir, cancelar, guardar, is_open, estructura_actual):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, ""
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "menu-guardar-como":
        titulo_actual = estructura_actual.get("TITULO", "Nueva Estructura")
        return True, titulo_actual
    elif trigger_id in ["btn-cancelar-como", "btn-guardar-como-confirmar"]:
        return False, ""
    
    return is_open, ""

@app.callback(
    Output("modal-guardar-plantilla", "is_open"),
    Input("menu-guardar-plantilla", "n_clicks"),
    Input("btn-cancelar-plantilla", "n_clicks"),
    Input("btn-guardar-plantilla-confirmar", "n_clicks"),
    State("modal-guardar-plantilla", "is_open"),
    prevent_initial_call=True
)
def toggle_modal_guardar_plantilla(abrir, cancelar, guardar, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "menu-guardar-plantilla":
        return True
    elif trigger_id in ["btn-cancelar-plantilla", "btn-guardar-plantilla-confirmar"]:
        return False
    
    return is_open

# ============================================================================
# CALLBACKS PARA GESTIÓN DE ESTRUCTURAS
# ============================================================================

@app.callback(
    Output("estructura-actual", "data", allow_duplicate=True),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("btn-cargar-db", "n_clicks"),
    State("select-estructura-db", "value"),
    prevent_initial_call=True
)
def cargar_estructura_desde_db(n_clicks, nombre_estructura):
    if not nombre_estructura:
        return dash.no_update, True, "Error", "Seleccione una estructura", "danger", "danger"
    
    try:
        # Construir la ruta del archivo
        ruta_estructura = data_dir / nombre_estructura
        
        # Cargar la estructura
        estructura = estructura_manager.cargar_estructura(ruta_estructura)
        
        if estructura:
            # Guardar como estructura actual
            estructura_manager.guardar_estructura(estructura, archivo_actual)
            
            return estructura, True, "Éxito", f"Estructura '{nombre_estructura}' cargada correctamente", "success", "success"
    except Exception as e:
        print(f"Error cargando estructura: {e}")
    
    return dash.no_update, True, "Error", "No se pudo cargar la estructura", "danger", "danger"

@app.callback(
    Output("estructura-actual", "data", allow_duplicate=True),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("btn-guardar-como-confirmar", "n_clicks"),
    State("input-titulo-nuevo", "value"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def guardar_estructura_como(n_clicks, nuevo_titulo, estructura_actual):
    if not nuevo_titulo or not nuevo_titulo.strip():
        return dash.no_update, True, "Error", "Ingrese un título válido", "danger", "danger"
    
    try:
        # Actualizar título en la estructura
        estructura_actualizada = estructura_actual.copy()
        estructura_actualizada["TITULO"] = nuevo_titulo.strip()
        
        # Crear nombre de archivo
        nombre_archivo = f"{nuevo_titulo.strip()}.estructura.json"
        ruta_destino = data_dir / nombre_archivo
        
        # Guardar con el nuevo nombre
        estructura_manager.guardar_estructura(estructura_actualizada, ruta_destino)
        
        # También guardar como actual
        estructura_manager.guardar_estructura(estructura_actualizada, archivo_actual)
        
        return estructura_actualizada, True, "Éxito", f"Estructura guardada como '{nuevo_titulo}'", "success", "success"
    except Exception as e:
        print(f"Error guardando estructura: {e}")
    
    return dash.no_update, True, "Error", "No se pudo guardar la estructura", "danger", "danger"

@app.callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("btn-guardar-plantilla-confirmar", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def guardar_como_plantilla(n_clicks, estructura_actual):
    try:
        # Guardar como plantilla
        estructura_manager.guardar_estructura(estructura_actual, estructura_manager.plantilla_path)
        
        return True, "Éxito", "Plantilla actualizada correctamente", "success", "success"
    except Exception as e:
        print(f"Error guardando plantilla: {e}")
        return True, "Error", "No se pudo guardar la plantilla", "danger", "danger"

# Callback para abrir/cerrar modal nueva estructura
@app.callback(
    Output("modal-nueva-estructura", "is_open"),
    Output("input-nombre-nueva-estructura", "value"),
    Input("menu-nueva-estructura", "n_clicks"),
    Input("btn-cancelar-nueva", "n_clicks"),
    Input("btn-crear-nueva-confirmar", "n_clicks"),
    State("modal-nueva-estructura", "is_open"),
    prevent_initial_call=True
)
def toggle_modal_nueva_estructura(abrir, cancelar, crear, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, ""
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "menu-nueva-estructura":
        return True, ""
    elif trigger_id in ["btn-cancelar-nueva", "btn-crear-nueva-confirmar"]:
        return False, ""
    
    return is_open, ""

# Callback para crear nueva estructura
@app.callback(
    Output("estructura-actual", "data", allow_duplicate=True),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("btn-crear-nueva-confirmar", "n_clicks"),
    State("input-nombre-nueva-estructura", "value"),
    prevent_initial_call=True
)
def crear_nueva_estructura_callback(n_clicks, nombre):
    if not nombre or not nombre.strip():
        return dash.no_update, True, "Error", "Ingrese un nombre válido", "danger", "danger"
    
    try:
        # Crear nueva estructura con el nombre especificado
        nueva_estructura = estructura_manager.crear_nueva_estructura(titulo=nombre.strip())
        
        # Guardar como actual
        estructura_manager.guardar_estructura(nueva_estructura, archivo_actual)
        
        return nueva_estructura, True, "Éxito", f"Nueva estructura '{nombre.strip()}' creada", "success", "success"
    except Exception as e:
        return dash.no_update, True, "Error", f"Error al crear estructura: {str(e)}", "danger", "danger"


# Callback para guardar estructura en DB
@app.callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("menu-guardar-estructura", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def guardar_estructura_db(n_clicks, estructura_actual):
    if estructura_actual and "TITULO" in estructura_actual:
        try:
            titulo = estructura_actual["TITULO"]
            nombre_archivo = f"{titulo}.estructura.json"
            estructura_manager.guardar_estructura(estructura_actual, data_dir / nombre_archivo)
            return True, "Éxito", f"Estructura guardada: {nombre_archivo}", "success", "success"
        except Exception as e:
            return True, "Error", f"Error al guardar: {str(e)}", "danger", "danger"
    return True, "Error", "No hay estructura para guardar", "danger", "danger"

# Callback para descargar estructura a PC
@app.callback(
    Output("download-estructura", "data"),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("menu-descargar-estructura", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def descargar_estructura_pc(n_clicks, estructura_actual):
    if estructura_actual and "TITULO" in estructura_actual:
        try:
            titulo = estructura_actual["TITULO"]
            nombre_archivo = f"{titulo}.estructura.json"
            contenido = json.dumps(estructura_actual, indent=2, ensure_ascii=False)
            return (
                dict(content=contenido, filename=nombre_archivo),
                True, "Éxito", f"Estructura descargada: {nombre_archivo}", "success", "success"
            )
        except Exception as e:
            return dash.no_update, True, "Error", f"Error al descargar: {str(e)}", "danger", "danger"
    return dash.no_update, True, "Error", "No hay estructura para descargar", "danger", "danger"

# ============================================================================
# CALLBACKS PARA AJUSTE DE PARÁMETROS
# ============================================================================

@app.callback(
    Output("estructura-actual", "data", allow_duplicate=True),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("guardar-parametros", "n_clicks"),
    State({"type": "param-input", "index": ALL}, "id"),
    State({"type": "param-input", "index": ALL}, "value"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def guardar_parametros_ajustados(n_clicks, param_ids, param_values, estructura_actual):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    try:
        # Crear copia de la estructura actual
        estructura_actualizada = estructura_actual.copy()
        
        # Actualizar parámetros modificados
        for param_id, param_value in zip(param_ids, param_values):
            if param_id and "index" in param_id:
                param_key = param_id["index"]
                
                # Convertir tipos según el valor original
                if param_key in estructura_actual:
                    original_value = estructura_actual[param_key]
                    
                    # Mantener tipo de dato
                    if isinstance(original_value, bool):
                        estructura_actualizada[param_key] = bool(param_value)
                    elif isinstance(original_value, int):
                        try:
                            estructura_actualizada[param_key] = int(float(param_value))
                        except:
                            estructura_actualizada[param_key] = param_value
                    elif isinstance(original_value, float):
                        try:
                            estructura_actualizada[param_key] = float(param_value)
                        except:
                            estructura_actualizada[param_key] = param_value
                    else:
                        estructura_actualizada[param_key] = param_value
                else:
                    estructura_actualizada[param_key] = param_value
        
        # Guardar en archivo actual
        estructura_manager.guardar_estructura(estructura_actualizada, archivo_actual)
        
        # Notificación de éxito
        return (
            estructura_actualizada,
            True, 
            "Éxito", 
            "Parámetros guardados correctamente", 
            "success", 
            "success"
        )
        
    except Exception as e:
        print(f"Error guardando parámetros: {e}")
        return (
            dash.no_update,
            True,
            "Error",
            f"Error al guardar parámetros: {str(e)}",
            "danger",
            "danger"
        )

# ============================================================================
# CALLBACKS PARA CARGA DESDE COMPUTADORA
# ============================================================================

@app.callback(
    Output("upload-estructura", "style", allow_duplicate=True),
    Input("menu-cargar-desde-pc", "n_clicks"),
    prevent_initial_call=True
)
def mostrar_upload_component(n_clicks):
    """Mostrar el componente de upload cuando se hace clic en el menú"""
    if n_clicks:
        return {
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
            'display': 'block'
        }
    return dash.no_update

@app.callback(
    Output("estructura-actual", "data", allow_duplicate=True),
    Output("upload-estructura", "style", allow_duplicate=True),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("upload-estructura", "contents"),
    State("upload-estructura", "filename"),
    prevent_initial_call=True
)
def cargar_estructura_desde_upload(contents, filename):
    if contents is None:
        raise dash.exceptions.PreventUpdate
    
    try:
        import base64
        import io
        
        # Decodificar el contenido del archivo
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Cargar JSON
        estructura = json.loads(decoded.decode('utf-8'))
        
        # Validar estructura
        if not validar_estructura_json(estructura):
            return (
                dash.no_update,
                {'display': 'none'},
                True, "Error", 
                "El archivo no tiene una estructura válida", 
                "danger", "danger"
            )
        
        # Guardar como estructura actual
        estructura_manager.guardar_estructura(estructura, archivo_actual)
        
        # Ocultar el componente de upload
        upload_style = {'display': 'none'}
        
        return estructura, upload_style, True, "Éxito", f"Estructura '{filename}' cargada correctamente", "success", "success"
        
    except Exception as e:
        print(f"Error cargando estructura desde upload: {e}")
        return (
            dash.no_update,
            {'display': 'none'},
            True, "Error", 
            f"Error al cargar el archivo: {str(e)}", 
            "danger", "danger"
        )

# ============================================================================
# CALLBACKS PARA ACTUALIZACIÓN DE BADGE Y ESTRUCTURAS DISPONIBLES
# ============================================================================

@app.callback(
    Output("badge-estructura-actual", "children"),
    Input("estructura-actual", "data")
)
def actualizar_badge_estructura(estructura_actual):
    if estructura_actual:
        titulo = estructura_actual.get("TITULO", "Sin estructura")
        tipo_estructura = estructura_actual.get("TIPO_ESTRUCTURA", "N/A")
        terna = estructura_actual.get("TERNA", "N/A")
        disposicion = estructura_actual.get("DISPOSICION", "N/A")
        tension = estructura_actual.get("TENSION", "N/A")
        return f"{titulo} | {tipo_estructura} | {terna} | {disposicion} | {tension}kV"
    return "Sin estructura"


@app.callback(
    Output("estructuras-disponibles", "data"),
    Input("estructura-actual", "data"),
    prevent_initial_call=True
)
def actualizar_estructuras_disponibles(estructura_actual):
    return estructura_manager.listar_estructuras()

# Callback para actualizar lista de estructuras en vista eliminar
@app.callback(
    Output("select-estructura-eliminar", "options"),
    Input("contenido-principal", "children"),
    prevent_initial_call=True
)
def actualizar_lista_eliminar(contenido):
    estructuras = estructura_manager.listar_estructuras()
    # Filtrar actual.estructura.json y plantilla.estructura.json
    estructuras_filtradas = [e for e in estructuras if e not in ["actual.estructura.json", "plantilla.estructura.json"]]
    return [{"label": e, "value": e} for e in estructuras_filtradas]

# ============================================================================
# CALLBACK PARA ELIMINAR ESTRUCTURAS
# ============================================================================

@app.callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Output("contenido-principal", "children", allow_duplicate=True),
    Input("btn-eliminar-estructura", "n_clicks"),
    State("select-estructura-eliminar", "value"),
    prevent_initial_call=True
)
def eliminar_estructura_callback(n_clicks, nombre_estructura):
    if n_clicks is None or not nombre_estructura:
        raise dash.exceptions.PreventUpdate
    
    try:
        # Eliminar la estructura
        exito = estructura_manager.eliminar_estructura(nombre_estructura)
        
        if exito:
            return True, "Éxito", f"Estructura '{nombre_estructura}' eliminada correctamente", "success", "success", crear_vista_home()
        else:
            return True, "Error", f"No se pudo eliminar la estructura '{nombre_estructura}'", "danger", "danger", dash.no_update
    except Exception as e:
        print(f"Error eliminando estructura: {e}")
        return True, "Error", f"Error al eliminar la estructura: {str(e)}", "danger", "danger", dash.no_update

# ============================================================================
# CALLBACKS PARA CÁLCULOS AEA-95301
# ============================================================================

@app.callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("menu-crear-cables", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def crear_cables_callback(n_clicks, estructura_actual):
    if not estructura_actual:
        return True, "Error", "No hay estructura cargada", "danger", "danger"
    
    resultado = calculo_objetos.crear_objetos_cable(estructura_actual)
    
    if resultado["exito"]:
        mensaje = f"{resultado['mensaje']}\n✓ Conductor: {resultado['conductor']}\n✓ Guardia: {resultado['guardia']}"
        return True, "Éxito", mensaje, "success", "success"
    else:
        return True, "Error", resultado["mensaje"], "danger", "danger"

@app.callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("menu-crear-cadena", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def crear_cadena_callback(n_clicks, estructura_actual):
    if not estructura_actual:
        return True, "Error", "No hay estructura cargada", "danger", "danger"
    
    resultado = calculo_objetos.crear_objetos_cadena(estructura_actual)
    
    if resultado["exito"]:
        return True, "Éxito", resultado["mensaje"], "success", "success"
    else:
        return True, "Error", resultado["mensaje"], "danger", "danger"

@app.callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("menu-crear-estructura-obj", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def crear_estructura_obj_callback(n_clicks, estructura_actual):
    if not estructura_actual:
        return True, "Error", "No hay estructura cargada", "danger", "danger"
    
    resultado = calculo_objetos.crear_objetos_estructura(estructura_actual)
    
    if resultado["exito"]:
        return True, "Éxito", resultado["mensaje"], "success", "success"
    else:
        return True, "Error", resultado["mensaje"], "danger", "danger"

@app.callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("menu-crear-todos-objetos", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def crear_todos_objetos_callback(n_clicks, estructura_actual):
    if not estructura_actual:
        return True, "Error", "No hay estructura cargada", "danger", "danger"
    
    resultado = calculo_objetos.crear_todos_objetos(estructura_actual)
    
    if resultado["exito"]:
        return True, "Éxito", resultado["mensaje"], "success", "success"
    else:
        return True, "Error", resultado["mensaje"], "danger", "danger"

# ============================================================================
# CALLBACKS PARA CÁLCULO MECÁNICO DE CONDUCTORES
# ============================================================================

@app.callback(
    Output("tabla-estados-climaticos", "children"),
    Input("contenido-principal", "children"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def actualizar_tabla_estados(contenido, estructura_actual):
    return crear_tabla_estados_climaticos(estructura_actual)

@app.callback(
    Output("estructura-actual", "data", allow_duplicate=True),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("btn-guardar-params-cmc", "n_clicks"),
    State("param-L_vano", "value"),
    State("param-alpha", "value"),
    State("param-theta", "value"),
    State("param-Vmax", "value"),
    State("param-Vmed", "value"),
    State("param-t_hielo", "value"),
    State("param-SALTO_PORCENTUAL", "value"),
    State("param-PASO_AFINADO", "value"),
    State("param-OBJ_CONDUCTOR", "value"),
    State("param-OBJ_GUARDIA", "value"),
    State("param-RELFLECHA_MAX_GUARDIA", "value"),
    State("param-RELFLECHA_SIN_VIENTO", "value"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def guardar_params_cmc(n_clicks, L_vano, alpha, theta, Vmax, Vmed, t_hielo,
                       SALTO_PORCENTUAL, PASO_AFINADO, OBJ_CONDUCTOR, OBJ_GUARDIA,
                       RELFLECHA_MAX_GUARDIA, RELFLECHA_SIN_VIENTO, estructura_actual):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        estructura_actualizada = estructura_actual.copy()
        estructura_actualizada.update({
            "L_vano": float(L_vano),
            "alpha": float(alpha),
            "theta": float(theta),
            "Vmax": float(Vmax),
            "Vmed": float(Vmed),
            "t_hielo": float(t_hielo),
            "SALTO_PORCENTUAL": float(SALTO_PORCENTUAL),
            "PASO_AFINADO": float(PASO_AFINADO),
            "OBJ_CONDUCTOR": OBJ_CONDUCTOR,
            "OBJ_GUARDIA": OBJ_GUARDIA,
            "RELFLECHA_MAX_GUARDIA": float(RELFLECHA_MAX_GUARDIA),
            "RELFLECHA_SIN_VIENTO": bool(RELFLECHA_SIN_VIENTO)
        })
        
        estructura_manager.guardar_estructura(estructura_actualizada, archivo_actual)
        
        return estructura_actualizada, True, "Éxito", "Parámetros guardados", "success", "success"
    except Exception as e:
        return dash.no_update, True, "Error", f"Error: {str(e)}", "danger", "danger"

@app.callback(
    Output("resultados-cmc", "children"),
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "icon", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Input("btn-calcular-cmc", "n_clicks"),
    State("param-L_vano", "value"),
    State("param-alpha", "value"),
    State("param-theta", "value"),
    State("param-Vmax", "value"),
    State("param-Vmed", "value"),
    State("param-t_hielo", "value"),
    State("param-SALTO_PORCENTUAL", "value"),
    State("param-PASO_AFINADO", "value"),
    State("param-OBJ_CONDUCTOR", "value"),
    State("param-OBJ_GUARDIA", "value"),
    State("param-RELFLECHA_MAX_GUARDIA", "value"),
    State("param-RELFLECHA_SIN_VIENTO", "value"),
    State({"type": "estado-temp", "index": ALL}, "value"),
    State({"type": "estado-viento", "index": ALL}, "value"),
    State({"type": "estado-hielo", "index": ALL}, "value"),
    State({"type": "restriccion-conductor", "index": ALL}, "value"),
    State({"type": "restriccion-guardia", "index": ALL}, "value"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def calcular_cmc(n_clicks, L_vano, alpha, theta, Vmax, Vmed, t_hielo,
                SALTO_PORCENTUAL, PASO_AFINADO, OBJ_CONDUCTOR, OBJ_GUARDIA,
                RELFLECHA_MAX_GUARDIA, RELFLECHA_SIN_VIENTO,
                temps, vientos, hielos, restricciones_cond, restricciones_guard, estructura_actual):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    try:
        # Primero crear todos los objetos
        resultado_objetos = calculo_objetos.crear_todos_objetos(estructura_actual)
        if not resultado_objetos["exito"]:
            return html.Div(), True, "Error", resultado_objetos["mensaje"], "danger", "danger"
        
        # Construir estados climáticos
        estados_ids = ["I", "II", "III", "IV", "V"]
        descripciones = ["Tmáx", "Tmín", "Vmáx", "Vmed", "TMA"]
        estados_climaticos = {}
        for i, estado_id in enumerate(estados_ids):
            estados_climaticos[estado_id] = {
                "temperatura": float(temps[i]),
                "descripcion": descripciones[i],
                "viento_velocidad": float(vientos[i]),
                "espesor_hielo": float(hielos[i])
            }
        
        # Construir restricciones
        restricciones_dict = {
            "conductor": {"tension_max_porcentaje": {}},
            "guardia": {"tension_max_porcentaje": {}, "relflecha_max": float(RELFLECHA_MAX_GUARDIA)}
        }
        for i, estado_id in enumerate(estados_ids):
            restricciones_dict["conductor"]["tension_max_porcentaje"][estado_id] = float(restricciones_cond[i])
            restricciones_dict["guardia"]["tension_max_porcentaje"][estado_id] = float(restricciones_guard[i])
        
        # Parámetros para cálculo
        params = {
            "L_vano": float(L_vano),
            "alpha": float(alpha),
            "theta": float(theta),
            "Vmax": float(Vmax),
            "Vmed": float(Vmed),
            "t_hielo": float(t_hielo),
            "exposicion": estructura_actual.get("exposicion", "C"),
            "clase": estructura_actual.get("clase", "C"),
            "Zco": estructura_actual.get("Zco", 13.0),
            "Zcg": estructura_actual.get("Zcg", 13.0),
            "Zca": estructura_actual.get("Zca", 13.0),
            "Zes": estructura_actual.get("Zes", 10.0),
            "Cf_cable": estructura_actual.get("Cf_cable", 1.0),
            "Cf_guardia": estructura_actual.get("Cf_guardia", 1.0),
            "Cf_cadena": estructura_actual.get("Cf_cadena", 0.9),
            "Cf_estructura": estructura_actual.get("Cf_estructura", 0.9),
            "PCADENA": estructura_actual.get("PCADENA", 10.5),
            "SALTO_PORCENTUAL": float(SALTO_PORCENTUAL),
            "PASO_AFINADO": float(PASO_AFINADO),
            "OBJ_CONDUCTOR": OBJ_CONDUCTOR,
            "OBJ_GUARDIA": OBJ_GUARDIA,
            "RELFLECHA_MAX_GUARDIA": float(RELFLECHA_MAX_GUARDIA),
            "RELFLECHA_SIN_VIENTO": bool(RELFLECHA_SIN_VIENTO)
        }
        
        resultado = calculo_mecanico.calcular(params, estados_climaticos, restricciones_dict)
        
        if resultado["exito"]:
            # Crear componentes de resultados
            resultados_html = [
                html.H4("Resultados del Cálculo Mecánico", className="mt-4 mb-3"),
                
                html.H5("Conductor"),
                dbc.Table.from_dataframe(resultado["df_conductor"], striped=True, bordered=True, hover=True, size="sm"),
                
                html.H5("Cable de Guardia", className="mt-4"),
                dbc.Table.from_dataframe(resultado["df_guardia"], striped=True, bordered=True, hover=True, size="sm"),
            ]
            
            if resultado["df_cargas_totales"] is not None:
                resultados_html.extend([
                    html.H5("Lista Total de Cargas", className="mt-4"),
                    dbc.Table.from_dataframe(resultado["df_cargas_totales"], striped=True, bordered=True, hover=True, size="sm"),
                    dbc.Button("Descargar CSV", id="btn-descargar-cargas-csv", color="primary", className="mt-2")
                ])
            
            # Agregar gráficos de flechas
            if calculo_mecanico.resultados_conductor and calculo_mecanico.resultados_guardia:
                try:
                    fig_combinado, fig_conductor, fig_guardia = crear_grafico_flechas(
                        calculo_mecanico.resultados_conductor,
                        calculo_mecanico.resultados_guardia,
                        float(L_vano)
                    )
                    resultados_html.extend([
                        html.H5("Gráficos de Flechas", className="mt-4"),
                        html.H6("Conductor y Guardia", className="mt-3"),
                        dcc.Graph(figure=fig_combinado, config={'displayModeBar': True}),
                        html.H6("Solo Conductor", className="mt-3"),
                        dcc.Graph(figure=fig_conductor, config={'displayModeBar': True}),
                        html.H6("Solo Cable de Guardia", className="mt-3"),
                        dcc.Graph(figure=fig_guardia, config={'displayModeBar': True})
                    ])
                except Exception as e:
                    print(f"Error generando gráficos de flechas: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("No hay resultados de conductor o guardia para graficar")
            
            return resultados_html, True, "Éxito", "Cálculo completado", "success", "success"
        else:
            return html.Div(), True, "Error", resultado["mensaje"], "danger", "danger"
            
    except Exception as e:
        return html.Div(), True, "Error", f"Error en cálculo: {str(e)}", "danger", "danger"

# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    # Crear directorio data si no existe
    data_dir.mkdir(exist_ok=True)
    
    # Asegurar que exista el archivo de cables
    if not cables_path.exists():
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
        cables_path.write_text(json.dumps(cables_base, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Asegurar que exista el archivo de plantilla
    if not estructura_manager.plantilla_path.exists():
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
        estructura_manager.guardar_estructura(estructura_base, estructura_manager.plantilla_path)
    
    # Ejecutar aplicación
    app.run(debug=True, port=8050)