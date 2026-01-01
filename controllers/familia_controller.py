"""
Controlador para gestión de Familias de Estructuras
"""

from dash import callback, Input, Output, State, ctx, no_update, ALL
import dash_bootstrap_components as dbc
from dash import html
import json
from pathlib import Path
from datetime import datetime

def register_callbacks(app):
    """Registrar callbacks de familia"""
    
    # Callback para manejar modal
    @app.callback(
        [Output("modal-familia-parametro", "is_open"),
         Output("modal-familia-body-parametro", "children"),
         Output("modal-familia-celda-info", "data")],
        [Input("tabla-familia", "active_cell"),
         Input("modal-familia-confirmar", "n_clicks"),
         Input("modal-familia-cancelar", "n_clicks")],
        [State("modal-familia-parametro", "is_open"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def manejar_modal_parametro(active_cell, n_confirm, n_cancel, is_open, tabla_data):
        """Maneja apertura/cierre del modal"""
        from dash import ctx, no_update, html
        import dash_bootstrap_components as dbc
        
        print(f"DEBUG: Callback modal ejecutado - active_cell: {active_cell}")
        
        if not ctx.triggered:
            print("DEBUG: No hay trigger, retornando no_update")
            return no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        print(f"DEBUG: Trigger ID: {trigger_id}")
        
        # Abrir modal al hacer clic en celda
        if trigger_id == "tabla-familia" and active_cell:
            print(f"DEBUG: Click en tabla detectado - columna: {active_cell.get('column_id')}")
            
            if not active_cell.get("column_id", "").startswith("Estr."):
                print("DEBUG: Columna no es Estr.X, no abrir modal")
                return no_update, no_update, no_update
            
            fila = active_cell["row"]
            columna = active_cell["column_id"]
            
            if not tabla_data or fila >= len(tabla_data):
                print("DEBUG: Datos de tabla inválidos")
                return no_update, no_update, no_update
            
            parametro = tabla_data[fila]["parametro"]
            valor_actual = tabla_data[fila][columna]
            tipo = tabla_data[fila].get("tipo", "str")
            
            print(f"DEBUG: Parámetro: {parametro}, Valor: {valor_actual}, Tipo: {tipo}")
            
            # Solo abrir modal para tipos no numéricos
            if tipo in ["int", "float"]:
                print("DEBUG: Tipo numérico, no abrir modal")
                return no_update, no_update, no_update
            
            # Obtener opciones si es select
            from utils.parametros_manager import ParametrosManager
            opciones = ParametrosManager.obtener_opciones_parametro(parametro)
            print(f"DEBUG: Opciones obtenidas: {opciones}")
            
            if opciones:
                # Modal con botones para opciones
                botones = []
                for opcion in opciones:
                    color = "primary" if opcion == valor_actual else "outline-secondary"
                    botones.append(
                        dbc.Button(
                            opcion,
                            id={"type": "familia-opcion-btn", "value": opcion},
                            color=color,
                            className="me-2 mb-2",
                            size="sm"
                        )
                    )
                contenido = html.Div([
                    html.P(f"Seleccione valor para {parametro}:"),
                    html.Div(botones)
                ])
            elif tipo == "bool":
                # Modal para booleanos
                contenido = html.Div([
                    html.P(f"Seleccione valor para {parametro}:"),
                    dbc.ButtonGroup([
                        dbc.Button(
                            "Verdadero",
                            id={"type": "familia-bool-btn", "value": True},
                            color="success" if valor_actual else "outline-success"
                        ),
                        dbc.Button(
                            "Falso",
                            id={"type": "familia-bool-btn", "value": False},
                            color="danger" if not valor_actual else "outline-danger"
                        )
                    ])
                ])
            else:
                # Modal para texto
                contenido = html.Div([
                    html.P(f"Ingrese valor para {parametro}:"),
                    dbc.Input(
                        id="input-valor",
                        type="text",
                        value=valor_actual
                    )
                ])
            
            celda_info = {"fila": fila, "columna": columna, "parametro": parametro}
            print(f"DEBUG: Abriendo modal con celda_info: {celda_info}")
            return True, contenido, celda_info
        
        # Cerrar modal
        elif trigger_id in ["modal-familia-confirmar", "modal-familia-cancelar"]:
            print("DEBUG: Cerrando modal")
            return False, no_update, no_update
        
        print("DEBUG: Trigger no reconocido")
        return no_update, no_update, no_update
    
    # Callback para selección directa
    @app.callback(
        [Output("tabla-familia", "data", allow_duplicate=True),
         Output("modal-familia-parametro", "is_open", allow_duplicate=True)],
        [Input({"type": "familia-opcion-btn", "value": ALL}, "n_clicks"),
         Input({"type": "familia-bool-btn", "value": ALL}, "n_clicks")],
        [State("modal-familia-celda-info", "data"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def seleccionar_opcion_directa(n_clicks_opciones, n_clicks_bool, celda_info, tabla_data):
        """Actualiza tabla directamente al seleccionar opción y cierra modal"""
        from dash import ctx, no_update
        
        if not ctx.triggered or not celda_info:
            return no_update, no_update
        
        # Obtener el valor seleccionado
        trigger = ctx.triggered[0]
        if trigger["value"] is None:
            return no_update, no_update
        
        # Extraer valor del componente que disparó el callback
        component_id = trigger["prop_id"].split(".")[0]
        import json
        component_data = json.loads(component_id)
        valor_seleccionado = component_data["value"]
        
        # Actualizar tabla
        fila = celda_info["fila"]
        columna = celda_info["columna"]
        tabla_data[fila][columna] = valor_seleccionado
        
        # Cerrar modal y actualizar tabla
        return tabla_data, False

# Callback único para navegación
@callback(
    Output("contenido-principal", "children", allow_duplicate=True),
    [Input("menu-familia-estructuras", "n_clicks")],
    prevent_initial_call=True
)
def mostrar_vista_familia(n_clicks):
    """Mostrar vista de familia de estructuras"""
    if not n_clicks:
        return no_update
    
    try:
        from components.vista_familia_estructuras import crear_vista_familia_estructuras
        familia_actual = None  # Por ahora usar valores por defecto
        vista = crear_vista_familia_estructuras(familia_actual)
        return vista
    except Exception as e:
        return html.Div([
            dbc.Alert(f"Error al cargar vista familia: {str(e)}", color="danger")
        ])