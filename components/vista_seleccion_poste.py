"""Vista de Selección de Poste de Hormigón"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.view_helpers import ViewHelpers
from utils.calculo_cache import CalculoCache

def crear_vista_seleccion_poste(estructura_actual, calculo_guardado=None):
    """Crear vista de selección de postes de hormigón"""
    
    if not estructura_actual:
        return html.Div([
            dbc.Alert("No hay estructura cargada. Por favor, cargue o cree una estructura primero.", color="warning")
        ])
    
    # Parámetros de configuración de selección de postes
    params_sph = {
        'FORZAR_N_POSTES': estructura_actual.get('FORZAR_N_POSTES', 0),
        'FORZAR_ORIENTACION': estructura_actual.get('FORZAR_ORIENTACION', 'No'),
        'PRIORIDAD_DIMENSIONADO': estructura_actual.get('PRIORIDAD_DIMENSIONADO', 'altura_libre'),
        'ANCHO_CRUCETA': estructura_actual.get('ANCHO_CRUCETA', 0.3)
    }
    
    return html.Div([
        dcc.Store(id="store-calculo-sph", data=calculo_guardado),
        dbc.Row([
            dbc.Col([
                html.H2("Selección Poste Hormigón (AEA-95301-2007)", className="mb-4"),
                dbc.Button("← Volver", id={"type": "btn-volver", "index": "sph"}, color="secondary", className="mb-3"),
            ])
        ]),
        
        # Parámetros ajustables
        dbc.Card([
            dbc.CardHeader(html.H4("Parámetros de Configuración")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Forzar N° Postes"),
                        dcc.Slider(
                            id="slider-forzar-n-postes",
                            min=0, max=3, step=1,
                            value=params_sph['FORZAR_N_POSTES'],
                            marks={0: 'Auto', 1: '1', 2: '2', 3: '3'},
                            tooltip={"placement": "bottom", "always_visible": False}
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Forzar Orientación"),
                        dbc.Select(
                            id="select-forzar-orientacion",
                            options=[
                                {"label": "No forzar", "value": "No"},
                                {"label": "Longitudinal", "value": "Longitudinal"},
                                {"label": "Transversal", "value": "Transversal"}
                            ],
                            value=params_sph['FORZAR_ORIENTACION']
                        )
                    ], md=6)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Prioridad Dimensionado"),
                        dbc.Select(
                            id="select-prioridad-dimensionado",
                            options=[
                                {"label": "Altura Libre", "value": "altura_libre"},
                                {"label": "Longitud Total", "value": "longitud_total"}
                            ],
                            value=params_sph['PRIORIDAD_DIMENSIONADO']
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Ancho Cruceta (m)"),
                        dbc.Input(
                            id="input-ancho-cruceta",
                            type="number",
                            value=params_sph['ANCHO_CRUCETA'],
                            step=0.1,
                            min=0.1
                        )
                    ], md=6)
                ])
            ])
        ], className="mb-4"),
        
        # Botones de acción
        dbc.Row([
            dbc.Col([
                dbc.Button("Guardar Parámetros", id="btn-guardar-params-sph", color="primary", className="me-2"),
                dbc.Button("Calcular", id="btn-calcular-sph", color="success")
            ])
        ], className="mb-4"),
        
        # Área de resultados
        html.Div(id="resultados-sph", children=_crear_area_resultados(calculo_guardado, estructura_actual) if calculo_guardado else [])
    ])

def _crear_area_resultados(calculo_guardado, estructura_actual=None):
    """Crear área de resultados del cálculo"""
    
    if not calculo_guardado:
        return []
    
    resultados = calculo_guardado.get('resultados', {})
    config_seleccionada = resultados.get('config_seleccionada', 'N/A')
    dimensiones = resultados.get('dimensiones', {})
    Rc_adopt = resultados.get('Rc_adopt', 0)
    
    # Determinar número de postes
    n_postes = 1 if "Monoposte" in config_seleccionada else 2 if "Biposte" in config_seleccionada else 3
    
    # Limpiar emojis del texto
    desarrollo_texto = ViewHelpers.limpiar_emojis(calculo_guardado.get('desarrollo_texto', 'No disponible'))
    
    output = [
        dbc.Card([
            dbc.CardHeader(html.H4("Resultados del Cálculo")),
            dbc.CardBody([
                dbc.Alert([
                    html.H5("Calculo completado", className="alert-heading"),
                    html.Hr(),
                    html.P([
                        html.Strong("Configuración: "), f"{config_seleccionada}", html.Br(),
                        html.Strong("Código: "), f"{n_postes} x {dimensiones.get('Ht_comercial', 0):.1f}m / Ro {Rc_adopt:.0f}daN", html.Br(),
                        html.Strong("Altura libre: "), f"{dimensiones.get('Hl', 0):.2f} m", html.Br(),
                        html.Strong("Empotramiento: "), f"{dimensiones.get('He_final', 0):.2f} m", html.Br(),
                        html.Strong("Resistencia en cima: "), f"{Rc_adopt:.0f} daN"
                    ])
                ], color="success"),
                html.Hr()
            ] + ViewHelpers.crear_pre_output(desarrollo_texto, "Desarrollo Completo"))
        ], className="mt-4")
    ]
    
    return output
