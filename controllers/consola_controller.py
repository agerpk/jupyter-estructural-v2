"""Controlador para vista de consola"""
import dash
from dash import Input, Output
from utils.console_capture import get_console_capture

def register_callbacks(app):
    """Registrar callbacks de consola"""
    
    @app.callback(
        Output("consola-output", "children"),
        Input("btn-actualizar-consola", "n_clicks"),
        prevent_initial_call=False
    )
    def actualizar_consola(n_clicks):
        """Actualizar contenido de consola"""
        try:
            capture = get_console_capture()
            return capture.get_text()
        except:
            return dash.no_update
