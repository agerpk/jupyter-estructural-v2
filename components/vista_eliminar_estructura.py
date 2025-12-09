"""
Vista para eliminar estructuras de la base de datos
"""

from dash import html
import dash_bootstrap_components as dbc

def crear_vista_eliminar_estructura():
    """Crear vista para eliminar estructuras con modal"""
    
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
                            placeholder="Seleccione una estructura...",
                            className="mb-3"
                        ),
                    ], width=8)
                ]),
                
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Eliminar Estructura",
                            id="btn-eliminar-estructura",
                            color="danger",
                            size="lg",
                            className="w-100"
                        ),
                        width=4
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Volver",
                            id={"type": "btn-volver", "index": "eliminar"},
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
