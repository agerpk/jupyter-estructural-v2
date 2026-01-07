"""
Componente tabla editable para parámetros de estructura.
"""

import dash_bootstrap_components as dbc
from dash import html, dash_table, dcc
from typing import List, Dict, Any
from utils.parametros_manager import ParametrosManager

def crear_tabla_parametros(estructura_actual: Dict, cables_disponibles: List[str] = None) -> html.Div:
    """Crea tabla editable de parámetros"""
    
    # Convertir estructura a formato tabla
    tabla_data = ParametrosManager.estructura_a_tabla(estructura_actual)
    
    # Configurar columnas
    columnas = [
        {"name": "Categoría", "id": "categoria", "editable": False, "type": "text"},
        {"name": "Parámetro", "id": "parametro", "editable": False, "type": "text"},
        {"name": "Símbolo", "id": "simbolo", "editable": False, "type": "text"},
        {"name": "Valor", "id": "valor", "editable": True, "type": "any"},
        {"name": "Unidad", "id": "unidad", "editable": False, "type": "text"},
        {"name": "Descripción", "id": "descripcion", "editable": False, "type": "text"}
    ]
    
    return html.Div([
        html.H5("Parámetros de Estructura", className="mb-3"),
        
        # Botón para modificar estados climáticos
        dbc.Card([
            dbc.CardHeader(html.H6("Estados Climáticos y Restricciones")),
            dbc.CardBody([
                dbc.Button("Modificar Estados Climáticos y Restricciones", 
                          id="btn-modificar-estados-tabla", 
                          color="info", size="sm")
            ])
        ], className="mb-3"),
        
        # Modal para edición
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Editar Parámetro")),
            dbc.ModalBody(id="modal-body-parametro"),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-cancelar", color="secondary", className="me-2"),
                dbc.Button("Confirmar", id="modal-confirmar", color="primary")
            ])
        ], id="modal-parametro", is_open=False),
        
        # Modal para estados climáticos
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Estados Climáticos y Restricciones")),
            dbc.ModalBody(id="modal-estados-tabla-body"),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-estados-tabla-cancelar", color="secondary", className="me-2"),
                dbc.Button("Guardar", id="modal-estados-tabla-guardar", color="primary")
            ])
        ], id="modal-estados-tabla", is_open=False, size="xl"),
        
        dcc.Store(id="modal-celda-info", data=None),
        
        dash_table.DataTable(
            id="tabla-parametros",
            data=tabla_data,
            columns=columnas,
            editable=True,
            row_deletable=False,
            sort_action="native",
            filter_action="native",
            page_action="none",
            fixed_rows={'headers': True, 'data': 1},
            
            style_cell={
                'textAlign': 'right',
                'padding': '8px',
                'fontFamily': 'Arial, sans-serif',
                'fontSize': '14px',
                'color': '#000000',
                'backgroundColor': '#ffffff',
                'width': 'auto',
                'minWidth': '100px',
                'maxWidth': '300px'
            },
            style_header={
                'backgroundColor': '#007bff',
                'color': '#ffffff',
                'fontWeight': 'bold',
                'border': '1px solid #dee2e6',
                'textAlign': 'center',
                'position': 'sticky',
                'top': 0,
                'zIndex': 1
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
                    'if': {'row_index': 0},
                    'backgroundColor': '#fff3cd',
                    'fontWeight': 'bold',
                    'position': 'sticky',
                    'top': '40px',
                    'zIndex': 1
                },
                {
                    'if': {'column_id': 'valor'},
                    'backgroundColor': '#f8f9fa',
                    'color': '#000000'
                },
                {
                    'if': {'column_id': 'parametro'},
                    'fontWeight': 'bold',
                    'color': '#000000',
                    'textAlign': 'left'
                },
                {
                    'if': {'column_id': 'categoria'},
                    'color': '#000000',
                    'textAlign': 'left'
                }
            ],
            
            style_filter={
                'backgroundColor': '#e9ecef',
                'color': '#000000'
            },
            
            css=[{
                'selector': '.dash-table-container td.cell--selected, .dash-table-container td.focused, .dash-table-container .cell--selected, .dash-table-container .focused',
                'rule': 'background-color: #e3f2fd !important; color: #000000 !important; border: 1px solid #90caf9 !important;'
            }, {
                'selector': '.dash-table-container input.dash-cell-value, .dash-table-container input',
                'rule': 'background-color: #e3f2fd !important; color: #000000 !important; text-align: right !important;'
            }, {
                'selector': '.dash-table-container .cell:hover, .dash-table-container td:hover',
                'rule': 'background-color: #f0f8ff !important; color: #000000 !important;'
            }, {
                'selector': '.dash-table-container .cell.editing, .dash-table-container td.editing',
                'rule': 'background-color: #e3f2fd !important; color: #000000 !important;'
            }]
        )
    ])

def crear_filtros_categoria() -> html.Div:
    """Crea filtros por categoría"""
    
    categorias = ParametrosManager.obtener_parametros_por_categoria()
    opciones_categoria = [{"label": "Todas", "value": "todas"}]
    opciones_categoria.extend([{"label": cat, "value": cat} for cat in sorted(categorias.keys())])
    
    return dbc.Row([
        dbc.Col([
            html.Label("Filtrar por categoría:", className="form-label"),
            dbc.Select(
                id="filtro-categoria",
                options=opciones_categoria,
                value="todas",
                size="sm"
            )
        ], width=4),
        dbc.Col([
            html.Label("Buscar parámetro:", className="form-label"),
            dbc.Input(
                id="buscar-parametro",
                type="text",
                placeholder="Escriba para buscar...",
                size="sm"
            )
        ], width=4),
        dbc.Col([
            html.Label("Mostrar solo editables:", className="form-label"),
            dbc.Switch(
                id="solo-editables",
                value=False
            )
        ], width=4)
    ], className="mb-3")

def validar_tabla_parametros(tabla_data: List[Dict]) -> List[Dict]:
    """Valida datos de tabla y retorna errores"""
    errores = []
    
    for i, fila in enumerate(tabla_data):
        parametro = fila["parametro"]
        valor = fila["valor"]
        
        # Validar con ParametrosManager
        es_valido, mensaje = ParametrosManager.validar_valor(parametro, valor)
        
        if not es_valido:
            errores.append({
                "fila": i,
                "parametro": parametro,
                "valor": valor,
                "error": mensaje
            })
    
    return errores