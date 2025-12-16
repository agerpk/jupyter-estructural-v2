"""Controlador de interfaz de usuario"""

import dash
from dash import Input, Output
from models.app_state import AppState
from config.app_config import ARCHIVOS_PROTEGIDOS
import dash


def register_callbacks(app):
    """Registrar callbacks de UI"""
    
    state = AppState()
    
    @app.callback(
        Output("badge-estructura-actual", "children"),
        Input("estructura-actual", "data"),
        prevent_initial_call=True
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
        Output("modal-acerca-de", "is_open"),
        Input("menu-acerca-de", "n_clicks"),
        Input("btn-cerrar-acerca-de", "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_modal_acerca_de(abrir, cerrar):
        ctx = dash.callback_context
        if not ctx.triggered:
            return False
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "menu-acerca-de":
            return True
        elif trigger_id == "btn-cerrar-acerca-de":
            return False
        
        return False
    
    @app.callback(
        Output("badge-vista-actual", "children"),
        Input("btn-inicio", "n_clicks"),
        Input("menu-ajustar-parametros", "n_clicks"),
        Input("menu-calculo-mecanico", "n_clicks"),
        Input("menu-diseno-geometrico", "n_clicks"),
        Input("menu-diseno-mecanico", "n_clicks"),
        Input("menu-arboles-carga", "n_clicks"),
        Input("menu-seleccion-poste", "n_clicks"),
        Input("menu-calcular-todo", "n_clicks"),
        prevent_initial_call=True
    )
    def actualizar_badge_vista(*args):
        ctx = dash.callback_context
        if not ctx.triggered:
            return "Inicio"
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        nombres_vistas = {
            "btn-inicio": "Inicio",
            "menu-ajustar-parametros": "Ajustar Parámetros",
            "menu-calculo-mecanico": "CMC",
            "menu-diseno-geometrico": "DGE",
            "menu-diseno-mecanico": "DME",
            "menu-arboles-carga": "Árboles de Carga",
            "menu-seleccion-poste": "SPH",
            "menu-calcular-todo": "Calcular Todo"
        }
        return nombres_vistas.get(trigger_id, "Vista")
    

