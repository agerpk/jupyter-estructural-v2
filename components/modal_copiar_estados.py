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
        dbc.ModalHeader(
            dbc.ModalTitle("Copiar Estados Desde Estructura", style={"color": "#ffffff"}),
            style={"backgroundColor": "#1e1e1e"}
        ),
        dbc.ModalBody([
            html.P("Seleccione la estructura origen:", className="mb-3", style={"color": "#ffffff"}),
            dcc.Dropdown(
                id=f"{modal_id}-dropdown-estructuras",
                placeholder="Seleccione estructura...",
                className="mb-3",
                style={"backgroundColor": "#1e1e1e", "color": "#ffffff"}
            ),
            dbc.Alert(
                "Los estados actuales serán reemplazados completamente por los de la estructura seleccionada.",
                color="warning",
                className="mb-0"
            )
        ], style={"backgroundColor": "#2d2d2d"}),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id=f"{modal_id}-btn-cancelar", color="secondary", className="me-2"),
            dbc.Button("Confirmar", id=f"{modal_id}-btn-confirmar", color="primary")
        ], style={"backgroundColor": "#1e1e1e"})
    ], id=modal_id, is_open=False, size="md")
