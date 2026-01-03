import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from utils.view_helpers import ViewHelpers

def crear_vista_fundacion(estructura_actual, calculo_guardado=None):
    """Crear vista para cálculo de fundaciones - inicia vacía como DGE"""
    
    # Generar resultados si hay cálculo guardado
    resultados_previos = []
    if calculo_guardado:
        resultados_previos = generar_resultados_fundacion(calculo_guardado, estructura_actual)
        if not isinstance(resultados_previos, list):
            resultados_previos = [resultados_previos]
    
    # Formulario de parámetros
    formulario = dbc.Card([
        dbc.CardHeader(html.H5("Parámetros de Fundación")),
        dbc.CardBody([
            # Selector de método y forma
            html.H6("Configuración de Fundación", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Método"),
                    dcc.Dropdown(
                        id="dropdown-metodo-fundacion",
                        options=[
                            {"label": "Sulzberger", "value": "sulzberger"},
                            {"label": "Mohr-Pohl (Próximamente)", "value": "mohr_pohl", "disabled": True}
                        ],
                        value="sulzberger"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Forma"),
                    dcc.Dropdown(
                        id="dropdown-forma-fundacion",
                        options=[
                            {"label": "Monobloque", "value": "monobloque"},
                            {"label": "Escalonada Recta", "value": "escalonada_recta"},
                            {"label": "Escalonada Pirámide Truncada", "value": "escalonada_piramide"}
                        ],
                        value="monobloque"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Tipo de Base"),
                    dcc.Dropdown(
                        id="dropdown-tipo-base",
                        options=[
                            {"label": "Rómbica", "value": "Rombica"},
                            {"label": "Cuadrada", "value": "Cuadrada"}
                        ],
                        value="Rombica"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("N° Postes (desde SPH)"),
                    dbc.Input(id="input-n-postes", type="number", value=1, disabled=True)
                ], width=3)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Orientación (desde SPH)"),
                    dbc.Input(id="input-orientacion", type="text", value="longitudinal", disabled=True)
                ], width=3)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Datos de la tierra
            html.H6("Datos de la Tierra", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Índice Compresibilidad C [kg/m³]"),
                    dbc.Input(id="input-c", type="number", value=5000000, step=100000)
                ], width=3),
                dbc.Col([
                    dbc.Label("Presión Admisible σadm [kg/m²]"),
                    dbc.Input(id="input-sigma-adm", type="number", value=50000)
                ], width=3),
                dbc.Col([
                    dbc.Label("Ángulo Tierra Gravante β [°]"),
                    dbc.Input(id="input-beta", type="number", value=8.0, step=0.1)
                ], width=3),
                dbc.Col([
                    dbc.Label("Coef. Fricción tierra-hormigón μ"),
                    dbc.Input(id="input-mu", type="number", value=0.40, step=0.01)
                ], width=3)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Requerimientos
            html.H6("Requerimientos", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Coef. Seguridad Volcamiento (F.S)"),
                    dbc.Input(id="input-fs", type="number", value=1.5, step=0.1)
                ], width=3),
                dbc.Col([
                    dbc.Label("Inclinación por Desplazamiento (tg α adm)"),
                    dbc.Input(id="input-tg-alfa-adm", type="number", value=0.01, step=0.001)
                ], width=3),
                dbc.Col([
                    dbc.Label("Relación Máx. Sin Armadura (t/he)"),
                    dbc.Input(id="input-t-he-max", type="number", value=1.25, step=0.05)
                ], width=3),
                dbc.Col([
                    dbc.Label("Superación Presión Adm. (σmax/σadm)"),
                    dbc.Input(id="input-sigma-max-adm", type="number", value=1.33, step=0.01)
                ], width=3)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Incremento Iteraciones [m]"),
                    dbc.Input(id="input-incremento-calc", type="number", value=0.01, step=0.001)
                ], width=3)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Constantes
            html.H6("Constantes", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Densidad Hormigón [kg/m³]"),
                    dbc.Input(id="input-gamma-hor", type="number", value=2200)
                ], width=3),
                dbc.Col([
                    dbc.Label("Densidad Tierra [kg/m³]"),
                    dbc.Input(id="input-gamma-tierra", type="number", value=3800)
                ], width=3),
                dbc.Col([
                    dbc.Label("Coef. Aumento Cb/Ct"),
                    dbc.Input(id="input-cacb", type="number", value=1.20, step=0.01)
                ], width=3)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Dimensionamiento inicial
            html.H6("Dimensionamiento Inicial", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Profundidad propuesta (tin) [m]"),
                    dbc.Input(id="input-t", type="number", value=1.7, step=0.1)
                ], width=4),
                dbc.Col([
                    dbc.Label("Longitud colineal inferior (ain) [m]"),
                    dbc.Input(id="input-a", type="number", value=1.3, step=0.1)
                ], width=4),
                dbc.Col([
                    dbc.Label("Longitud transversal inferior (bin) [m]"),
                    dbc.Input(id="input-b", type="number", value=1.3, step=0.1)
                ], width=4)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Datos del poste (configurables)
            html.H6("Datos del Poste (Configurables)", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Distancia molde hueco lateral (dml) [m]"),
                    dbc.Input(id="input-dml", type="number", value=0.15, step=0.01)
                ], width=3),
                dbc.Col([
                    dbc.Label("Distancia molde hueco fondo (dmf) [m]"),
                    dbc.Input(id="input-dmf", type="number", value=0.20, step=0.01)
                ], width=3),
                dbc.Col([
                    dbc.Label("Diámetro del molde (dmol) [m]"),
                    dbc.Input(id="input-dmol", type="number", value=0.60, step=0.01)
                ], width=3),
                dbc.Col([
                    dbc.Label("Separación postes en cima (spc) [m]"),
                    dbc.Input(id="input-spc", type="number", value=0.30, step=0.01)
                ], width=3)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Pendiente postes dobles/triples (pp) [%]"),
                    dbc.Input(id="input-pp", type="number", value=4.0, step=0.1)
                ], width=4),
                dbc.Col([
                    dbc.Label("Conicidad poste (con) [%]"),
                    dbc.Input(id="input-con", type="number", value=1.5, step=0.1)
                ], width=4)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Botones
            dbc.Row([
                dbc.Col([
                    dbc.Button("Calcular Fundación", id="btn-calcular-fundacion", 
                              color="primary", className="me-2"),
                    dbc.Button("Guardar Parámetros", id="btn-guardar-fundacion", 
                              color="success", className="me-2"),
                    dbc.Button("Cargar desde Cache", id="btn-cargar-cache-fundacion", 
                              color="secondary", outline=True)
                ], width=12)
            ])
        ])
    ], className="mb-3")
    
    # Área de resultados
    area_resultados = html.Div(id="resultados-fundacion", children=resultados_previos if resultados_previos else [])
    
    # Toast para notificaciones
    toast = dbc.Toast(
        id="toast-fundacion",
        header="Fundación",
        is_open=False,
        dismissable=True,
        duration=4000,
        style={"position": "fixed", "top": 66, "right": 10, "width": 350, "z-index": 9999}
    )
    
    return html.Div([
        html.H3("Cálculo de Fundaciones"),
        formulario,
        area_resultados,
        toast
    ])

def generar_resultados_fundacion(calculo_guardado, estructura_actual, omitir_vigencia=False):
    """Generar componentes de resultados desde cache - retorna lista de componentes"""
    print(f"🔍 DEBUG: Iniciando generar_resultados_fundacion")
    
    if not calculo_guardado:
        print(f"⚠️ DEBUG: calculo_guardado es None")
        return [dbc.Alert("No hay datos de cálculo disponibles", color="warning")]
    
    resultados = calculo_guardado.get('resultados', {})
    hash_params = calculo_guardado.get('hash_parametros', '')
    
    print(f"📋 DEBUG: Resultados keys: {list(resultados.keys())}")
    
    output = []
    
    # Verificar vigencia solo si no se omite
    if not omitir_vigencia:
        from utils.calculo_cache import CalculoCache
        vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        
        # Alerta de cache
        alerta = ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=vigente)
        if alerta:
            output.append(alerta)
    
    output.append(dbc.Alert("Resultados cargados desde cache", color="info", className="mb-3"))
    
    # Crear tabla de resultados
    if 'dataframe_html' in resultados:
        try:
            df = pd.read_json(resultados['dataframe_html'], orient='split')
            tabla = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, size="sm")
            output.append(html.H5("Resultados por Hipótesis"))
            output.append(tabla)
            print(f"📊 DEBUG: Tabla creada con {len(df)} filas")
        except Exception as e:
            print(f"❌ ERROR creando tabla: {e}")
            output.append(html.P("Error cargando tabla de resultados"))
    else:
        print(f"⚠️ DEBUG: No hay dataframe_html en resultados")
        output.append(html.P("No hay datos de tabla disponibles"))
    
    # Cargar gráfico 3D interactivo desde JSON
    if hash_params:
        try:
            fig_3d_json = ViewHelpers.cargar_figura_plotly_json(f"FUND_3D.{hash_params}.json")
            if fig_3d_json and isinstance(fig_3d_json, dict):
                output.append(html.Hr(className="mt-4"))
                output.append(html.H5("Visualización 3D de la Fundación"))
                grafico_3d = dcc.Graph(
                    figure=fig_3d_json,
                    config={'displayModeBar': True},
                    style={'height': '800px', 'width': '100%'}
                )
                output.append(grafico_3d)
                print(f"📊 DEBUG: Componente 3D creado desde cache")
        except Exception as e:
            print(f"❌ ERROR cargando gráfico 3D desde cache: {e}")
    
    # Si no hay gráfico en cache, intentar crear nuevo
    if not any(isinstance(comp, dcc.Graph) for comp in output):
        try:
            print(f"⚠️ DEBUG: No hay gráfico en cache, intentando crear nuevo...")
            from utils.grafico_sulzberger_monobloque import crear_componente_fundacion_3d
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            componente_3d = crear_componente_fundacion_3d(nombre_estructura)
            if componente_3d:
                output.append(html.Hr(className="mt-4"))
                output.append(html.H5("Visualización 3D de la Fundación"))
                output.append(componente_3d)
                print(f"📊 DEBUG: Componente 3D creado nuevo exitosamente")
        except Exception as e:
            print(f"❌ ERROR creando componente 3D nuevo: {e}")
    
    # Memoria de cálculo
    memoria_texto = resultados.get('memoria_calculo', 'No hay memoria de cálculo disponible')
    if memoria_texto and memoria_texto != 'No hay memoria de cálculo disponible':
        output.append(html.Hr(className="mt-4"))
        output.append(html.H5("Memoria de Cálculo"))
        output.append(html.Pre(
            memoria_texto,
            style={
                'backgroundColor': '#1e1e1e',
                'color': '#d4d4d4',
                'padding': '10px',
                'borderRadius': '5px',
                'fontSize': '0.75rem',
                'maxHeight': '300px',
                'overflowY': 'auto',
                'whiteSpace': 'pre-wrap',
                'fontFamily': 'monospace'
            }
        ))
        print(f"📋 DEBUG: Memoria de cálculo: {len(memoria_texto)} caracteres")
    
    print(f"🔍 DEBUG: Retornando lista con {len(output)} componentes")
    return output