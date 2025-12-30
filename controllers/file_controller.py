"""Controlador de operaciones de archivo"""

import dash
from dash import Input, Output, State
import json
import base64
from models.app_state import AppState
from utils.validaciones import validar_estructura_json
from config.app_config import DATA_DIR


def register_callbacks(app):
    """Registrar callbacks de operaciones de archivo"""
    
    state = AppState()
    
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
    
    @app.callback(
        Output("select-estructura-db", "options"),
        Input("modal-cargar-db", "is_open"),
        prevent_initial_call=True
    )
    def actualizar_lista_estructuras_modal(is_open):
        if is_open:
            estructuras = state.estructura_manager.listar_estructuras()
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
    
    @app.callback(
        Output("upload-estructura", "style", allow_duplicate=True),
        Input("menu-cargar-desde-pc", "n_clicks"),
        prevent_initial_call=True
    )
    def mostrar_upload_component(n_clicks):
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
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            estructura = json.loads(decoded.decode('utf-8'))
            
            if not validar_estructura_json(estructura):
                return (
                    dash.no_update,
                    {'display': 'none'},
                    True, "Error", 
                    "El archivo no tiene una estructura válida", 
                    "danger", "danger"
                )
            
            # Guardar usando el sistema unificado
            state.set_estructura_actual(estructura)
            ruta_actual = state.get_estructura_actual_path()
            state.estructura_manager.guardar_estructura(estructura, ruta_actual)
            
            upload_style = {'display': 'none'}
            
            return estructura, upload_style, True, "Éxito", f"Estructura '{filename}' cargada correctamente", "success", "success"
            
        except Exception as e:
            return (
                dash.no_update,
                {'display': 'none'},
                True, "Error", 
                f"Error al cargar el archivo: {str(e)}", 
                "danger", "danger"
            )
    
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
