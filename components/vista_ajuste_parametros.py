"""
Vista para ajustar parámetros de la estructura actual
"""

from dash import html
import dash_bootstrap_components as dbc
from components.parametro_input import crear_grupo_parametros

def crear_vista_ajuste_parametros():
    """Crear vista de ajuste de parámetros"""
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Ajustar Parámetros de Estructura", className="mb-0")),
            dbc.CardBody([
                dbc.Alert(
                    "Modifique los parámetros de la estructura actual. Los cambios se guardarán al presionar 'Guardar Parámetros'.",
                    color="warning",
                    className="mb-4"
                ),
                
                html.Div(id="contenedor-parametros"),
                
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Guardar Parámetros",
                            id="guardar-parametros",
                            color="success",
                            size="lg",
                            className="w-100"
                        ),
                        width=6
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Volver",
                            id="btn-volver-home",
                            color="secondary",
                            size="lg",
                            className="w-100"
                        ),
                        width=6
                    )
                ], className="mt-4")
            ])
        ])
    ])

# Callback para poblar parámetros (se implementará en app principal)