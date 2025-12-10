"""Vista para Calcular Todo - Ejecución secuencial de todos los cálculos"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def crear_vista_calcular_todo(estructura_actual, calculo_guardado=None):
    """Vista para ejecutar todos los cálculos en secuencia"""
    
    # Si hay cálculo guardado, mostrar resultados
    output_inicial = []
    btn_disabled = True
    if calculo_guardado and calculo_guardado.get('resultados'):
        output_inicial = [dbc.Alert("✅ Resultados cargados desde cache", color="info", className="mb-3")]
        btn_disabled = False
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Calcular Todo - Ejecución Completa", className="mb-0")),
            dbc.CardBody([
                dbc.Alert([
                    html.H5("Secuencia de Cálculo:", className="alert-heading"),
                    html.P("Esta vista ejecutará automáticamente todos los cálculos en el siguiente orden:"),
                    html.Ol([
                        html.Li("Cálculo Mecánico de Cables (CMC)"),
                        html.Li("Diseño Geométrico de Estructura (DGE)"),
                        html.Li("Diseño Mecánico de Estructura (DME)"),
                        html.Li("Árboles de Carga"),
                        html.Li("Selección de Poste de Hormigón (SPH)")
                    ]),
                    html.P("Los resultados se mostrarán en orden a continuación.", className="mb-0")
                ], color="info", className="mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Ejecutar Cálculo Completo",
                            id="btn-calcular-todo",
                            color="success",
                            size="lg",
                            className="w-100"
                        )
                    ], md=8),
                    dbc.Col([
                        dbc.Button(
                            "Descargar HTML",
                            id="btn-descargar-html-todo",
                            color="primary",
                            size="lg",
                            className="w-100",
                            disabled=btn_disabled
                        )
                    ], md=4)
                ], className="mb-4"),
                
                html.Hr(),
                
                # Área de resultados
                html.Div(output_inicial, id="output-calcular-todo")
            ])
        ]),
        
        # Store para guardar el HTML completo
        dcc.Store(id="html-completo-store"),
        dcc.Download(id="download-html-completo")
    ])
