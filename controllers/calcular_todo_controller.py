"""Controlador para Calcular Todo - Orquestador modular"""

import dash
from dash import Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de calcular todo"""
    
    state = AppState()
    
    @app.callback(
        Output("output-calcular-todo", "children", allow_duplicate=True),
        Input("btn-cargar-cache-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_desde_cache(n_clicks, estructura_actual):
        """Carga modular desde cachés individuales"""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        from components.vista_calcular_todo import cargar_resultados_modulares
        return cargar_resultados_modulares(estructura_actual)
    
    @app.callback(
        Output("output-calcular-todo", "children"),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-calcular-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def ejecutar_calculo_completo(n_clicks, estructura_actual):
        """Ejecuta todos los cálculos en secuencia"""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            from components.vista_calcular_todo import cargar_resultados_modulares
            
            # Por ahora, solo cargar desde caché
            # TODO: Implementar ejecución secuencial de cálculos
            return (
                [dbc.Alert("Función en desarrollo. Use 'Cargar desde Cache' para ver resultados.", color="info")],
                True, "Info", "Función en desarrollo", "info", "info"
            )
            
        except Exception as e:
            import traceback
            error_msg = f"Error en cálculo completo: {str(e)}"
            print(traceback.format_exc())
            return (
                [dbc.Alert(error_msg, color="danger")],
                True, "Error", error_msg, "danger", "danger"
            )
