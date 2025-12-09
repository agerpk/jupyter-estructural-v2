"""
Vista principal/home de la aplicación
"""

from dash import html
import dash_bootstrap_components as dbc

def crear_vista_home():
    """Crear vista principal/home"""
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Resumen de Estructura Actual", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="resumen-estructura-actual"),
                        dbc.Button(
                            "Ver Detalles Completos",
                            id="btn-ver-detalles",
                            color="info",
                            className="mt-3"
                        )
                    ])
                ])
            ], width=12)
        ])
    ])
