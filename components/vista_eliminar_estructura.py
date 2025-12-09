"""
Vista para eliminar estructuras de la base de datos
"""

from dash import html
import dash_bootstrap_components as dbc
from utils.estructura_manager import EstructuraManager

def crear_vista_eliminar_estructura():
    """Crear vista para eliminar estructuras"""
    
    # Obtener estructuras disponibles (esto se actualizará via callback)
    estructura_manager = EstructuraManager(Path("data"))
    estructuras = estructura_manager.listar_estructuras()
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Eliminar Estructura de Base de Datos", className="mb-0")),
            dbc.CardBody([
                dbc.Alert(
                    [
                        html.Strong("¡Precaución!"),
                        " Esta acción eliminará permanentemente la estructura seleccionada. ",
                        "No se puede deshacer."
                    ],
                    color="danger",
                    className="mb-4"
                ),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Seleccionar estructura a eliminar:"),
                        dbc.Select(
                            id="select-estructura-eliminar",
                            options=[{"label": e, "value": e} for e in estructuras],
                            placeholder="Seleccione una estructura...",
                            className="mb-3"
                        ),
                        
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Información de la estructura seleccionada:", className="mb-3"),
                                html.Div(id="info-estructura-eliminar")
                            ])
                        ], className="mb-4")
                    ], width=8)
                ]),
                
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Eliminar Estructura",
                            id="btn-eliminar-confirmar",
                            color="danger",
                            size="lg",
                            className="w-100",
                            disabled=len(estructuras) == 0
                        ),
                        width=4
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Volver",
                            id="btn-volver-home",
                            color="secondary",
                            size="lg",
                            className="w-100"
                        ),
                        width=4
                    )
                ], justify="between")
            ])
        ])
    ])