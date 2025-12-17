"""Vista para ajustar parámetros de catenaria"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def crear_vista_ajustar_catenaria(datos_catenaria):
    """Crear vista de ajuste de catenaria"""
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4(f"Ajustar Catenaria: {datos_catenaria.get('TITULO', '')}", className="mb-0")),
            dbc.CardBody([
                # Parámetros de Diseño de Línea
                html.H5("PARÁMETROS DE DISEÑO DE LÍNEA", className="text-info mt-3 mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("L_vano (m):"),
                        dbc.Input(id="cat-L_vano", type="number", value=datos_catenaria.get("L_vano", 400), className="mb-3"),
                        
                        dbc.Label("Vmax (m/s):"),
                        dbc.Input(id="cat-Vmax", type="number", value=datos_catenaria.get("Vmax", 38.9), className="mb-3"),
                        
                        dbc.Label("Vmed (m/s):"),
                        dbc.Input(id="cat-Vmed", type="number", value=datos_catenaria.get("Vmed", 15.56), className="mb-3"),
                        
                        dbc.Label("Q:"),
                        dbc.Input(id="cat-Q", type="number", value=datos_catenaria.get("Q", 0.0613), step=0.0001, className="mb-3"),
                        
                        dbc.Label("Zco (m):"),
                        dbc.Input(id="cat-Zco", type="number", value=datos_catenaria.get("Zco", 13), className="mb-3"),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Cf_cable:"),
                        dbc.Input(id="cat-Cf_cable", type="number", value=datos_catenaria.get("Cf_cable", 1.0), step=0.1, className="mb-3"),
                        
                        dbc.Label("exposicion:"),
                        dbc.Select(id="cat-exposicion", options=[
                            {"label": "B", "value": "B"},
                            {"label": "C", "value": "C"},
                            {"label": "D", "value": "D"}
                        ], value=datos_catenaria.get("exposicion", "C"), className="mb-3"),
                        
                        dbc.Label("Zona_climatica:"),
                        dbc.Select(id="cat-Zona_climatica", options=[
                            {"label": "A", "value": "A"},
                            {"label": "B", "value": "B"},
                            {"label": "C", "value": "C"},
                            {"label": "D", "value": "D"},
                            {"label": "E", "value": "E"}
                        ], value=datos_catenaria.get("Zona_climatica", "D"), className="mb-3"),
                    ], md=6)
                ]),
                
                # Configuración de Flechado
                html.H5("CONFIGURACIÓN DE FLECHADO / CÁLCULO MECÁNICO", className="text-info mt-4 mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("SALTO_PORCENTUAL:"),
                        dcc.Slider(id="cat-SALTO_PORCENTUAL", min=0, max=0.1, step=0.01, 
                                  value=datos_catenaria.get("SALTO_PORCENTUAL", 0.05),
                                  marks={0: '0%', 0.05: '5%', 0.1: '10%'},
                                  tooltip={"placement": "bottom", "always_visible": True}, className="mb-4"),
                        
                        dbc.Label("PASO_AFINADO:"),
                        dcc.Slider(id="cat-PASO_AFINADO", min=0, max=0.02, step=0.001,
                                  value=datos_catenaria.get("PASO_AFINADO", 0.005),
                                  marks={0: '0%', 0.01: '1%', 0.02: '2%'},
                                  tooltip={"placement": "bottom", "always_visible": True}, className="mb-4"),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("OBJ_CONDUCTOR:"),
                        dbc.Select(id="cat-OBJ_CONDUCTOR", options=[
                            {"label": "FlechaMin", "value": "FlechaMin"},
                            {"label": "TiroMin", "value": "TiroMin"}
                        ], value=datos_catenaria.get("OBJ_CONDUCTOR", "FlechaMin"), className="mb-3"),
                        
                        dbc.Label("OBJ_GUARDIA:"),
                        dbc.Select(id="cat-OBJ_GUARDIA", options=[
                            {"label": "FlechaMin", "value": "FlechaMin"},
                            {"label": "TiroMin", "value": "TiroMin"}
                        ], value=datos_catenaria.get("OBJ_GUARDIA", "TiroMin"), className="mb-3"),
                    ], md=6)
                ]),
                
                # Botones
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Guardar Ajustes", id="btn-guardar-ajustes-catenaria", color="primary", size="lg", className="w-100 mt-4")
                    ], md=6),
                    dbc.Col([
                        dbc.Button("Volver", id={"type": "btn-volver", "index": "catenaria"}, color="secondary", size="lg", className="w-100 mt-4")
                    ], md=6)
                ])
            ])
        ])
    ])
