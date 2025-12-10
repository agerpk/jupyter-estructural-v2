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
        Output("contenido-principal", "children", allow_duplicate=True),
        Input("estructuras-disponibles", "data"),
        Input("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def actualizar_vista_home_estructuras(estructuras_data, estructura_actual):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        # Solo actualizar si estamos en home
        from config.app_config import NAVEGACION_STATE_FILE
        try:
            if NAVEGACION_STATE_FILE.exists():
                import json
                with open(NAVEGACION_STATE_FILE, 'r') as f:
                    vista = json.load(f).get("ultima_vista", "home")
                    if vista == "home":
                        from components.vista_home import crear_vista_home
                        return crear_vista_home()
        except:
            pass
        
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        Output("badge-vista-actual", "children"),
        Input("contenido-principal", "children")
    )
    def actualizar_badge_vista(contenido):
        from config.app_config import NAVEGACION_STATE_FILE
        try:
            if NAVEGACION_STATE_FILE.exists():
                import json
                with open(NAVEGACION_STATE_FILE, 'r') as f:
                    data = json.load(f)
                    vista = data.get("ultima_vista", "home")
                    
                    nombres_vistas = {
                        "home": "Inicio",
                        "ajustar-parametros": "Ajustar Parámetros",
                        "calculo-mecanico": "CMC",
                        "diseno-geometrico": "DGE",
                        "diseno-mecanico": "DME",
                        "arboles-carga": "Árboles de Carga",
                        "seleccion-poste": "SPH",
                        "calcular-todo": "Calcular Todo"
                    }
                    return nombres_vistas.get(vista, "Vista")
        except:
            pass
        return "Inicio"
