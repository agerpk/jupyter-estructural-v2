"""
Vista para análisis de Vano Económico
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from models.app_state import AppState

def crear_vista_vano_economico():
    """Crear vista principal de Vano Económico"""
    
    # Cargar familia activa
    state = AppState()
    nombre_familia_activa = state.get_familia_activa()
    
    # Cargar ajustes guardados
    ajustes = state.get_vano_economico_ajustes() or {}
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Vano Económico", className="mb-0")),
            dbc.CardBody([
                # Familia activa
                crear_seccion_familia_activa(nombre_familia_activa),
                
                html.Hr(),
                
                # Controles de vano
                crear_controles_vano(ajustes),
                
                html.Hr(),
                
                # Controles de cantidades
                crear_controles_cantidades(ajustes),
                
                html.Hr(),
                
                # Botones de acción
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Confirmar Ajustes", 
                                  id="vano-economico-btn-confirmar", 
                                  color="success",
                                  size="lg",
                                  className="w-100")
                    ], width=4),
                    dbc.Col([
                        dbc.Button("Calcular Vano Económico", 
                                  id="vano-economico-btn-calcular", 
                                  color="primary",
                                  size="lg",
                                  className="w-100")
                    ], width=4),
                    dbc.Col([
                        dbc.Button("Cargar Cache", 
                                  id="vano-economico-btn-cargar-cache", 
                                  color="dark",
                                  size="lg",
                                  className="w-100")
                    ], width=4)
                ], className="mb-3"),
                
                # Barra de progreso
                html.Div([
                    html.Label("Progreso:", className="fw-bold"),
                    dbc.Progress(id="vano-economico-progress", 
                                value=0, 
                                striped=True,
                                animated=True,
                                className="mb-3")
                ], id="vano-economico-progress-container", style={"display": "none"}),
                
                # Área de resultados
                html.Div(id="vano-economico-resultados")
            ])
        ])
    ])

def crear_seccion_familia_activa(nombre_familia):
    """Sección para mostrar/cargar familia"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Familia Activa:", className="fw-bold"),
                    html.H5(nombre_familia or "Ninguna", 
                           id="vano-economico-familia-actual",
                           className="text-primary")
                ], width=6),
                dbc.Col([
                    html.Label("Cargar otra familia:", className="fw-bold"),
                    dbc.Select(id="vano-economico-select-familia",
                              placeholder="Seleccione familia...")
                ], width=6)
            ])
        ])
    ], className="mb-3")

def crear_controles_vano(ajustes):
    """Controles para configurar rango de vanos"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Configuración de Vanos")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Vano Mínimo [m]:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-min", 
                             type="number", 
                             value=ajustes.get("vano_min", 300), 
                             step=10,
                             min=50)
                ], width=4),
                dbc.Col([
                    html.Label("Vano Máximo [m]:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-max", 
                             type="number", 
                             value=ajustes.get("vano_max", 500), 
                             step=10,
                             min=50)
                ], width=4),
                dbc.Col([
                    html.Label("Salto [m]:", className="fw-bold"),
                    dbc.Input(
                        id="vano-economico-salto",
                        type="number",
                        value=ajustes.get("salto", 50)
                    )
                ], width=4)
            ])
        ])
    ])

def crear_controles_cantidades(ajustes):
    """Controles para cálculo dinámico de cantidades"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Configuración de Cantidades")),
        dbc.CardBody([
            # LONGTRAZA
            dbc.Row([
                dbc.Col([
                    html.Label("Longitud de Traza [m]:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-longtraza", 
                             type="number", value=ajustes.get("longtraza", 10000), step=100, min=100)
                ], width=12)
            ], className="mb-3"),
            
            # Criterio RR
            dbc.Row([
                dbc.Col([
                    html.Label("Criterio para Retenciones:", className="fw-bold"),
                    dbc.Select(id="vano-economico-select-criterio-rr",
                              options=[
                                  {"label": "Por Distancia", "value": "Distancia"},
                                  {"label": "Por Suspensiones", "value": "Suspensiones"},
                                  {"label": "Manual", "value": "Manual"}
                              ],
                              value=ajustes.get("criterio_rr", "Distancia"))
                ], width=6),
                dbc.Col([
                    html.Label("RR cada X metros:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-rr-cada-x-m", 
                             type="number", value=ajustes.get("rr_cada_x_m", 2000), step=100, min=100)
                ], width=3),
                dbc.Col([
                    html.Label("RR cada X suspensiones:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-rr-cada-x-s", 
                             type="number", value=ajustes.get("rr_cada_x_s", 5), step=1, min=1)
                ], width=3)
            ], className="mb-3"),
            
            # Manual
            dbc.Row([
                dbc.Col([
                    html.Label("Cantidad RR Manual:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-cant-rr-manual", 
                             type="number", value=ajustes.get("cant_rr_manual", 4), step=1, min=0,
                             disabled=True)
                ], width=6)
            ], id="vano-economico-row-manual"),
            
            html.Hr(),
            
            # Display calculado
            html.H6("Cantidades Calculadas (ejemplo con vano medio):", className="text-muted"),
            html.Div(id="vano-economico-display-cantidades")
        ])
    ])
