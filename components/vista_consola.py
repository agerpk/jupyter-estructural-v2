"""Vista de consola - Muestra output capturado desde inicio de app"""
from dash import html, dcc
import dash_bootstrap_components as dbc

def crear_vista_consola():
    """Crear vista de consola"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("Consola de Sistema", className="mb-3"),
                html.P("Output capturado desde el inicio de la aplicación", className="text-muted"),
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Button("Actualizar", id="btn-actualizar-consola", color="primary", className="me-2"),
            ], width=12, className="mb-3")
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Pre(
                    id="consola-output",
                    style={
                        "backgroundColor": "#1e1e1e",
                        "color": "#d4d4d4",
                        "padding": "15px",
                        "borderRadius": "5px",
                        "minHeight": "500px",
                        "maxHeight": "65vh",
                        "overflow": "auto",
                        "fontFamily": "Consolas, Monaco, 'Courier New', monospace",
                        "fontSize": "13px",
                        "lineHeight": "1.4",
                        "whiteSpace": "pre-wrap",
                        "wordWrap": "break-word",
                        "userSelect": "text"
                    }
                )
            ], width=12)
        ]),
        
        # Store para indicar que estamos en vista consola
        dcc.Store(id="consola-activa", data=True)
    ], className="container-fluid mt-4")
