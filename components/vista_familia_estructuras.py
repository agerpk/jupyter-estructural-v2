"""
Vista para gestión de Familias de Estructuras
"""

from dash import html, dcc, dash_table, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import json

def crear_vista_familia_estructuras(familia_actual=None):
    """Crear vista principal de Familias de Estructuras"""
    
    if familia_actual is None:
        familia_actual = {
            "nombre_familia": "",
            "estructuras": {
                "Estr.1": cargar_plantilla_estructura()
            }
        }
    
    # Generar datos de tabla
    tabla_data = generar_datos_tabla_familia(familia_actual)
    
    # Configurar columnas dinámicamente
    columnas = [
        {"name": "Parámetro", "id": "parametro", "editable": False, "type": "text"},
        {"name": "Símbolo", "id": "simbolo", "editable": False, "type": "text"},
        {"name": "Unidad", "id": "unidad", "editable": False, "type": "text"},
        {"name": "Descripción", "id": "descripcion", "editable": False, "type": "text"}
    ]
    
    # Agregar columnas de estructuras
    estructuras = familia_actual.get("estructuras", {})
    for nombre_estr in sorted(estructuras.keys()):
        columnas.append({
            "name": nombre_estr,
            "id": nombre_estr,
            "editable": True,
            "type": "any"
        })
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Familia de Estructuras", className="mb-0")),
            dbc.CardBody([
                # Campo nombre familia
                crear_campo_nombre_familia(familia_actual.get("nombre_familia", "")),
                html.Hr(),
                
                # Botones de acción
                crear_botones_familia(),
                html.Hr(),
                
                # Tabla de parámetros multi-columna
                dash_table.DataTable(
                    id="tabla-familia",
                    data=tabla_data,
                    columns=columnas,
                    editable=True,
                    row_deletable=False,
                    sort_action="native",
                    filter_action="native",
                    page_action="none",
                    
                    style_cell={
                        'textAlign': 'right',
                        'padding': '8px',
                        'fontFamily': 'Arial, sans-serif',
                        'fontSize': '14px',
                        'color': '#000000',
                        'backgroundColor': '#ffffff',
                        'width': 'auto',
                        'minWidth': '80px',
                        'maxWidth': '200px'
                    },
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'parametro'},
                            'width': '150px',
                            'textAlign': 'left'
                        },
                        {
                            'if': {'column_id': 'simbolo'},
                            'width': '80px',
                            'textAlign': 'center'
                        },
                        {
                            'if': {'column_id': 'unidad'},
                            'width': '80px',
                            'textAlign': 'center'
                        },
                        {
                            'if': {'column_id': 'descripcion'},
                            'width': '200px',
                            'textAlign': 'left'
                        }
                    ],
                    style_header={
                        'backgroundColor': '#007bff',
                        'color': '#ffffff',
                        'fontWeight': 'bold',
                        'border': '1px solid #dee2e6',
                        'textAlign': 'center'
                    },
                    style_data={
                        'border': '1px solid #dee2e6',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                        'color': '#000000',
                        'backgroundColor': '#ffffff'
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'parametro'},
                            'fontWeight': 'bold',
                            'color': '#000000',
                            'textAlign': 'left',
                            'backgroundColor': '#f8f9fa'
                        }
                    ] + [
                        {
                            'if': {'column_id': nombre_estr},
                            'backgroundColor': '#f0f8ff',
                            'color': '#000000'
                        }
                        for nombre_estr in estructuras.keys()
                    ],
                    
                    css=[{
                        'selector': '.dash-table-container td.cell--selected, .dash-table-container td.focused',
                        'rule': 'background-color: #e3f2fd !important; color: #000000 !important; border: 1px solid #90caf9 !important;'
                    }]
                ),
                
                # Modales
                crear_modales_familia()
            ])
        ])
    ])

# Callback para abrir modal al hacer click en celda
@callback(
    [Output("modal-familia-parametro", "is_open"),
     Output("modal-body-familia-parametro", "children"),
     Output("modal-familia-celda-info", "data")],
    [Input("tabla-familia", "active_cell")],
    [State("tabla-familia", "data"),
     State("modal-familia-parametro", "is_open")],
    prevent_initial_call=True
)
def abrir_modal_celda_familia(active_cell, tabla_data, is_open):
    """Abrir modal para editar celda de familia"""
    if not active_cell or not tabla_data:
        return False, "", None
    
    fila_idx = active_cell["row"]
    columna_id = active_cell["column_id"]
    
    # Solo abrir modal para columnas de estructura (Estr.X)
    if not columna_id.startswith("Estr."):
        return False, "", None
    
    fila = tabla_data[fila_idx]
    parametro = fila["parametro"]
    valor_actual = fila.get(columna_id, "")
    
    # Crear contenido del modal según tipo de parámetro
    from utils.parametros_manager import ParametrosManager
    opciones = ParametrosManager.obtener_opciones_parametro(parametro)
    
    if opciones:  # Parámetro tipo select
        contenido = [
            html.P(f"Editando: {parametro} - {columna_id}"),
            dbc.Label("Seleccione valor:"),
            dbc.Select(
                id="modal-familia-input",
                options=[{"label": opt, "value": opt} for opt in opciones],
                value=valor_actual
            )
        ]
    else:  # Parámetro numérico o texto
        contenido = [
            html.P(f"Editando: {parametro} - {columna_id}"),
            dbc.Label("Nuevo valor:"),
            dbc.Input(
                id="modal-familia-input",
                type="text",
                value=valor_actual
            )
        ]
    
    celda_info = {
        "fila": fila_idx,
        "columna": columna_id,
        "parametro": parametro,
        "valor_original": valor_actual
    }
    
    return True, contenido, celda_info

@callback(
    [Output("tabla-familia", "data", allow_duplicate=True),
     Output("modal-familia-parametro", "is_open", allow_duplicate=True)],
    [Input("modal-familia-confirmar", "n_clicks")],
    [State("modal-familia-input", "value"),
     State("modal-familia-celda-info", "data"),
     State("tabla-familia", "data")],
    prevent_initial_call=True
)
def confirmar_edicion_celda_familia(n_clicks, nuevo_valor, celda_info, tabla_data):
    """Confirmar edición de celda en familia"""
    if not n_clicks or not celda_info or not tabla_data:
        return no_update, no_update
    
    # Actualizar valor en tabla
    fila_idx = celda_info["fila"]
    columna_id = celda_info["columna"]
    
    tabla_data[fila_idx][columna_id] = nuevo_valor
    
    return tabla_data, False

@callback(
    Output("modal-familia-parametro", "is_open", allow_duplicate=True),
    [Input("modal-familia-cancelar", "n_clicks")],
    prevent_initial_call=True
)
def cancelar_edicion_celda_familia(n_clicks):
    """Cancelar edición de celda"""
    if n_clicks:
        return False
    return no_update

def crear_campo_nombre_familia(nombre_actual):
    """Crear campo para nombre de familia"""
    return dbc.Row([
        dbc.Col([
            html.Label("NOMBRE FAMILIA:", className="form-label fw-bold"),
            dbc.Input(
                id="input-nombre-familia",
                type="text",
                value=nombre_actual,
                placeholder="Ingrese nombre de la familia...",
                size="lg"
            )
        ], width=6)
    ], className="mb-3")

def crear_botones_familia():
    """Crear botones de acción para familia"""
    return dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("Agregar Estructura", id="btn-agregar-estructura", color="success", size="sm"),
                dbc.Button("Eliminar Estructura", id="btn-eliminar-estructura", color="danger", size="sm"),
                dbc.Button("Cargar Columna", id="btn-cargar-columna", color="info", size="sm")
            ])
        ], width=6),
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("Guardar Familia", id="btn-guardar-familia", color="primary", size="sm"),
                dbc.Button("Cargar Familia", id="btn-cargar-familia", color="secondary", size="sm"),
                dbc.Button("Cargar Cache", id="btn-cargar-cache-familia", color="warning", size="sm"),
                dbc.Button("Calcular Familia", id="btn-calcular-familia", color="success", size="sm")
            ])
        ], width=6)
    ], className="mb-3")



def crear_modales_familia():
    """Crear modales para edición de familia"""
    return html.Div([
        # Modal para cargar columna con estructura existente
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Cargar Columna con Estructura Existente")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Estructura a cargar:", className="form-label"),
                        dbc.Select(
                            id="select-estructura-cargar",
                            placeholder="Seleccione estructura..."
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label("Columna destino:", className="form-label"),
                        dbc.Select(
                            id="select-columna-destino",
                            placeholder="Seleccione columna..."
                        )
                    ], width=6)
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancelar-cargar-columna", color="secondary", className="me-2"),
                dbc.Button("Cargar", id="btn-confirmar-cargar-columna", color="primary")
            ])
        ], id="modal-cargar-columna", is_open=False),
        
        # Modal para cargar familia
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Cargar Familia")),
            dbc.ModalBody([
                html.Label("Seleccionar familia:", className="form-label"),
                dbc.Select(
                    id="select-familia-cargar",
                    placeholder="Seleccione familia..."
                )
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancelar-cargar-familia", color="secondary", className="me-2"),
                dbc.Button("Cargar", id="btn-confirmar-cargar-familia", color="primary")
            ])
        ], id="modal-cargar-familia", is_open=False),
        
        # Modal para editar celda (reutilizar de ajustar parámetros)
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Editar Parámetro")),
            dbc.ModalBody(id="modal-body-familia-parametro"),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-familia-cancelar", color="secondary", className="me-2"),
                dbc.Button("Confirmar", id="modal-familia-confirmar", color="primary")
            ])
        ], id="modal-familia-parametro", is_open=False),
        
        # Store para datos de celda
        dcc.Store(id="modal-familia-celda-info", data=None)
    ])

def generar_datos_tabla_familia(familia_actual):
    """Generar datos para tabla de familia usando ParametrosManager"""
    
    # Cargar plantilla para obtener estructura de parámetros
    plantilla = cargar_plantilla_estructura()
    
    if not plantilla:
        return []
    
    # Obtener estructuras de la familia
    estructuras = familia_actual.get("estructuras", {"Estr.1": plantilla})
    
    # Usar ParametrosManager para generar datos completos
    from utils.parametros_manager import ParametrosManager
    tabla_base = ParametrosManager.estructura_a_tabla(plantilla)
    
    # Generar filas de tabla
    tabla_data = []
    
    # Agregar campo cantidad (no está en plantilla)
    fila_cantidad = {
        "parametro": "cantidad",
        "simbolo": "Q",
        "unidad": "u",
        "descripcion": "Cantidad de estructuras"
    }
    for nombre_estr, datos_estr in estructuras.items():
        fila_cantidad[nombre_estr] = datos_estr.get("cantidad", 1)
    tabla_data.append(fila_cantidad)
    
    # Agregar todos los parámetros de la tabla base
    for fila_base in tabla_base:
        parametro = fila_base["parametro"]
        
        fila = {
            "parametro": parametro,
            "simbolo": fila_base["simbolo"],
            "unidad": fila_base["unidad"],
            "descripcion": fila_base["descripcion"]
        }
        
        # Agregar valores de cada estructura
        for nombre_estr, datos_estr in estructuras.items():
            # Manejar parámetros anidados de costeo
            if parametro.startswith("costeo."):
                parts = parametro.split(".")
                valor = datos_estr
                for part in parts:
                    if isinstance(valor, dict) and part in valor:
                        valor = valor[part]
                    else:
                        valor = fila_base["valor"]  # Valor por defecto
                        break
                fila[nombre_estr] = valor
            else:
                fila[nombre_estr] = datos_estr.get(parametro, fila_base["valor"])
        
        tabla_data.append(fila)
    
    return tabla_data

def cargar_plantilla_estructura():
    """Cargar plantilla de estructura"""
    try:
        with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def obtener_info_parametros():
    """Obtener información de parámetros (símbolo, unidad, descripción)"""
    # Reutilizar de vista_ajuste_parametros.py
    return {
        "TITULO": {"simbolo": "T", "unidad": "", "descripcion": "Título de la estructura"},
        "TIPO_ESTRUCTURA": {"simbolo": "TE", "unidad": "", "descripcion": "Tipo de estructura"},
        "TENSION": {"simbolo": "V", "unidad": "kV", "descripcion": "Tensión nominal"},
        "L_vano": {"simbolo": "L", "unidad": "m", "descripcion": "Vano regulador de diseño"},
        "alpha": {"simbolo": "α", "unidad": "°", "descripcion": "Ángulo de quiebre máximo"},
        "theta": {"simbolo": "θ", "unidad": "°", "descripcion": "Ángulo de viento oblicuo"},
        "Vmax": {"simbolo": "Vmax", "unidad": "m/s", "descripcion": "Viento máximo"},
        "Vmed": {"simbolo": "Vmed", "unidad": "m/s", "descripcion": "Viento medio"},
        "Vtormenta": {"simbolo": "Vt", "unidad": "m/s", "descripcion": "Viento de tormenta"},
        "DISPOSICION": {"simbolo": "D", "unidad": "", "descripcion": "Disposición de conductores"},
        "TERNA": {"simbolo": "T", "unidad": "", "descripcion": "Tipo de terna"},
        "CANT_HG": {"simbolo": "HG", "unidad": "u", "descripcion": "Cantidad cables guardia"},
        "ALTURA_MINIMA_CABLE": {"simbolo": "Hmin", "unidad": "m", "descripcion": "Altura mínima cable"},
        "cantidad": {"simbolo": "Q", "unidad": "u", "descripcion": "Cantidad de estructuras"}
        # Agregar más según necesidad
    }