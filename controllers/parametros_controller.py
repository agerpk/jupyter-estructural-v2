"""Controlador de ajuste de parámetros"""

import dash
from dash import Input, Output, State, ALL
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de ajuste de parámetros"""
    
    state = AppState()
    
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
            estructura_actualizada = estructura_actual.copy()
            
            for param_id, param_value in zip(param_ids, param_values):
                if param_id and "index" in param_id:
                    param_key = param_id["index"]
                    
                    if param_key in estructura_actual:
                        original_value = estructura_actual[param_key]
                        
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
            
            state.estructura_manager.guardar_estructura(estructura_actualizada, state.archivo_actual)
            
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
