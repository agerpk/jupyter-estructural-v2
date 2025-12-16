"""Controlador para Calcular Todo - Orquestador modular"""

import dash
from dash import Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de calcular todo"""
    
    from dash import dcc
    import base64
    from datetime import datetime
    
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
    
    @app.callback(
        Output("download-html-todo", "data"),
        Input("btn-descargar-html-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def descargar_html(n_clicks, estructura_actual):
        """Descarga el contenido actual como HTML"""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            from utils.descargar_html import generar_html_completo
            
            html_completo = generar_html_completo(estructura_actual)
            
            nombre_estructura = estructura_actual.get('TITULO', 'estructura') if estructura_actual else 'estructura'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            return dcc.send_string(html_completo, f"{nombre_estructura}_calculo_completo_{timestamp}.html")
            
        except Exception as e:
            import traceback
            print(f"Error generando HTML: {traceback.format_exc()}")
            raise dash.exceptions.PreventUpdate
