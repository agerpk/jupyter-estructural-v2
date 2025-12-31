"""
Clase ModalCelda para edición de celdas con validación mediante modal.
"""

import dash_bootstrap_components as dbc
from dash import html, Input, Output, State, callback, no_update, dcc, ALL, callback_context
from typing import List, Dict, Any, Optional, Union

class ModalCelda:
    """Clase para crear modales de edición de celdas con validación"""
    
    def __init__(self, modal_id: str):
        self.modal_id = modal_id
        self.input_id = f"{modal_id}-input"
        self.confirm_id = f"{modal_id}-confirm"
        self.cancel_id = f"{modal_id}-cancel"
        self.buttons_id = f"{modal_id}-buttons"
    
    def crear_modal(self, titulo: str = "Editar Valor") -> dbc.Modal:
        """Crea el modal base"""
        return dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(titulo)),
            dbc.ModalBody(id=f"{self.modal_id}-body"),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id=self.cancel_id, color="secondary", className="me-2"),
                dbc.Button("Confirmar", id=self.confirm_id, color="primary")
            ])
        ], id=self.modal_id, is_open=False, size="md")
    
    def crear_contenido_opciones(self, opciones: List[str], valor_actual: str = "") -> html.Div:
        """Crea contenido con botones para selección de opciones"""
        botones = []
        for opcion in opciones:
            color = "primary" if opcion == valor_actual else "outline-secondary"
            botones.append(
                dbc.Button(
                    opcion,
                    id={"type": "opcion-btn", "modal": self.modal_id, "value": opcion},
                    color=color,
                    className="me-2 mb-2",
                    size="sm"
                )
            )
        
        return html.Div([
            html.P("Seleccione una opción:", className="mb-3"),
            html.Div(botones, id=self.buttons_id),
            dcc.Store(id=f"{self.modal_id}-valor-seleccionado", data=valor_actual)
        ])
    
    def crear_contenido_booleano(self, valor_actual: bool = False) -> html.Div:
        """Crea contenido para valores booleanos"""
        return html.Div([
            html.P("Seleccione el valor:", className="mb-3"),
            dbc.ButtonGroup([
                dbc.Button(
                    "Verdadero",
                    id={"type": "bool-btn", "modal": self.modal_id, "value": True},
                    color="success" if valor_actual else "outline-success",
                    size="lg"
                ),
                dbc.Button(
                    "Falso", 
                    id={"type": "bool-btn", "modal": self.modal_id, "value": False},
                    color="danger" if not valor_actual else "outline-danger",
                    size="lg"
                )
            ], className="w-100"),
            dcc.Store(id=f"{self.modal_id}-valor-seleccionado", data=valor_actual)
        ])
    
    def crear_contenido_numerico(self, valor_actual: Union[int, float] = 0, 
                                min_val: Optional[float] = None, 
                                max_val: Optional[float] = None,
                                step: float = 1) -> html.Div:
        """Crea contenido para valores numéricos con restricciones"""
        return html.Div([
            html.P("Ingrese el valor:", className="mb-3"),
            dbc.Input(
                id=self.input_id,
                type="number",
                value=valor_actual,
                min=min_val,
                max=max_val,
                step=step,
                size="lg"
            ),
            html.Small(
                f"Rango: {min_val or 'sin límite'} - {max_val or 'sin límite'}",
                className="text-muted mt-2"
            ) if min_val is not None or max_val is not None else None
        ])

def crear_callback_modal_opciones(app, modal_celda: ModalCelda):
    """Crea callback para modal de opciones"""
    
    @app.callback(
        [Output(f"{modal_celda.modal_id}-valor-seleccionado", "data"),
         Output(modal_celda.buttons_id, "children")],
        Input({"type": "opcion-btn", "modal": modal_celda.modal_id, "value": ALL}, "n_clicks"),
        [State(f"{modal_celda.modal_id}-valor-seleccionado", "data"),
         State(modal_celda.buttons_id, "children")],
        prevent_initial_call=True
    )
    def seleccionar_opcion(n_clicks_list, valor_actual, botones_actuales):
        """Maneja selección de opciones"""
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update
        
        # Obtener valor seleccionado
        trigger_id = ctx.triggered[0]["prop_id"]
        valor_seleccionado = eval(trigger_id.split(".")[0])["value"]
        
        # Actualizar botones
        nuevos_botones = []
        for boton_data in botones_actuales:
            if boton_data["props"]["children"] == valor_seleccionado:
                # Botón seleccionado
                boton_data["props"]["color"] = "primary"
            else:
                # Botón no seleccionado
                boton_data["props"]["color"] = "outline-secondary"
            nuevos_botones.append(boton_data)
        
        return valor_seleccionado, nuevos_botones

def crear_callback_modal_booleano(app, modal_celda: ModalCelda):
    """Crea callback para modal booleano"""
    
    @app.callback(
        Output(f"{modal_celda.modal_id}-valor-seleccionado", "data"),
        Input({"type": "bool-btn", "modal": modal_celda.modal_id, "value": ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def seleccionar_booleano(n_clicks_list):
        """Maneja selección booleana"""
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        
        trigger_id = ctx.triggered[0]["prop_id"]
        valor_seleccionado = eval(trigger_id.split(".")[0])["value"]
        
        return valor_seleccionado

def integrar_modal_con_tabla(app, modal_celda: ModalCelda, tabla_id: str):
    """Integra modal con DataTable para edición de celdas"""
    
    @app.callback(
        [Output(modal_celda.modal_id, "is_open"),
         Output(f"{modal_celda.modal_id}-body", "children"),
         Output(f"{modal_celda.modal_id}-celda-info", "data")],
        [Input(tabla_id, "active_cell"),
         Input(modal_celda.confirm_id, "n_clicks"),
         Input(modal_celda.cancel_id, "n_clicks")],
        [State(modal_celda.modal_id, "is_open"),
         State(tabla_id, "data"),
         State(f"{modal_celda.modal_id}-valor-seleccionado", "data")],
        prevent_initial_call=True
    )
    def manejar_modal_celda(active_cell, n_confirm, n_cancel, is_open, tabla_data, valor_seleccionado):
        """Maneja apertura/cierre del modal y edición de celdas"""
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Abrir modal al hacer clic en celda
        if trigger_id == tabla_id and active_cell:
            fila = active_cell["row"]
            columna = active_cell["column_id"]
            
            # Solo abrir modal para columna "valor"
            if columna != "valor":
                return no_update, no_update, no_update
            
            parametro = tabla_data[fila]["parametro"]
            valor_actual = tabla_data[fila]["valor"]
            tipo = tabla_data[fila]["tipo"]
            
            # Determinar tipo de contenido según el parámetro
            from utils.parametros_manager import ParametrosManager
            opciones = ParametrosManager.obtener_opciones_parametro(parametro)
            
            if opciones:  # Parámetro con opciones predefinidas
                contenido = modal_celda.crear_contenido_opciones(opciones, valor_actual)
            elif tipo == "bool":  # Parámetro booleano
                contenido = modal_celda.crear_contenido_booleano(valor_actual)
            elif tipo in ["int", "float"]:  # Parámetro numérico con restricciones
                # Obtener restricciones del parámetro
                min_val, max_val = ParametrosManager.obtener_rango_parametro(parametro)
                step = 1 if tipo == "int" else 0.1
                contenido = modal_celda.crear_contenido_numerico(valor_actual, min_val, max_val, step)
            else:
                return no_update, no_update, no_update  # No abrir modal para otros tipos
            
            celda_info = {"fila": fila, "columna": columna, "parametro": parametro}
            return True, contenido, celda_info
        
        # Cerrar modal
        elif trigger_id in [modal_celda.confirm_id, modal_celda.cancel_id]:
            return False, no_update, no_update
        
        return no_update, no_update, no_update
    
    @app.callback(
        Output(tabla_id, "data", allow_duplicate=True),
        Input(modal_celda.confirm_id, "n_clicks"),
        [State(f"{modal_celda.modal_id}-celda-info", "data"),
         State(f"{modal_celda.modal_id}-valor-seleccionado", "data"),
         State(modal_celda.input_id, "value"),
         State(tabla_id, "data")],
        prevent_initial_call=True
    )
    def actualizar_celda(n_confirm, celda_info, valor_seleccionado, valor_input, tabla_data):
        """Actualiza valor de celda después de confirmar modal"""
        if not n_confirm or not celda_info:
            return no_update
        
        fila = celda_info["fila"]
        parametro = celda_info["parametro"]
        
        # Determinar valor final
        if valor_seleccionado is not None:
            nuevo_valor = valor_seleccionado
        elif valor_input is not None:
            nuevo_valor = valor_input
        else:
            return no_update
        
        # Actualizar tabla
        tabla_data[fila]["valor"] = nuevo_valor
        
        return tabla_data

# Store para información de celda
def crear_store_celda_info(modal_id: str):
    """Crea store para información de celda editada"""
    return dcc.Store(id=f"{modal_id}-celda-info", data=None)