"""Controlador de navegación"""

import dash
from dash import Input, Output, State, ALL, callback_context
import json
from components.vista_home import crear_vista_home
from components.vista_ajuste_parametros import crear_vista_ajuste_parametros
from components.vista_eliminar_estructura import crear_vista_eliminar_estructura
from components.vista_calculo_mecanico import crear_vista_calculo_mecanico
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de navegación"""
    
    state = AppState()
    
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
        ctx = callback_context
        
        if not ctx.triggered:
            return crear_vista_home()
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-inicio":
            return crear_vista_home()
        
        elif trigger_id == "menu-ajustar-parametros":
            cables_disponibles = state.cable_manager.obtener_cables()
            return crear_vista_ajuste_parametros(estructura_actual, cables_disponibles)
        
        elif trigger_id == "menu-eliminar-estructura":
            return crear_vista_eliminar_estructura()
        
        elif trigger_id == "menu-calculo-mecanico":
            return crear_vista_calculo_mecanico(estructura_actual)
        
        elif "btn-volver" in trigger_id:
            try:
                trigger_json = json.loads(trigger_id.replace("'", '"'))
                if trigger_json.get("type") == "btn-volver":
                    return crear_vista_home()
            except:
                pass
        
        elif trigger_id in ["menu-nueva-estructura", "menu-guardar-estructura"]:
            return dash.no_update
    
        return crear_vista_home()
