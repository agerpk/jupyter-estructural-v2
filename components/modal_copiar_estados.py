"""
Sub-modal para copiar estados climáticos desde otra estructura.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

def crear_modal_copiar_estados(modal_id="modal-copiar-estados"):
    """
    Crea sub-modal para copiar estados desde otra estructura
    
    Args:
        modal_id: ID del sub-modal
    
    Returns:
        dbc.Modal con dropdown de estructuras
    """
    
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Copiar Estados Desde Estructura")),
        dbc.ModalBody([
            html.P("Seleccione la estructura origen:", className="mb-3"),
            dcc.Dropdown(
                id=f"{modal_id}-dropdown-estructuras",
                placeholder="Seleccione estructura...",
                className="mb-3"
            ),
            dbc.Alert(
                "Los estados actuales serán reemplazados completamente por los de la estructura seleccionada.",
                color="warning",
                className="mb-0"
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id=f"{modal_id}-btn-cancelar", color="secondary", className="me-2"),
            dbc.Button("Confirmar", id=f"{modal_id}-btn-confirmar", color="primary")
        ])
    ], id=modal_id, is_open=False, size="md")
