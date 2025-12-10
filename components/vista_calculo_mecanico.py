"""
Vista para Cálculo Mecánico de Conductores
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import base64
from pathlib import Path
from config.app_config import DATA_DIR


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
                    dbc.Col([
                        dbc.Label("alpha (°) - Ángulo de quiebre"),
                        dcc.Slider(id="param-alpha", min=0, max=180, step=1, value=estructura_actual.get("alpha", 0),
                                  marks={0: '0°', 45: '45°', 90: '90°', 135: '135°', 180: '180°'},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=3),
                    dbc.Col([
                        dbc.Label("theta (°) - Ángulo viento oblicuo"),
                        dcc.Slider(id="param-theta", min=0, max=180, step=1, value=estructura_actual.get("theta", 45),
                                  marks={0: '0°', 45: '45°', 90: '90°', 135: '135°', 180: '180°'},
                                  tooltip={"placement": "bottom", "always_visible": True})
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
                        dcc.Slider(id="param-t_hielo", min=0, max=0.03, step=0.001, value=estructura_actual.get("t_hielo", 0.01),
                                  marks={0: '0', 0.01: '0.01', 0.02: '0.02', 0.03: '0.03'},
                                  tooltip={"placement": "bottom", "always_visible": True})
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
                        dbc.Label("SALTO_PORCENTUAL - Para búsqueda de soluciones en cálculo mecánico"),
                        dcc.Slider(id="param-SALTO_PORCENTUAL", min=0, max=0.1, step=0.01, 
                                  value=estructura_actual.get("SALTO_PORCENTUAL", 0.05),
                                  marks={0: '0%', 0.05: '5%', 0.1: '10%'},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=6),
                    dbc.Col([
                        dbc.Label("PASO_AFINADO - Refinamiento de búsqueda"),
                        dcc.Slider(id="param-PASO_AFINADO", min=0, max=0.02, step=0.001,
                                  value=estructura_actual.get("PASO_AFINADO", 0.005),
                                  marks={0: '0%', 0.01: '1%', 0.02: '2%'},
                                  tooltip={"placement": "bottom", "always_visible": True})
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
                        dcc.Slider(id="param-RELFLECHA_MAX_GUARDIA", min=0.5, max=1.1, step=0.01,
                                  value=estructura_actual.get("RELFLECHA_MAX_GUARDIA", 0.95),
                                  marks={0.5: '50%', 0.75: '75%', 1.0: '100%', 1.1: '110%'},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=12),
                ])
            ])
        ], className="mb-3"),
        
        # Estados Climáticos
        dbc.Card([
            dbc.CardHeader(html.H5("Estados Climáticos")),
            dbc.CardBody([
                html.Div(id="tabla-estados-climaticos")
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
        import pandas as pd
        
        # Convertir resultados a DataFrames
        resultados_conductor = calculo_guardado.get('resultados_conductor', {})
        resultados_guardia = calculo_guardado.get('resultados_guardia', {})
        
        # Crear DataFrames
        df_conductor = pd.DataFrame(resultados_conductor).T
        df_guardia = pd.DataFrame(resultados_guardia).T
        
        resultados_html = [
            dbc.Alert("Resultados cargados desde cálculo anterior", color="info", className="mb-3"),
            html.H4("Resultados del Cálculo Mecánico", className="mt-4 mb-3"),
            
            html.H5("Conductor"),
            dbc.Table.from_dataframe(df_conductor, striped=True, bordered=True, hover=True, size="sm"),
            
            html.H5("Cable de Guardia", className="mt-4"),
            dbc.Table.from_dataframe(df_guardia, striped=True, bordered=True, hover=True, size="sm"),
        ]
        
        # Cargar tabla de cargas si existe
        if calculo_guardado.get('df_cargas_totales'):
            df_cargas = pd.DataFrame(calculo_guardado['df_cargas_totales'])
            resultados_html.extend([
                html.H5("Lista Total de Cargas", className="mt-4"),
                dbc.Table.from_dataframe(df_cargas, striped=True, bordered=True, hover=True, size="sm"),
            ])
        
        # Cargar imágenes si existen y hash coincide
        hash_params = calculo_guardado.get('hash_parametros')
        if hash_params:
            resultados_html.append(html.H5("Gráficos de Flechas", className="mt-4"))
            
            img_combinado = DATA_DIR / f"CMC_Combinado.{hash_params}.png"
            if img_combinado.exists():
                with open(img_combinado, 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                resultados_html.extend([
                    html.H6("Conductor y Guardia", className="mt-3"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%'})
                ])
            
            img_conductor = DATA_DIR / f"CMC_Conductor.{hash_params}.png"
            if img_conductor.exists():
                with open(img_conductor, 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                resultados_html.extend([
                    html.H6("Solo Conductor", className="mt-3"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%'})
                ])
            
            img_guardia = DATA_DIR / f"CMC_Guardia.{hash_params}.png"
            if img_guardia.exists():
                with open(img_guardia, 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                resultados_html.extend([
                    html.H6("Solo Cable de Guardia", className="mt-3"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%'})
                ])
        
        return html.Div(resultados_html)
    except Exception as e:
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
