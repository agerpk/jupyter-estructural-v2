import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from utils.view_helpers import ViewHelpers

def crear_vista_costeo(estructura_actual, calculo_guardado=None):
    """Crear vista para cálculo de costeo - inicia vacía como DGE"""
    
    # Generar resultados si hay cálculo guardado
    resultados_previos = []
    if calculo_guardado:
        resultados_previos = generar_resultados_costeo(calculo_guardado, estructura_actual)
        if not isinstance(resultados_previos, list):
            resultados_previos = [resultados_previos]
    
    # Obtener parámetros de costeo desde estructura o usar defaults
    params_costeo = estructura_actual.get('costeo', {}) if estructura_actual else {}
    
    # Valores por defecto actualizados para nueva fórmula (interpolados R²=0.989)
    default_coef_a = 127.384729  # por metro de longitud
    default_coef_b = 1.543826    # por daN de resistencia
    default_coef_c = -631.847156 # fijo
    
    # Formulario de parámetros
    formulario = dbc.Card([
        dbc.CardHeader(html.H5("Parámetros de Costeo")),
        dbc.CardBody([
            # Costos de Postes
            html.H6("Costos de Postes", className="text-primary"),
            dbc.Alert([
                html.Strong("Fórmula Postes: "),
                "Costo = A × Longitud_m + B × Resistencia_daN + C"
            ], color="info", className="mb-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Coeficiente A (por m longitud)"),
                    dbc.Input(id="input-coef-a", type="number", value=params_costeo.get('postes', {}).get('coef_a', 127.384729), step=1.0)
                ], width=3),
                dbc.Col([
                    dbc.Label("Coeficiente B (por daN resistencia)"),
                    dbc.Input(id="input-coef-b", type="number", value=params_costeo.get('postes', {}).get('coef_b', 1.543826), step=0.01)
                ], width=3),
                dbc.Col([
                    dbc.Label("Coeficiente C (fijo)"),
                    dbc.Input(id="input-coef-c", type="number", value=params_costeo.get('postes', {}).get('coef_c', -631.847156), step=10.0)
                ], width=3)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Costos de Accesorios
            html.H6("Costos de Accesorios", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Precio Crucetas [UM/u]"),
                    dbc.Input(id="input-precio-crucetas", type="number", value=params_costeo.get('accesorios', {}).get('crucetas', 580.0), step=50.0)
                ], width=3),
                dbc.Col([
                    dbc.Label("Precio Ménsulas [UM/u]"),
                    dbc.Input(id="input-precio-mensulas", type="number", value=params_costeo.get('accesorios', {}).get('mensulas', 320.0), step=25.0)
                ], width=3),
                dbc.Col([
                    dbc.Label("Precio Vínculos [UM/u]"),
                    dbc.Input(id="input-precio-vinculos", type="number", value=params_costeo.get('accesorios', {}).get('vinculos', 320.0), step=10.0)
                ], width=3)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Costos de Fundaciones
            html.H6("Costos de Fundaciones", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Precio Hormigón [UM/m³]"),
                    dbc.Input(id="input-precio-hormigon", type="number", value=params_costeo.get('fundaciones', {}).get('precio_m3_hormigon', 250.0), step=10.0)
                ], width=4),
                dbc.Col([
                    dbc.Label("Factor Hierro"),
                    dbc.Input(id="input-factor-hierro", type="number", value=params_costeo.get('fundaciones', {}).get('factor_hierro', 1.2), step=0.1)
                ], width=4)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Costos de Montaje
            html.H6("Costos de Montaje y Logística", className="text-primary"),
            dbc.Alert([
                html.Strong("Factor Terreno: "),
                "Multiplica el costo de montaje (Precio por Estructura) según dificultad de acceso y condiciones del terreno. ",
                "1.0=Normal, 1.2=Dificultades menores, 1.5=Difícil, 2.0=Muy difícil"
            ], color="info", className="mb-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Precio por Estructura [UM]"),
                    dbc.Input(id="input-precio-estructura", type="number", value=params_costeo.get('montaje', {}).get('precio_por_estructura', 5000.0), step=500.0)
                ], width=4),
                dbc.Col([
                    dbc.Label("Factor Terreno"),
                    dbc.Input(id="input-factor-terreno", type="number", value=params_costeo.get('montaje', {}).get('factor_terreno', 1.0), step=0.1)
                ], width=4),
                dbc.Col([
                    dbc.Label("Adicional Estructura [UM]"),
                    dbc.Input(id="input-adicional-estructura", type="number", value=params_costeo.get('adicional_estructura', 2000.0), step=500.0)
                ], width=4)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Botones
            dbc.Row([
                dbc.Col([
                    dbc.Button("Calcular Costeo", id="btn-calcular-costeo", 
                              color="primary", className="me-2"),
                    dbc.Button("Guardar Parámetros", id="btn-guardar-costeo", 
                              color="success", className="me-2"),
                    dbc.Button("Cargar desde Cache", id="btn-cargar-cache-costeo", 
                              color="secondary", outline=True)
                ], width=12)
            ])
        ])
    ], className="mb-3")
    
    # Área de resultados
    area_resultados = html.Div(id="resultados-costeo", children=resultados_previos if resultados_previos else [])
    
    return html.Div([
        html.H3("Cálculo de Costeo"),
        formulario,
        area_resultados
    ])

def generar_resultados_costeo(calculo_guardado, estructura_actual, mostrar_alerta_cache=False):
    """Generar componentes de resultados desde cache - retorna lista de componentes"""
    
    if not calculo_guardado:
        return [dbc.Alert("No hay datos de cálculo disponibles", color="warning")]
    
    resultados = calculo_guardado.get('resultados', {})
    
    output = []
    
    # Solo mostrar alerta de cache si se solicita explícitamente
    if mostrar_alerta_cache:
        from utils.calculo_cache import CalculoCache
        vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        alerta = ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=vigente)
        if alerta:
            output.append(alerta)
        output.append(dbc.Alert("Resultados cargados desde cache", color="info", className="mb-3"))
    
    # Tabla de costos detallada
    if 'tabla_costos' in resultados:
        try:
            from io import StringIO
            df = pd.read_json(StringIO(resultados['tabla_costos']), orient='split')
            tabla = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, size="sm")
            output.append(html.H5("Detalle de Costos"))
            output.append(tabla)
        except Exception as e:
            output.append(html.P("Error cargando tabla de costos"))
    
    # Resumen de costos
    if 'resumen_costos' in resultados:
        resumen = resultados['resumen_costos']
        output.append(html.Hr(className="mt-4"))
        output.append(html.H5("Resumen de Costos"))
        output.append(dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{resumen.get('costo_total', 0):,.0f} UM", className="text-primary"),
                        html.P("Costo Total", className="mb-0")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{resumen.get('costo_postes', 0):,.0f} UM"),
                        html.P("Postes", className="mb-0")
                    ])
                ])
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{resumen.get('costo_accesorios', 0):,.0f} UM"),
                        html.P("Accesorios", className="mb-0")
                    ])
                ])
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{resumen.get('costo_fundaciones', 0):,.0f} UM"),
                        html.P("Fundaciones", className="mb-0")
                    ])
                ])
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{resumen.get('costo_montaje', 0):,.0f} UM"),
                        html.P("Montaje", className="mb-0")
                    ])
                ])
            ], width=3)
        ]))
    
    return output