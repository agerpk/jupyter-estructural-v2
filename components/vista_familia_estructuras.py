"""
Vista para gestión de Familias de Estructuras
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import json

def crear_vista_familia_estructuras(familia_actual=None):
    """Crear vista principal de Familias de Estructuras"""
    
    print("DEBUG: Iniciando crear_vista_familia_estructuras")
    
    if familia_actual is None:
        familia_actual = {
            "nombre_familia": "",
            "estructuras": {
                "Estr.1": cargar_plantilla_estructura()
            }
        }
        print("DEBUG: Familia actual creada por defecto")
    else:
        print(f"DEBUG: Familia actual recibida: {familia_actual.get('nombre_familia', 'Sin nombre')}")
    
    # Generar datos de tabla
    tabla_data = generar_datos_tabla_familia(familia_actual)
    print(f"DEBUG: Tabla generada con {len(tabla_data)} filas")
    
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
            "editable": False,  # Usar modal
            "type": "any"
        })
    
    print(f"DEBUG: Columnas configuradas: {[col['id'] for col in columnas]}")
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Familia de Estructuras", className="mb-0")),
            dbc.CardBody([
                # Campo nombre familia
                crear_campo_nombre_familia(familia_actual.get("nombre_familia", "")),
                html.Hr(),
                
                # Tabla de parámetros multi-columna
                dash_table.DataTable(
                    id="tabla-familia",
                    data=tabla_data,
                    columns=columnas,
                    editable=False,  # Usar modal
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
                        'maxWidth': '200px',
                        'cursor': 'pointer'
                    },
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'parametro'},
                            'width': '150px',
                            'textAlign': 'left'
                        }
                    ] + [
                        {
                            'if': {'column_id': nombre_estr},
                            'backgroundColor': '#f0f8ff',
                            'color': '#000000',
                            'cursor': 'pointer'
                        }
                        for nombre_estr in estructuras.keys()
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
                    }
                ),
                
                # Modal para edición
                crear_modal_familia()
            ])
        ])
    ])

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

def crear_modal_familia():
    """Crear modal para edición de celda"""
    return html.Div([
        # Modal para editar celda
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Editar Parámetro")),
            dbc.ModalBody(id="modal-familia-body-parametro"),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-familia-cancelar", color="secondary", className="me-2"),
                dbc.Button("Confirmar", id="modal-familia-confirmar", color="primary")
            ])
        ], id="modal-familia-parametro", is_open=False),
        
        # Stores para datos
        dcc.Store(id="modal-familia-celda-info", data=None)
    ])

# Los callbacks están ahora en familia_controller.py

def generar_datos_tabla_familia(familia_actual):
    """Generar datos para tabla de familia usando ParametrosManager"""
    
    print("DEBUG: Iniciando generar_datos_tabla_familia")
    
    # Cargar plantilla para obtener estructura de parámetros
    plantilla = cargar_plantilla_estructura()
    
    if not plantilla:
        print("DEBUG: No se pudo cargar plantilla")
        return []
    
    print(f"DEBUG: Plantilla cargada con {len(plantilla)} campos")
    
    # Obtener estructuras de la familia
    estructuras = familia_actual.get("estructuras", {"Estr.1": plantilla})
    print(f"DEBUG: Estructuras en familia: {list(estructuras.keys())}")
    
    # Usar ParametrosManager para generar datos completos
    from utils.parametros_manager import ParametrosManager
    tabla_base = ParametrosManager.estructura_a_tabla(plantilla)
    print(f"DEBUG: Tabla base generada con {len(tabla_base)} parámetros")
    
    # Generar filas de tabla
    tabla_data = []
    
    # Agregar todos los parámetros de la tabla base
    for fila_base in tabla_base:
        parametro = fila_base["parametro"]
        
        fila = {
            "parametro": parametro,
            "simbolo": fila_base["simbolo"],
            "unidad": fila_base["unidad"],
            "descripcion": fila_base["descripcion"],
            "tipo": fila_base["tipo"]
        }
        
        # Agregar valores de cada estructura
        for nombre_estr, datos_estr in estructuras.items():
            fila[nombre_estr] = datos_estr.get(parametro, fila_base["valor"])
        
        tabla_data.append(fila)
    
    print(f"DEBUG: Tabla final generada con {len(tabla_data)} filas")
    if tabla_data:
        print(f"DEBUG: Primera fila: {tabla_data[0]}")
    
    return tabla_data

def cargar_plantilla_estructura():
    """Cargar plantilla de estructura"""
    try:
        with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}