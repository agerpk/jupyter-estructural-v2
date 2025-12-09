"""
Vista principal/home de la aplicación
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

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
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Acciones Rápidas", className="mb-0")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(
                                dbc.Button(
                                    html.Div([
                                        html.I(className="bi bi-plus-circle me-2"),
                                        "Nueva Estructura"
                                    ]),
                                    id="menu-nueva-estructura",
                                    color="primary",
                                    className="w-100 mb-2"
                                ),
                                width=12
                            ),
                            dbc.Col(
                                dbc.Button(
                                    html.Div([
                                        html.I(className="bi bi-upload me-2"),
                                        "Cargar Estructura"
                                    ]),
                                    id="menu-cargar-estructura",
                                    color="success",
                                    className="w-100 mb-2"
                                ),
                                width=12
                            ),
                            dbc.Col(
                                dbc.Button(
                                    html.Div([
                                        html.I(className="bi bi-gear me-2"),
                                        "Ajustar Parámetros"
                                    ]),
                                    id="menu-ajustar-parametros",
                                    color="warning",
                                    className="w-100 mb-2"
                                ),
                                width=12
                            ),
                            dbc.Col(
                                dbc.Button(
                                    html.Div([
                                        html.I(className="bi bi-calculator me-2"),
                                        "Calcular Estructura"
                                    ]),
                                    id="btn-calcular",
                                    color="info",
                                    className="w-100"
                                ),
                                width=12
                            )
                        ])
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardHeader(html.H4("Visualización de Estructura", className="mb-0")),
            dbc.CardBody([
                dcc.Graph(
                    id="grafico-estructura",
                    figure=crear_grafico_placeholder(),
                    style={'height': '500px'}
                ),
                dbc.Row([
                    dbc.Col(
                        dbc.ButtonGroup([
                            dbc.Button("Vista 3D", id="btn-vista-3d"),
                            dbc.Button("Vista Lateral", id="btn-vista-lateral"),
                            dbc.Button("Vista Superior", id="btn-vista-superior"),
                        ]),
                        width=6
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Exportar Gráfico",
                            id="btn-exportar-grafico",
                            color="secondary",
                            className="float-end"
                        ),
                        width=6
                    )
                ])
            ])
        ])
    ])

def crear_grafico_placeholder():
    """Crear gráfico de estructura placeholder"""
    fig = go.Figure()
    
    # Agregar texto de placeholder
    fig.add_annotation(
        text="Gráfico de estructura se generará después del cálculo",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=20)
    )
    
    fig.update_layout(
        title="Estructura (pendiente de cálculo)",
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white'
    )
    
    return fig