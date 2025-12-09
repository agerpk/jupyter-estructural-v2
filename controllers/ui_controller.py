"""Controlador de interfaz de usuario"""

import dash
from dash import Input, Output
from models.app_state import AppState
from config.app_config import ARCHIVOS_PROTEGIDOS


def register_callbacks(app):
    """Registrar callbacks de UI"""
    
    state = AppState()
    
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
        return state.estructura_manager.listar_estructuras()
    
    @app.callback(
        Output("select-estructura-eliminar", "options"),
        Input("contenido-principal", "children"),
        prevent_initial_call=True
    )
    def actualizar_lista_eliminar(contenido):
        estructuras = state.estructura_manager.listar_estructuras()
        estructuras_filtradas = [e for e in estructuras if e not in ARCHIVOS_PROTEGIDOS]
        return [{"label": e, "value": e} for e in estructuras_filtradas]
