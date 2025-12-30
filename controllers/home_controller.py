"""Controlador para acciones de la vista home"""

import dash
from dash import html, Input, Output, State, ALL, callback_context
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
            # Actualizar estado y guardar en archivo unificado
            state.set_estructura_actual(estructura)
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
            
            # Guardar como actual usando sistema unificado
            state.set_estructura_actual(estructura)
            
            return False, estructura, True, "Éxito", f"Estructura duplicada como '{nuevo_nombre}'", "success"
        except Exception as e:
            return False, dash.no_update, True, "Error", f"Error: {str(e)}", "danger"
    
    # Ver datos del cable
    @app.callback(
        Output("modal-ver-cable", "is_open"),
        Output("modal-ver-cable-titulo", "children"),
        Output("modal-ver-cable-contenido", "children"),
        Input({"type": "btn-ver-cable", "index": ALL}, "n_clicks"),
        Input("btn-cerrar-ver-cable", "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_modal_ver_cable(n_clicks_ver, n_clicks_cerrar):
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered_id
        
        if trigger_id and isinstance(trigger_id, dict) and trigger_id.get("type") == "btn-ver-cable":
            cable_id = trigger_id["index"]
            cable = state.cable_manager.obtener_cable(cable_id)
            
            if not cable:
                return True, "Error", dbc.Alert("Cable no encontrado", color="danger")
            
            contenido = dbc.Container([
                dbc.Row([
                    dbc.Col([dbc.Label("Tipo:", className="fw-bold")], width=4),
                    dbc.Col([html.Span(cable.get("tipo", "N/A"))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Material:", className="fw-bold")], width=4),
                    dbc.Col([html.Span(cable.get("material", "N/A"))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Sección Nominal:", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("seccion_nominal", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Sección Total (mm²):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("seccion_total_mm2", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Diámetro Total (mm):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("diametro_total_mm", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Peso Unitario (daN/m):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("peso_unitario_dan_m", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Coef. Dilatación (1/°C):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("coeficiente_dilatacion_1_c", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Módulo Elasticidad (daN/mm²):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("modulo_elasticidad_dan_mm2", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Carga Rotura Mínima (daN):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("carga_rotura_minima_dan", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Tensión Rotura Mínima (MPa):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("tension_rotura_minima", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Carga Máx. Trabajo (daN):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("carga_max_trabajo", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Tensión Máx. Trabajo (MPa):", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("tension_max_trabajo", "N/A")))], width=8)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([dbc.Label("Norma Fabricación:", className="fw-bold")], width=4),
                    dbc.Col([html.Span(str(cable.get("norma_fabricacion", "N/A")))], width=8)
                ], className="mb-2")
            ], fluid=True)
            
            return True, f"Cable: {cable_id}", contenido
        
        return False, "", ""
    
    # Modificar cable desde home
    @app.callback(
        Output("contenido-principal", "children", allow_duplicate=True),
        Input({"type": "btn-modificar-cable-home", "index": ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def modificar_cable_home(n_clicks):
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks):
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered_id
        cable_id = trigger_id["index"]
        
        # Navegar a vista de modificar cable
        from components.vista_gestion_cables import crear_vista_modificar_cable
        cables_disponibles = state.cable_manager.obtener_cables()
        return crear_vista_modificar_cable(cables_disponibles)
