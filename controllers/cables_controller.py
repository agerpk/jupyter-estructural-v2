"""Controlador de gestión de cables"""

import dash
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState
from components.vista_gestion_cables import crear_vista_agregar_cable, crear_vista_modificar_cable, crear_vista_eliminar_cable


def register_callbacks(app):
    """Registrar callbacks de gestión de cables"""
    
    state = AppState()
    
    @app.callback(
        Output("form-modificar-cable", "children"),
        Input("select-cable-modificar", "value"),
        prevent_initial_call=True
    )
    def cargar_datos_cable(cable_id):
        if not cable_id:
            return html.Div()
        
        cable = state.cable_manager.obtener_cable(cable_id)
        if not cable:
            return html.Div("Cable no encontrado", className="text-danger")
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Tipo", style={"fontSize": "1.125rem"}),
                    dbc.RadioItems(
                        id="input-cable-tipo-mod",
                        options=[
                            {"label": "ADSS", "value": "ADSS"},
                            {"label": "OPGW", "value": "OPGW"},
                            {"label": "ACSR", "value": "ACSR"},
                            {"label": "AAAC", "value": "AAAC"},
                            {"label": "ACERO", "value": "ACERO"},
                            {"label": "OTRO", "value": "OTRO"}
                        ],
                        value=cable.get("tipo", "OTRO"),
                        inline=True
                    ),
                ], md=12),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Material", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-material-mod", type="text", value=cable.get("material", "")),
                ], md=6),
                dbc.Col([
                    dbc.Label("Sección Nominal", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-seccion-nominal-mod", type="text", value=cable.get("seccion_nominal", "")),
                ], md=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Sección Total (mm²) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-seccion-total-mod", type="number", step=0.01, value=cable.get("seccion_total_mm2", ""), required=True),
                ], md=6),
                dbc.Col([
                    dbc.Label("Diámetro Total (mm) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-diametro-mod", type="number", step=0.1, value=cable.get("diametro_total_mm", ""), required=True),
                ], md=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Peso Unitario (daN/m) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-peso-mod", type="number", step=0.001, value=cable.get("peso_unitario_dan_m", ""), required=True),
                ], md=6),
                dbc.Col([
                    dbc.Label("Coef. Dilatación (1/°C) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-dilatacion-mod", type="number", step=0.0000001, value=cable.get("coeficiente_dilatacion_1_c", ""), required=True),
                ], md=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Módulo Elasticidad (daN/mm²) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-modulo-mod", type="number", step=1, value=cable.get("modulo_elasticidad_dan_mm2", ""), required=True),
                ], md=6),
                dbc.Col([
                    dbc.Label("Carga Rotura Mínima (daN) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-rotura-mod", type="number", step=0.1, value=cable.get("carga_rotura_minima_dan", ""), required=True),
                ], md=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Tensión Rotura Mínima (MPa) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-tension-rotura-mod", type="number", step=0.01, value=cable.get("tension_rotura_minima", ""), required=True),
                ], md=6),
                dbc.Col([
                    dbc.Label("Carga Máx. Trabajo (daN) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-carga-max-mod", type="number", step=0.1, value=cable.get("carga_max_trabajo", ""), required=True),
                ], md=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Tensión Máx. Trabajo (MPa) *", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-tension-max-mod", type="number", step=0.01, value=cable.get("tension_max_trabajo", ""), required=True),
                ], md=6),
                dbc.Col([
                    dbc.Label("Norma Fabricación", style={"fontSize": "1.125rem"}),
                    dbc.Input(id="input-cable-norma-mod", type="text", value=cable.get("norma_fabricacion", "")),
                ], md=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button("Guardar Cambios", id="btn-guardar-cable-mod", color="primary", size="lg", className="w-100"),
                ], md=12),
            ])
        ])
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-cable", "n_clicks"),
        State("input-cable-id", "value"),
        State("input-cable-tipo", "value"),
        State("input-cable-material", "value"),
        State("input-cable-seccion-nominal", "value"),
        State("input-cable-seccion-total", "value"),
        State("input-cable-diametro", "value"),
        State("input-cable-peso", "value"),
        State("input-cable-dilatacion", "value"),
        State("input-cable-modulo", "value"),
        State("input-cable-rotura", "value"),
        State("input-cable-tension-rotura", "value"),
        State("input-cable-carga-max", "value"),
        State("input-cable-tension-max", "value"),
        State("input-cable-norma", "value"),
        prevent_initial_call=True
    )
    def guardar_nuevo_cable(n_clicks, cable_id, tipo, material, seccion_nominal, seccion_total, 
                           diametro, peso, dilatacion, modulo, rotura, tension_rotura, 
                           carga_max, tension_max, norma):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        if not cable_id or not cable_id.strip():
            return True, "Error", "Ingrese un ID válido para el cable", "danger", "danger"
        
        try:
            nuevo_cable = {
                "tipo": tipo or "OTRO",
                "material": material,
                "seccion_nominal": seccion_nominal,
                "seccion_total_mm2": float(seccion_total) if seccion_total else None,
                "diametro_total_mm": float(diametro) if diametro else None,
                "peso_unitario_dan_m": float(peso) if peso else None,
                "coeficiente_dilatacion_1_c": float(dilatacion) if dilatacion else None,
                "modulo_elasticidad_dan_mm2": float(modulo) if modulo else None,
                "carga_rotura_minima_dan": float(rotura) if rotura else None,
                "tension_rotura_minima": float(tension_rotura) if tension_rotura else None,
                "carga_max_trabajo": float(carga_max) if carga_max else None,
                "tension_max_trabajo": float(tension_max) if tension_max else None,
                "norma_fabricacion": norma
            }
            
            state.cable_manager.agregar_cable(cable_id.strip(), nuevo_cable)
            return True, "Éxito", f"Cable '{cable_id}' agregado correctamente", "success", "success"
        except Exception as e:
            return True, "Error", f"Error al guardar cable: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-cable-mod", "n_clicks"),
        State("select-cable-modificar", "value"),
        State("input-cable-tipo-mod", "value"),
        State("input-cable-material-mod", "value"),
        State("input-cable-seccion-nominal-mod", "value"),
        State("input-cable-seccion-total-mod", "value"),
        State("input-cable-diametro-mod", "value"),
        State("input-cable-peso-mod", "value"),
        State("input-cable-dilatacion-mod", "value"),
        State("input-cable-modulo-mod", "value"),
        State("input-cable-rotura-mod", "value"),
        State("input-cable-tension-rotura-mod", "value"),
        State("input-cable-carga-max-mod", "value"),
        State("input-cable-tension-max-mod", "value"),
        State("input-cable-norma-mod", "value"),
        prevent_initial_call=True
    )
    def modificar_cable(n_clicks, cable_id, tipo, material, seccion_nominal, seccion_total, 
                       diametro, peso, dilatacion, modulo, rotura, tension_rotura, 
                       carga_max, tension_max, norma):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        if not cable_id:
            return True, "Error", "Seleccione un cable", "danger", "danger"
        
        try:
            cable_actualizado = {
                "tipo": tipo or "OTRO",
                "material": material,
                "seccion_nominal": seccion_nominal,
                "seccion_total_mm2": float(seccion_total) if seccion_total else None,
                "diametro_total_mm": float(diametro) if diametro else None,
                "peso_unitario_dan_m": float(peso) if peso else None,
                "coeficiente_dilatacion_1_c": float(dilatacion) if dilatacion else None,
                "modulo_elasticidad_dan_mm2": float(modulo) if modulo else None,
                "carga_rotura_minima_dan": float(rotura) if rotura else None,
                "tension_rotura_minima": float(tension_rotura) if tension_rotura else None,
                "carga_max_trabajo": float(carga_max) if carga_max else None,
                "tension_max_trabajo": float(tension_max) if tension_max else None,
                "norma_fabricacion": norma
            }
            
            state.cable_manager.modificar_cable(cable_id, cable_actualizado)
            return True, "Éxito", f"Cable '{cable_id}' modificado correctamente", "success", "success"
        except Exception as e:
            return True, "Error", f"Error al modificar cable: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("info-cable-eliminar", "children"),
        Input("select-cable-eliminar", "value"),
        prevent_initial_call=True
    )
    def mostrar_info_cable(cable_id):
        if not cable_id:
            return html.Div()
        
        cable = state.cable_manager.obtener_cable(cable_id)
        if not cable:
            return html.Div("Cable no encontrado", className="text-danger")
        return dbc.Alert([
            html.H5(f"Cable: {cable_id}"),
            html.P(f"Tipo: {cable.get('tipo', 'N/A')}"),
            html.P(f"Material: {cable.get('material', 'N/A')}"),
            html.P(f"Diámetro: {cable.get('diametro_total_mm', 'N/A')} mm"),
            html.P("¿Está seguro que desea eliminar este cable?", className="text-danger fw-bold")
        ], color="warning")
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Output("contenido-principal", "children", allow_duplicate=True),
        Input("btn-eliminar-cable", "n_clicks"),
        State("select-cable-eliminar", "value"),
        prevent_initial_call=True
    )
    def eliminar_cable(n_clicks, cable_id):
        if not cable_id:
            return True, "Error", "Seleccione un cable", "danger", "danger", dash.no_update
        
        try:
            from components.vista_home import crear_vista_home
            state.cable_manager.eliminar_cable(cable_id)
            return True, "Éxito", f"Cable '{cable_id}' eliminado correctamente", "success", "success", crear_vista_home()
        except Exception as e:
            return True, "Error", f"Error al eliminar cable: {str(e)}", "danger", "danger", dash.no_update


    
    @app.callback(
        Output("input-cable-tipo", "value", allow_duplicate=True),
        Output("input-cable-material", "value", allow_duplicate=True),
        Output("input-cable-seccion-nominal", "value", allow_duplicate=True),
        Output("input-cable-seccion-total", "value", allow_duplicate=True),
        Output("input-cable-diametro", "value", allow_duplicate=True),
        Output("input-cable-peso", "value", allow_duplicate=True),
        Output("input-cable-dilatacion", "value", allow_duplicate=True),
        Output("input-cable-modulo", "value", allow_duplicate=True),
        Output("input-cable-rotura", "value", allow_duplicate=True),
        Output("input-cable-tension-rotura", "value", allow_duplicate=True),
        Output("input-cable-carga-max", "value", allow_duplicate=True),
        Output("input-cable-tension-max", "value", allow_duplicate=True),
        Output("input-cable-norma", "value", allow_duplicate=True),
        Input("btn-copiar-cable", "n_clicks"),
        State("select-cable-copiar", "value"),
        prevent_initial_call=True
    )
    def copiar_cable_agregar(n_clicks, cable_id):
        if not n_clicks or not cable_id:
            raise dash.exceptions.PreventUpdate
        
        cable = state.cable_manager.obtener_cable(cable_id)
        if not cable:
            raise dash.exceptions.PreventUpdate
        
        return (
            cable.get("tipo", "OTRO"),
            cable.get("material", ""),
            cable.get("seccion_nominal", ""),
            cable.get("seccion_total_mm2", ""),
            cable.get("diametro_total_mm", ""),
            cable.get("peso_unitario_dan_m", ""),
            cable.get("coeficiente_dilatacion_1_c", ""),
            cable.get("modulo_elasticidad_dan_mm2", ""),
            cable.get("carga_rotura_minima_dan", ""),
            cable.get("tension_rotura_minima", ""),
            cable.get("carga_max_trabajo", ""),
            cable.get("tension_max_trabajo", ""),
            cable.get("norma_fabricacion", "")
        )
    
    @app.callback(
        Output("input-cable-tipo-mod", "value", allow_duplicate=True),
        Output("input-cable-material-mod", "value", allow_duplicate=True),
        Output("input-cable-seccion-nominal-mod", "value", allow_duplicate=True),
        Output("input-cable-seccion-total-mod", "value", allow_duplicate=True),
        Output("input-cable-diametro-mod", "value", allow_duplicate=True),
        Output("input-cable-peso-mod", "value", allow_duplicate=True),
        Output("input-cable-dilatacion-mod", "value", allow_duplicate=True),
        Output("input-cable-modulo-mod", "value", allow_duplicate=True),
        Output("input-cable-rotura-mod", "value", allow_duplicate=True),
        Output("input-cable-tension-rotura-mod", "value", allow_duplicate=True),
        Output("input-cable-carga-max-mod", "value", allow_duplicate=True),
        Output("input-cable-tension-max-mod", "value", allow_duplicate=True),
        Output("input-cable-norma-mod", "value", allow_duplicate=True),
        Input("btn-copiar-cable-mod", "n_clicks"),
        State("select-cable-copiar-mod", "value"),
        prevent_initial_call=True
    )
    def copiar_cable_modificar(n_clicks, cable_id):
        if not n_clicks or not cable_id:
            raise dash.exceptions.PreventUpdate
        
        cable = state.cable_manager.obtener_cable(cable_id)
        if not cable:
            raise dash.exceptions.PreventUpdate
        
        return (
            cable.get("tipo", "OTRO"),
            cable.get("material", ""),
            cable.get("seccion_nominal", ""),
            cable.get("seccion_total_mm2", ""),
            cable.get("diametro_total_mm", ""),
            cable.get("peso_unitario_dan_m", ""),
            cable.get("coeficiente_dilatacion_1_c", ""),
            cable.get("modulo_elasticidad_dan_mm2", ""),
            cable.get("carga_rotura_minima_dan", ""),
            cable.get("tension_rotura_minima", ""),
            cable.get("carga_max_trabajo", ""),
            cable.get("tension_max_trabajo", ""),
            cable.get("norma_fabricacion", "")
        )
