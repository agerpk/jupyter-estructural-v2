"""
Vista para comparar múltiples cables usando lógica CMC
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def crear_vista_comparar_cables(comparativa_actual=None):
    """Crear vista principal de comparativa de cables"""
    
    # Título actual o por defecto
    titulo_actual = comparativa_actual.get("titulo", "Nueva_Comparativa") if comparativa_actual else "Nueva_Comparativa"
    
    return html.Div([
        # Store para estado de la comparativa
        dcc.Store(id="store-comparativa-actual", data=comparativa_actual),
        
        # Download component
        dcc.Download(id="download-html-comparativa"),
        
        # Header con gestión de archivos
        _crear_header_gestion_archivos(titulo_actual),
        
        html.Hr(),
        
        # Sección de cables
        _crear_seccion_cables(comparativa_actual),
        
        html.Hr(),
        
        # Sección de parámetros
        _crear_seccion_parametros(comparativa_actual),
        
        html.Hr(),
        
        # Sección de resultados
        _crear_seccion_resultados(),
        
        # Modales
        _crear_modales()
    ])

def _crear_header_gestion_archivos(titulo_actual):
    """Crear header con gestión de archivos"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Título de la Comparativa:", className="fw-bold"),
                    dbc.Input(
                        id="input-titulo-comparativa",
                        value=titulo_actual,
                        type="text",
                        placeholder="Nombre de la comparativa..."
                    )
                ], width=4),
                dbc.Col([
                    html.Div([
                        dbc.Button("Nueva", id="btn-nueva-comparativa", color="success", size="sm", className="me-2"),
                        dbc.Button("Cargar", id="btn-cargar-comparativa", color="primary", size="sm", className="me-2"),
                        dbc.Button("Guardar", id="btn-guardar-comparativa", color="info", size="sm", className="me-2"),
                        dbc.Button("Guardar Como", id="btn-guardar-como-comparativa", color="secondary", size="sm"),
                        dbc.Button("Cargar Cache", id="btn-cargar-cache-comparativa", color="warning", size="sm", className="ms-2")
                    ], className="d-flex align-items-end h-100")
                ], width=8)
            ])
        ])
    ], className="mb-3")

def _crear_seccion_cables(comparativa_actual):
    """Crear sección de gestión de cables"""
    cables_seleccionados = comparativa_actual.get("cables_seleccionados", []) if comparativa_actual else []
    
    return dbc.Card([
        dbc.CardHeader(html.H5("Cables a Comparar", className="mb-0")),
        dbc.CardBody([
            # Lista de cables seleccionados
            html.Div(id="lista-cables-seleccionados", children=_crear_lista_cables(cables_seleccionados)),
            
            html.Hr(),
            
            # Agregar cable
            dbc.Row([
                dbc.Col([
                    dbc.Label("Agregar Cable:"),
                    dbc.Select(
                        id="select-cable-agregar",
                        placeholder="Seleccione un cable..."
                    )
                ], width=8),
                dbc.Col([
                    dbc.Button("Agregar", id="btn-agregar-cable", color="primary", className="mt-4")
                ], width=4)
            ])
        ])
    ], className="mb-3")

def _crear_lista_cables(cables_seleccionados):
    """Crear lista visual de cables seleccionados"""
    if not cables_seleccionados:
        return dbc.Alert("No hay cables seleccionados", color="info")
    
    cards = []
    for i, cable in enumerate(cables_seleccionados):
        card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6(cable, className="mb-0")
                    ], width=10),
                    dbc.Col([
                        dbc.Button("×", id={"type": "btn-eliminar-cable", "index": i}, 
                                 color="danger", size="sm", outline=True)
                    ], width=2)
                ])
            ])
        ], className="mb-2")
        cards.append(card)
    
    return html.Div(cards)

def _crear_seccion_parametros(comparativa_actual):
    """Crear sección de parámetros de línea"""
    params = comparativa_actual.get("parametros_linea", {}) if comparativa_actual else {}
    config = comparativa_actual.get("configuracion_calculo", {}) if comparativa_actual else {}
    
    return dbc.Card([
        dbc.CardHeader(html.H5("Parámetros de Línea", className="mb-0")),
        dbc.CardBody([
            # Parámetros básicos
            dbc.Row([
                dbc.Col([
                    dbc.Label("Vano (m):"),
                    dcc.Slider(
                        id="slider-vano-comparativa",
                        min=50, max=1000, step=10, 
                        value=params.get("L_vano", 150),
                        marks={50: '50', 200: '200', 500: '500', 1000: '1000'},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Ángulo θ (°):"),
                    dbc.Select(
                        id="select-theta-comparativa",
                        options=[
                            {"label": "0°", "value": 0},
                            {"label": "45°", "value": 45},
                            {"label": "90°", "value": 90},
                            {"label": "135°", "value": 135},
                            {"label": "180°", "value": 180}
                        ],
                        value=params.get("theta", 0)
                    )
                ], width=6)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Viento Máximo (m/s):"),
                    dbc.Input(
                        id="input-vmax-comparativa",
                        type="number", value=params.get("Vmax", 38.9), step=0.1
                    )
                ], width=4),
                dbc.Col([
                    dbc.Label("Viento Medio (m/s):"),
                    dbc.Input(
                        id="input-vmed-comparativa",
                        type="number", value=params.get("Vmed", 15.56), step=0.1
                    )
                ], width=4),
                dbc.Col([
                    dbc.Label("Hielo (m):"),
                    dbc.Select(
                        id="select-hielo-comparativa",
                        options=[
                            {"label": "0 m", "value": 0},
                            {"label": "0.01 m", "value": 0.01},
                            {"label": "0.02 m", "value": 0.02},
                            {"label": "0.03 m", "value": 0.03}
                        ],
                        value=params.get("t_hielo", 0)
                    )
                ], width=4)
            ], className="mb-4"),
            
            # Configuración de cálculo
            html.H6("Configuración de Cálculo", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Vano Desnivelado:"),
                    dbc.Switch(
                        id="switch-vano-desnivelado",
                        value=config.get("VANO_DESNIVELADO", True)
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Objetivo Optimización:"),
                    dbc.Select(
                        id="select-objetivo-conductor",
                        options=[
                            {"label": "Flecha Mínima", "value": "FlechaMin"},
                            {"label": "Tiro Mínimo", "value": "TiroMin"}
                        ],
                        value=config.get("OBJ_CONDUCTOR", "FlechaMin")
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Salto Porcentual:"),
                    dbc.Select(
                        id="select-salto-porcentual",
                        options=[
                            {"label": "0%", "value": 0},
                            {"label": "5%", "value": 0.05},
                            {"label": "10%", "value": 0.10}
                        ],
                        value=config.get("SALTO_PORCENTUAL", 0.05)
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Paso Afinado:"),
                    dbc.Select(
                        id="select-paso-afinado",
                        options=[
                            {"label": "0%", "value": 0},
                            {"label": "1%", "value": 0.01},
                            {"label": "2%", "value": 0.02}
                        ],
                        value=config.get("PASO_AFINADO", 0.01)
                    )
                ], width=3)
            ], className="mb-3"),
            
            # Controles de desnivel (mostrar solo si vano desnivelado está activo)
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("H Ant. (m):"),
                        dbc.Input(
                            id="input-h-piq-anterior",
                            type="number",
                            value=config.get("H_PIQANTERIOR", 0),
                            min=-15, max=15, step=0.1, size="sm"
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Label("H Post. (m):"),
                        dbc.Input(
                            id="input-h-piq-posterior",
                            type="number",
                            value=config.get("H_PIQPOSTERIOR", 0),
                            min=-15, max=15, step=0.1, size="sm"
                        )
                    ], width=3)
                ])
            ], id="controles-desnivel", style={"display": "block" if config.get("VANO_DESNIVELADO", True) else "none"}),
            
            # Parámetros de viento
            html.Hr(),
            html.H6("Parámetros de Viento", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Exposición:"),
                    dbc.Select(
                        id="select-exposicion-comparativa",
                        options=[
                            {"label": "A", "value": "A"},
                            {"label": "B", "value": "B"},
                            {"label": "C", "value": "C"},
                            {"label": "D", "value": "D"}
                        ],
                        value=params.get("exposicion", "C")
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Clase:"),
                    dbc.Select(
                        id="select-clase-comparativa",
                        options=[
                            {"label": "A", "value": "A"},
                            {"label": "B", "value": "B"},
                            {"label": "C", "value": "C"},
                            {"label": "D", "value": "D"}
                        ],
                        value=params.get("clase", "C")
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Zco (m):"),
                    dbc.Input(
                        id="input-zco-comparativa",
                        type="number", value=params.get("Zco", 13.0), step=0.1
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Cf Cable:"),
                    dbc.Input(
                        id="input-cf-cable-comparativa",
                        type="number", value=params.get("Cf_cable", 1.0), step=0.1
                    )
                ], width=3)
            ], className="mb-4"),
            
            html.Hr(),
            
            # Estados climáticos editables
            html.H6("Estados Climáticos", className="mb-3"),
            html.Div(id="tabla-estados-climaticos")
        ])
    ], className="mb-3")

def _crear_seccion_resultados():
    """Crear sección de resultados"""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5("Resultados", className="mb-0")
                ], width=6),
                dbc.Col([
                    dbc.Button("Calcular Comparativa", id="btn-calcular-comparativa", 
                             color="success", className="me-2")
                ], width=3),
                dbc.Col([
                    dbc.Button("Descargar HTML", id="btn-descargar-html-comparativa", 
                             color="info", className="float-end")
                ], width=3)
            ])
        ]),
        dbc.CardBody([
            html.Div(id="resultados-comparativa", children=[
                dbc.Alert("Configure los cables y parámetros, luego presione 'Calcular Comparativa'", 
                         color="info")
            ])
        ])
    ])

def _crear_tabla_estados_climaticos(estados_climaticos):
    """Crear tabla editable de estados climáticos con estilos consistentes"""
    if not estados_climaticos:
        return html.P("No hay estados climáticos configurados")
    
    # Crear tabla usando Bootstrap con estilos consistentes
    headers = [
        html.Th("Estado", style={"width": "8%"}),
        html.Th("Temp (°C)", style={"width": "12%"}),
        html.Th("Descripción", style={"width": "20%"}),
        html.Th("Viento (m/s)", style={"width": "15%"}),
        html.Th("Hielo (m)", style={"width": "12%"}),
        html.Th("Rest. Cond.", style={"width": "16%"}),
        html.Th("Rest. Guard.", style={"width": "17%"})
    ]
    
    filas = []
    for estado_id, estado_data in estados_climaticos.items():
        fila = html.Tr([
            html.Td(html.Strong(estado_id), style={"verticalAlign": "middle", "textAlign": "center"}),
            html.Td([
                dbc.Input(
                    id={"type": "temp-estado", "index": estado_id},
                    type="number", value=estado_data.get("temperatura", 0),
                    size="sm", step=1, style={"width": "100%"}
                )
            ]),
            html.Td([
                dbc.Input(
                    id={"type": "desc-estado", "index": estado_id},
                    type="text", value=estado_data.get("descripcion", ""),
                    size="sm", style={"width": "100%"}
                )
            ]),
            html.Td([
                dbc.Input(
                    id={"type": "viento-estado", "index": estado_id},
                    type="number", value=estado_data.get("viento_velocidad", 0),
                    size="sm", step=0.1, style={"width": "100%"}
                )
            ]),
            html.Td([
                dbc.Input(
                    id={"type": "hielo-estado", "index": estado_id},
                    type="number", value=estado_data.get("hielo_espesor", 0),
                    size="sm", step=0.001, min=0, max=0.1, style={"width": "100%"}
                )
            ]),
            html.Td([
                dbc.Input(
                    id={"type": "rest-cond-estado", "index": estado_id},
                    type="number", value=estado_data.get("restriccion_conductor", 0.25),
                    size="sm", step=0.01, min=0, max=1, style={"width": "100%"}
                )
            ]),
            html.Td([
                dbc.Input(
                    id={"type": "rest-guard-estado", "index": estado_id},
                    type="number", value=estado_data.get("restriccion_guardia", 0.7),
                    size="sm", step=0.01, min=0, max=1, style={"width": "100%"}
                )
            ])
        ])
        filas.append(fila)
    
    return dbc.Table([
        html.Thead([html.Tr(headers)]),
        html.Tbody(filas)
    ], bordered=True, striped=True, hover=True, size="sm", 
       style={"tableLayout": "fixed", "width": "100%"})

def _crear_modales():
    """Crear modales necesarios"""
    return html.Div([
        # Modal Guardar Como
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Guardar Comparativa Como")),
            dbc.ModalBody([
                dbc.Label("Nuevo título:"),
                dbc.Input(id="input-nuevo-titulo-comparativa", type="text")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancelar-guardar-como-comp", color="secondary", className="me-2"),
                dbc.Button("Guardar", id="btn-confirmar-guardar-como-comp", color="primary")
            ])
        ], id="modal-guardar-como-comparativa", is_open=False),
        
        # Modal Cargar Comparativa
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Cargar Comparativa Existente")),
            dbc.ModalBody([
                dbc.Label("Seleccionar comparativa:"),
                dbc.Select(
                    id="select-comparativa-cargar",
                    placeholder="Seleccione una comparativa..."
                )
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancelar-cargar-comp", color="secondary", className="me-2"),
                dbc.Button("Cargar", id="btn-confirmar-cargar-comp", color="primary")
            ])
        ], id="modal-cargar-comparativa", is_open=False)
    ])

def generar_resultados_desde_cache(cache_data):
    """Generar HTML de resultados desde cache"""
    import json
    import pandas as pd
    from dash import dcc
    
    resultados = cache_data.get("resultados", {})
    cables_calculados = resultados.get("cables_calculados", [])
    dataframes = resultados.get("dataframes", {})
    graficos = resultados.get("graficos", {})
    errores = resultados.get("errores", {})
    
    if not cables_calculados and not errores:
        return dbc.Alert("No hay resultados en cache", color="warning")
    
    # Crear tabs desde cache
    tabs = []
    
    # Tab comparativo primero
    if "comparativo" in graficos:
        try:
            from utils.view_helpers import ViewHelpers
            grafico_comparativo = ViewHelpers.crear_grafico_interactivo(
                graficos["comparativo"]["json"]
            )
            tab_comparativo = dbc.Tab(
                label="Comparativo",
                tab_id="tab-comparativo",
                children=[
                    html.H6("Gráfico Comparativo", className="mt-3"),
                    grafico_comparativo
                ]
            )
            tabs.append(tab_comparativo)
        except Exception as e:
            print(f"Error cargando gráfico comparativo: {e}")
    
    # Tabs por cable
    for cable_nombre in cables_calculados:
        try:
            # Crear tabla desde DataFrame
            tabla_content = html.P("No hay datos de tabla")
            if cable_nombre in dataframes:
                df_json = dataframes[cable_nombre]
                if isinstance(df_json, str):
                    df_data = json.loads(df_json)
                else:
                    df_data = df_json
                df = pd.DataFrame(df_data['data'], columns=df_data['columns'])
                tabla_content = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, size="sm")
            
            # Crear gráficos
            graficos_content = []
            if cable_nombre in graficos:
                for nombre_grafico, archivos in graficos[cable_nombre].items():
                    try:
                        from utils.view_helpers import ViewHelpers
                        grafico = ViewHelpers.crear_grafico_interactivo(archivos["json"])
                        graficos_content.append(html.H6(nombre_grafico, className="mt-3"))
                        graficos_content.append(grafico)
                    except Exception as e:
                        print(f"Error cargando gráfico {nombre_grafico} para {cable_nombre}: {e}")
            
            tab_content = html.Div([
                dbc.Alert(f"Resultados desde cache - {cable_nombre}", color="info"),
                html.H6("Resultados por Estado Climático:"),
                tabla_content
            ] + graficos_content)
            
            tab = dbc.Tab(label=cable_nombre[:20], tab_id=f"tab-cache-{cable_nombre}", children=tab_content)
            tabs.append(tab)
            
        except Exception as e:
            print(f"Error cargando cache para {cable_nombre}: {e}")
            tab_error = dbc.Tab(
                label=cable_nombre[:20], 
                tab_id=f"tab-error-cache-{cable_nombre}",
                children=dbc.Alert(f"Error cargando datos: {e}", color="danger")
            )
            tabs.append(tab_error)
    
    # Tabs de errores
    for cable_nombre, error_msg in errores.items():
        tab_error = dbc.Tab(
            label=f"{cable_nombre[:15]} (Error)",
            tab_id=f"tab-error-{cable_nombre}",
            children=dbc.Alert(f"Error en {cable_nombre}: {error_msg}", color="danger")
        )
        tabs.append(tab_error)
    
    if tabs:
        return html.Div([
            dbc.Alert(f"Cache cargado: {len(cables_calculados)} cables exitosos, {len(errores)} errores", color="success"),
            dbc.Tabs(tabs, active_tab="tab-comparativo" if "comparativo" in graficos else tabs[0].tab_id)
        ])
    else:
        return dbc.Alert("Error procesando cache", color="danger")