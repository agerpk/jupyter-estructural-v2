"""
Vista para Cálculo Mecánico de Conductores
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from config.app_config import DATA_DIR
from utils.view_helpers import ViewHelpers
from utils.calculo_cache import CalculoCache
from config.parametros_controles import obtener_config_control


def crear_vista_calculo_mecanico(estructura_actual, calculo_guardado=None):
    """Crear vista de cálculo mecánico de cables"""
    
    # Generar resultados si hay cálculo guardado
    resultados_previos = None
    if calculo_guardado:
        resultados_previos = generar_resultados_cmc(calculo_guardado, estructura_actual)
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("Cálculo Mecánico de Cables", className="mb-4"),
                dbc.Button("← Volver", id={"type": "btn-volver", "index": "calculo-mecanico"}, 
                          color="secondary", size="sm", className="mb-3"),
            ])
        ]),
        
        # Parámetros de Diseño de Línea
        dbc.Card([
            dbc.CardHeader(html.H5("Parámetros de Diseño de Línea")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("L_vano (m)"),
                        dbc.Input(id="param-L_vano", type="number", value=estructura_actual.get("L_vano", 400))
                    ], md=3),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("alpha (°) - Ángulo de quiebre"),
                        dcc.Slider(**{k: v for k, v in obtener_config_control("alpha").items() if k != "tipo"}, id="slider-alpha", value=estructura_actual.get("alpha", 0))
                    ], md=3),
                    dbc.Col([
                        dbc.Label("theta (°) - Ángulo viento oblicuo"),
                        dcc.Slider(**{k: v for k, v in obtener_config_control("theta").items() if k != "tipo"}, id="slider-theta", value=estructura_actual.get("theta", 45))
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Vmax (m/s)"),
                        dbc.Input(id="param-Vmax", type="number", value=estructura_actual.get("Vmax", 38.9))
                    ], md=3),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Vmed (m/s)"),
                        dbc.Input(id="param-Vmed", type="number", value=estructura_actual.get("Vmed", 15.56))
                    ], md=4),
                    dbc.Col([
                        dbc.Label("t_hielo (m) - Espesor manguito de hielo"),
                        dcc.Slider(**{k: v for k, v in obtener_config_control("t_hielo").items() if k != "tipo"}, id="slider-t_hielo", value=estructura_actual.get("t_hielo", 0.01))
                    ], md=8),
                ])
            ])
        ], className="mb-3"),
        
        # Configuración de Flechado
        dbc.Card([
            dbc.CardHeader(html.H5("Configuración de Flechado / Cálculo Mecánico")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("VANO_DESNIVELADO"),
                        html.Small("Si es True, se calcula el vano peso según desnivel de catenarias", className="text-muted d-block mb-2"),
                        dbc.Checklist(id="param-VANO_DESNIVELADO",
                                     options=[{"label": "Activado", "value": True}],
                                     value=[True] if estructura_actual.get("VANO_DESNIVELADO", False) else [],
                                     switch=True)
                    ], md=12),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("H_PIQANTERIOR (m)"),
                        html.Small("Altura piquete anterior", className="text-muted d-block mb-2"),
                        dbc.Row([
                            dbc.Col(dcc.Slider(id="slider-H_PIQANTERIOR", min=-15, max=15, step=0.05,
                                              value=estructura_actual.get("H_PIQANTERIOR", 0.0),
                                              marks={i*5: str(i*5) for i in range(-3, 4)},
                                              tooltip={"placement": "bottom", "always_visible": True}), width=8),
                            dbc.Col(dbc.Input(id="param-H_PIQANTERIOR", type="number", step=0.05,
                                             value=estructura_actual.get("H_PIQANTERIOR", 0.0), size="sm"), width=4)
                        ])
                    ], md=6),
                    dbc.Col([
                        dbc.Label("H_PIQPOSTERIOR (m)"),
                        html.Small("Altura piquete posterior - Visto en gráfico", className="text-muted d-block mb-2"),
                        dbc.Row([
                            dbc.Col(dcc.Slider(id="slider-H_PIQPOSTERIOR", min=-15, max=15, step=0.05,
                                              value=estructura_actual.get("H_PIQPOSTERIOR", 0.0),
                                              marks={i*5: str(i*5) for i in range(-3, 4)},
                                              tooltip={"placement": "bottom", "always_visible": True}), width=8),
                            dbc.Col(dbc.Input(id="param-H_PIQPOSTERIOR", type="number", step=0.05,
                                             value=estructura_actual.get("H_PIQPOSTERIOR", 0.0), size="sm"), width=4)
                        ])
                    ], md=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("SALTO_PORCENTUAL - Para búsqueda de soluciones en cálculo mecánico"),
                        dcc.Slider(**{k: v for k, v in obtener_config_control("SALTO_PORCENTUAL").items() if k != "tipo"}, id="slider-SALTO_PORCENTUAL", value=estructura_actual.get("SALTO_PORCENTUAL", 0.05))
                    ], md=6),
                    dbc.Col([
                        dbc.Label("PASO_AFINADO - Refinamiento de búsqueda"),
                        dcc.Slider(**{k: v for k, v in obtener_config_control("PASO_AFINADO").items() if k != "tipo"}, id="slider-PASO_AFINADO", value=estructura_actual.get("PASO_AFINADO", 0.005))
                    ], md=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("OBJ_CONDUCTOR - Objetivo de Optimización"),
                        html.Small("FlechaMin minimiza flecha hasta máxima tensión. TiroMin minimiza tiro hasta máxima flecha.", className="text-muted d-block mb-2"),
                        dbc.Select(id="param-OBJ_CONDUCTOR", 
                                  options=[{"label": "FlechaMin", "value": "FlechaMin"}, 
                                          {"label": "TiroMin", "value": "TiroMin"}],
                                  value=estructura_actual.get("OBJ_CONDUCTOR", "FlechaMin"))
                    ], md=4),
                    dbc.Col([
                        dbc.Label("OBJ_GUARDIA - Objetivo de Optimización"),
                        html.Small("FlechaMin minimiza flecha hasta máxima tensión. TiroMin minimiza tiro hasta máxima relación de flecha.", className="text-muted d-block mb-2"),
                        dbc.Select(id="param-OBJ_GUARDIA",
                                  options=[{"label": "FlechaMin", "value": "FlechaMin"},
                                          {"label": "TiroMin", "value": "TiroMin"}],
                                  value=estructura_actual.get("OBJ_GUARDIA", "TiroMin"))
                    ], md=4),
                    dbc.Col([
                        dbc.Label("RELFLECHA_SIN_VIENTO"),
                        dbc.Checklist(id="param-RELFLECHA_SIN_VIENTO",
                                     options=[{"label": "Activado", "value": True}],
                                     value=[True] if estructura_actual.get("RELFLECHA_SIN_VIENTO", True) else [],
                                     switch=True)
                    ], md=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("RELFLECHA_MAX_GUARDIA - Relación de flecha máxima para cable de guardia"),
                        dcc.Slider(**{k: v for k, v in obtener_config_control("RELFLECHA_MAX_GUARDIA").items() if k != "tipo"}, id="slider-RELFLECHA_MAX_GUARDIA", value=estructura_actual.get("RELFLECHA_MAX_GUARDIA", 0.95))
                    ], md=12),
                ])
            ])
        ], className="mb-3"),
        
        # Estados Climáticos
        dbc.Card([
            dbc.CardHeader(html.H5("Estados Climáticos")),
            dbc.CardBody([
                html.Div(crear_tabla_estados_climaticos(estructura_actual))
            ])
        ], className="mb-3"),
        
        # Botones de acción
        dbc.Row([
            dbc.Col([
                dbc.Button("Guardar Parámetros", id="btn-guardar-params-cmc", color="primary", className="me-2"),
                dbc.Button("Calcular", id="btn-calcular-cmc", color="success", size="lg"),
            ])
        ], className="mb-3"),
        
        # Área de resultados
        html.Div(id="resultados-cmc", children=resultados_previos, className="mt-4")
    ])


def generar_resultados_cmc(calculo_guardado, estructura_actual):
    """Generar HTML de resultados desde cálculo guardado"""
    try:
        from utils.format_helpers import formatear_resultados_cmc, formatear_dataframe_cmc
        
        # Verificar vigencia
        vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        
        resultados_html = [
            ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=vigente),
            html.H4("Resultados del Cálculo Mecánico", className="mt-4 mb-3"),
        ]
        
        # Conductor - guardar y cargar DataFrames completos
        if calculo_guardado.get('df_conductor_html'):
            df_conductor = pd.read_json(calculo_guardado['df_conductor_html'], orient='split').round(2)
            resultados_html.extend([
                html.H5("Conductor"),
                dbc.Table.from_dataframe(
                    df_conductor,
                    striped=True, bordered=True, hover=True, size="sm"
                )
            ])
        
        # Guardia 1 - guardar y cargar DataFrames completos
        if calculo_guardado.get('df_guardia1_html'):
            df_guardia1 = pd.read_json(calculo_guardado['df_guardia1_html'], orient='split').round(2)
            resultados_html.extend([
                html.H5("Cable de Guardia 1", className="mt-4"),
                dbc.Table.from_dataframe(
                    df_guardia1,
                    striped=True, bordered=True, hover=True, size="sm"
                )
            ])
        
        # Guardia 2 - guardar y cargar DataFrames completos
        if calculo_guardado.get('df_guardia2_html'):
            df_guardia2 = pd.read_json(calculo_guardado['df_guardia2_html'], orient='split').round(2)
            resultados_html.extend([
                html.H5("Cable de Guardia 2", className="mt-4"),
                dbc.Table.from_dataframe(
                    df_guardia2,
                    striped=True, bordered=True, hover=True, size="sm"
                )
            ])
        
        # Cargar tabla de cargas si existe
        if calculo_guardado.get('df_cargas_totales'):
            df_cargas = pd.DataFrame(calculo_guardado['df_cargas_totales'])
            resultados_html.extend(
                ViewHelpers.crear_tabla_desde_dataframe(df_cargas, "Lista Total de Cargas", responsive=True)
            )
        
        # Output de consola
        if calculo_guardado.get('console_output'):
            resultados_html.append(html.Hr(className="mt-4"))
            resultados_html.extend(
                ViewHelpers.crear_pre_output(
                    calculo_guardado['console_output'],
                    titulo="Output de Cálculo",
                    font_size='0.75rem'
                )
            )
        
        # Cargar gráficos interactivos (replicar formato original)
        hash_params = calculo_guardado.get('hash_parametros')
        if hash_params:
            resultados_html.append(html.H5("Gráficos de Flechas", className="mt-4"))
            
            # Cargar JSON y crear dcc.Graph igual que cuando se genera
            fig_combinado_dict = ViewHelpers.cargar_figura_plotly_json(f"CMC_Combinado.{hash_params}.json")
            if fig_combinado_dict:
                resultados_html.extend([
                    html.H6("Conductor y Guardia", className="mt-3"),
                    dcc.Graph(figure=fig_combinado_dict, config={'displayModeBar': True})
                ])
            
            fig_conductor_dict = ViewHelpers.cargar_figura_plotly_json(f"CMC_Conductor.{hash_params}.json")
            if fig_conductor_dict:
                resultados_html.extend([
                    html.H6("Solo Conductor", className="mt-3"),
                    dcc.Graph(figure=fig_conductor_dict, config={'displayModeBar': True})
                ])
            
            fig_guardia_dict = ViewHelpers.cargar_figura_plotly_json(f"CMC_Guardia.{hash_params}.json")
            if fig_guardia_dict:
                resultados_html.extend([
                    html.H6("Solo Cable de Guardia 1", className="mt-3"),
                    dcc.Graph(figure=fig_guardia_dict, config={'displayModeBar': True})
                ])
            
            fig_guardia2_dict = ViewHelpers.cargar_figura_plotly_json(f"CMC_Guardia2.{hash_params}.json")
            if fig_guardia2_dict:
                resultados_html.extend([
                    html.H6("Solo Cable de Guardia 2", className="mt-3"),
                    dcc.Graph(figure=fig_guardia2_dict, config={'displayModeBar': True})
                ])
        
        return html.Div(resultados_html)
    except Exception as e:
        import traceback
        print(f"Error en generar_resultados_cmc: {traceback.format_exc()}")
        return dbc.Alert(f"Error cargando resultados: {str(e)}", color="warning")


def crear_tabla_estados_climaticos(estructura_actual):
    """Crear tabla editable de estados climáticos con restricciones"""
    
    # Valores por defecto
    estados_default = {
        "I": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "espesor_hielo": 0},
        "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "espesor_hielo": 0},
        "III": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": estructura_actual.get("Vmax", 38.9), "espesor_hielo": 0},
        "IV": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": estructura_actual.get("Vmed", 15.56), "espesor_hielo": estructura_actual.get("t_hielo", 0.01)},
        "V": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "espesor_hielo": 0}
    }
    
    # Restricciones por defecto
    restricciones_conductor = {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25}
    restricciones_guardia = {"I": 0.7, "II": 0.70, "III": 0.70, "IV": 0.7, "V": 0.7}
    
    # Encabezado
    header = dbc.Row([
        dbc.Col(html.Strong("Estado"), md=1),
        dbc.Col(html.Strong("Temp (°C)"), md=1),
        dbc.Col(html.Strong("Descripción"), md=2),
        dbc.Col(html.Strong("Viento (m/s)"), md=2),
        dbc.Col(html.Strong("Hielo (m)"), md=2),
        dbc.Col(html.Strong("Restricción Conductor (%)"), md=2),
        dbc.Col(html.Strong("Restricción Guardia (%)"), md=2),
    ], className="mb-2 fw-bold")
    
    filas = [header]
    for estado_id, valores in estados_default.items():
        fila = dbc.Row([
            dbc.Col(html.Strong(estado_id), md=1),
            dbc.Col(
                dbc.Input(id={"type": "estado-temp", "index": estado_id}, type="number", 
                         value=valores["temperatura"], size="sm"), md=1
            ),
            dbc.Col(
                dbc.Input(id={"type": "estado-desc", "index": estado_id}, type="text",
                         value=valores["descripcion"], size="sm", disabled=True), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "estado-viento", "index": estado_id}, type="number",
                         value=valores["viento_velocidad"], size="sm"), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "estado-hielo", "index": estado_id}, type="number",
                         value=valores["espesor_hielo"], size="sm"), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "restriccion-conductor", "index": estado_id}, type="number",
                         value=restricciones_conductor[estado_id], size="sm", step=0.01, min=0, max=1), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "restriccion-guardia", "index": estado_id}, type="number",
                         value=restricciones_guardia[estado_id], size="sm", step=0.01, min=0, max=1), md=2
            ),
        ], className="mb-2")
        filas.append(fila)
    
    return html.Div(filas)
