"""Controlador para acciones de la vista home"""

import dash
from dash import Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
from models.app_state import AppState
from config.app_config import DATA_DIR
import json


def register_callbacks(app):
    """Registrar callbacks de home"""
    
    state = AppState()
    
    # Cargar estructura
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input({"type": "btn-cargar-estructura", "index": ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def cargar_estructura_home(n_clicks):
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks):
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered_id
        estructura_nombre = trigger_id["index"]
        
        try:
            ruta = DATA_DIR / estructura_nombre
            estructura = state.estructura_manager.cargar_estructura(ruta)
            state.estructura_manager.guardar_estructura(estructura, state.archivo_actual)
            return estructura, True, "Éxito", f"Estructura '{estructura_nombre}' cargada", "success"
        except Exception as e:
            return dash.no_update, True, "Error", f"Error: {str(e)}", "danger"
    
    # Descargar estructura
    @app.callback(
        Output("download-estructura", "data", allow_duplicate=True),
        Input({"type": "btn-descargar-estructura", "index": ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def descargar_estructura_home(n_clicks):
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks):
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered_id
        estructura_nombre = trigger_id["index"]
        
        try:
            ruta = DATA_DIR / estructura_nombre
            estructura = state.estructura_manager.cargar_estructura(ruta)
            contenido = json.dumps(estructura, indent=2, ensure_ascii=False)
            return dict(content=contenido, filename=estructura_nombre)
        except:
            raise dash.exceptions.PreventUpdate
    
    # Abrir modal eliminar
    @app.callback(
        Output("modal-confirmar-eliminar-home", "is_open", allow_duplicate=True),
        Output("texto-confirmar-eliminar", "children"),
        Output("estructura-a-eliminar", "data"),
        Input({"type": "btn-eliminar-estructura-home", "index": ALL}, "n_clicks"),
        Input("btn-cancelar-eliminar-home", "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_modal_eliminar(n_clicks_eliminar, n_clicks_cancelar):
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered_id
        
        if trigger_id and isinstance(trigger_id, dict) and trigger_id.get("type") == "btn-eliminar-estructura-home":
            estructura_nombre = trigger_id["index"]
            nombre_mostrar = estructura_nombre.replace(".estructura.json", "")
            return True, f"¿Está seguro que desea eliminar '{nombre_mostrar}'?", estructura_nombre
        
        return False, "", None
    
    # Confirmar eliminar
    @app.callback(
        Output("modal-confirmar-eliminar-home", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Output("contenido-principal", "children", allow_duplicate=True),
        Input("btn-confirmar-eliminar-home", "n_clicks"),
        State("estructura-a-eliminar", "data"),
        prevent_initial_call=True
    )
    def confirmar_eliminar(n_clicks, estructura_nombre):
        if not n_clicks or not estructura_nombre:
            raise dash.exceptions.PreventUpdate
        
        try:
            exito = state.estructura_manager.eliminar_estructura(estructura_nombre)
            if exito:
                from components.vista_home import crear_vista_home
                return False, True, "Éxito", f"Estructura '{estructura_nombre}' eliminada", "success", crear_vista_home()
            else:
                return False, True, "Error", "No se pudo eliminar", "danger", dash.no_update
        except Exception as e:
            return False, True, "Error", f"Error: {str(e)}", "danger", dash.no_update
    
    # Abrir modal duplicar
    @app.callback(
        Output("modal-duplicar-estructura", "is_open", allow_duplicate=True),
        Output("input-nombre-duplicado", "value"),
        Output("estructura-a-duplicar", "data"),
        Input({"type": "btn-duplicar-estructura", "index": ALL}, "n_clicks"),
        Input("btn-cancelar-duplicar", "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_modal_duplicar(n_clicks_duplicar, n_clicks_cancelar):
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered_id
        
        if trigger_id and isinstance(trigger_id, dict) and trigger_id.get("type") == "btn-duplicar-estructura":
            estructura_nombre = trigger_id["index"]
            nombre_base = estructura_nombre.replace(".estructura.json", "")
            nombre_copia = f"{nombre_base}_copia"
            return True, nombre_copia, estructura_nombre
        
        return False, "", None
    
    # Confirmar duplicar
    @app.callback(
        Output("modal-duplicar-estructura", "is_open", allow_duplicate=True),
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-confirmar-duplicar", "n_clicks"),
        State("estructura-a-duplicar", "data"),
        State("input-nombre-duplicado", "value"),
        prevent_initial_call=True
    )
    def confirmar_duplicar(n_clicks, estructura_origen, nuevo_nombre):
        if not n_clicks or not estructura_origen or not nuevo_nombre:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Cargar estructura original
            ruta_origen = DATA_DIR / estructura_origen
            estructura = state.estructura_manager.cargar_estructura(ruta_origen)
            
            # Modificar título
            estructura["TITULO"] = nuevo_nombre
            
            # Guardar copia
            nombre_archivo = f"{nuevo_nombre}.estructura.json"
            ruta_destino = DATA_DIR / nombre_archivo
            state.estructura_manager.guardar_estructura(estructura, ruta_destino)
            
            # Guardar como actual
            state.estructura_manager.guardar_estructura(estructura, state.archivo_actual)
            
            return False, estructura, True, "Éxito", f"Estructura duplicada como '{nuevo_nombre}'", "success"
        except Exception as e:
            return False, dash.no_update, True, "Error", f"Error: {str(e)}", "danger"
