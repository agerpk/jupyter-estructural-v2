"""Controlador para botones de estructura en Home"""

import dash
from dash import Input, Output, State, dcc


def register_callbacks(app):
    """Registrar callbacks de botones estructura en Home"""
    
    @app.callback(
        Output("modal-nueva-estructura", "is_open", allow_duplicate=True),
        Input("btn-nueva-estructura-home", "n_clicks"),
        prevent_initial_call=True
    )
    def abrir_modal_nueva_estructura(n_clicks):
        if n_clicks:
            return True
        return dash.no_update
    
    @app.callback(
        Output("modal-cargar-db", "is_open", allow_duplicate=True),
        Input("btn-cargar-db-home", "n_clicks"),
        prevent_initial_call=True
    )
    def abrir_modal_cargar_db(n_clicks):
        if n_clicks:
            return True
        return dash.no_update
    
    @app.callback(
        Output("upload-estructura-home", "style"),
        Input("btn-cargar-pc-home", "n_clicks"),
        prevent_initial_call=True
    )
    def mostrar_upload_home(n_clicks):
        if n_clicks:
            return {
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'display': 'block'
            }
        return dash.no_update
    
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("upload-estructura-home", "style", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("upload-estructura-home", "contents"),
        State("upload-estructura-home", "filename"),
        prevent_initial_call=True
    )
    def cargar_estructura_desde_upload_home(contents, filename):
        if contents is None:
            raise dash.exceptions.PreventUpdate
        
        from models.app_state import AppState
        from utils.validaciones import validar_estructura_json
        import json, base64
        
        state = AppState()
        
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            estructura = json.loads(decoded.decode('utf-8'))
            
            if not validar_estructura_json(estructura):
                return dash.no_update, {'display': 'none'}, True, "Error", "El archivo no tiene una estructura válida", "danger", "danger"
            
            state.estructura_manager.guardar_estructura(estructura, state.archivo_actual)
            return estructura, {'display': 'none'}, True, "Éxito", f"Estructura '{filename}' cargada correctamente", "success", "success"
            
        except Exception as e:
            return dash.no_update, {'display': 'none'}, True, "Error", f"Error al cargar el archivo: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("store-catenaria-actual", "data"),
        Input("btn-calcular-catenaria", "n_clicks"),
        State("select-cable-catenaria", "value"),
        State("input-vano-catenaria", "value"),
        prevent_initial_call=True
    )
    def calcular_catenaria(n_clicks, cable_id, vano):
        if not n_clicks or not cable_id:
            return dash.no_update
        
        from models.app_state import AppState
        from datetime import datetime
        from config.app_config import DATA_DIR
        import re, json
        
        state = AppState()
        plantilla = state.estructura_manager.cargar_estructura(state.estructura_manager.plantilla_path)
        
        cable_clean = re.sub(r'[^a-z0-9]', '', cable_id.lower())
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        titulo = f"{cable_clean}_{timestamp}"
        
        datos_catenaria = {
            "TITULO": titulo,
            "cable_conductor_id": cable_id,
            "L_vano": vano,
            "exposicion": plantilla.get("exposicion"),
            "Zona_climatica": plantilla.get("Zona_climatica"),
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
            "version": plantilla.get("version"),
            "Q": plantilla.get("Q"),
            "Zco": plantilla.get("Zco"),
            "Cf_cable": plantilla.get("Cf_cable"),
            "Vmax": plantilla.get("Vmax"),
            "Vmed": plantilla.get("Vmed"),
            "SALTO_PORCENTUAL": plantilla.get("SALTO_PORCENTUAL"),
            "PASO_AFINADO": plantilla.get("PASO_AFINADO"),
            "OBJ_CONDUCTOR": plantilla.get("OBJ_CONDUCTOR"),
            "OBJ_GUARDIA": plantilla.get("OBJ_GUARDIA")
        }
        
        archivo_path = DATA_DIR / f"{titulo}.CMC.json"
        archivo_path.write_text(json.dumps(datos_catenaria, indent=2, ensure_ascii=False), encoding="utf-8")
        
        return datos_catenaria
