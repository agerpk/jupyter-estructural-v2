"""Vista para Árboles de Carga 2D"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.view_helpers import ViewHelpers
from utils.calculo_cache import CalculoCache
import pandas as pd
import json


def crear_vista_arboles_carga(estructura_actual, calculo_guardado=None):
    """Crear vista de árboles de carga"""
    
    # Cargar configuración persistente
    from config.app_config import DATA_DIR
    import json
    config_path = DATA_DIR / "arboles_config.json"
    config_default = {
        "zoom": 0.5,
        "escala_flecha": 2.0,
        "grosor_linea": 3,
        "fontsize_nodos": 6,
        "fontsize_flechas": 6,
        "mostrar_nodos": True,
        "mostrar_sismo": False,
        "usar_3d": True
    }
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except:
        config = config_default
    
    # Si hay cache, usar configuración del cache
    if calculo_guardado and calculo_guardado.get('config_arboles'):
        config.update(calculo_guardado['config_arboles'])
    
    # Cargar resultados previos si existen
    resultados_previos = None
    if calculo_guardado:
        resultados_previos = generar_resultados_arboles(calculo_guardado, estructura_actual)
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("Árboles de Carga 2D", className="mb-4"),
                dbc.Button("← Volver", id={"type": "btn-volver", "index": "arboles-carga"}, 
                          color="secondary", size="sm", className="mb-3"),
            ])
        ]),
        
        # Información
        dbc.Alert([
            html.H5("Generación de Árboles de Carga", className="alert-heading"),
            html.P("Esta herramienta genera diagramas 2D (plano XZ) mostrando las cargas aplicadas en cada hipótesis."),
        ], color="info", className="mb-3"),
        
        # Configuración
        dbc.Card([
            dbc.CardHeader(html.H5("Configuración de Visualización")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Zoom"),
                        dcc.Slider(id="slider-zoom-arboles", min=0.25, max=2.0, step=0.25, value=config["zoom"],
                                  marks={i/4: f'{int(i*25)}%' for i in range(1, 9)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Escala de Flechas"),
                        dcc.Slider(id="slider-escala-flechas", min=0.5, max=3.0, step=0.5, value=config["escala_flecha"],
                                  marks={i/2: f'{int(i*50)}%' for i in range(1, 7)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Grosor de Líneas"),
                        dcc.Slider(id="slider-grosor-lineas", min=1, max=5, step=1, value=config["grosor_linea"],
                                  marks={i: str(i) for i in range(1, 6)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Tamaño letra nodos"),
                        dcc.Slider(id="slider-fontsize-nodos", min=4, max=16, step=2, value=config["fontsize_nodos"],
                                  marks={i: str(i) for i in range(4, 17, 2)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Tamaño letra flechas"),
                        dcc.Slider(id="slider-fontsize-flechas", min=4, max=16, step=2, value=config["fontsize_flechas"],
                                  marks={i: str(i) for i in range(4, 17, 2)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="param-mostrar-nodos",
                            options=[{"label": "Mostrar etiquetas de nodos", "value": True}],
                            value=[True] if config["mostrar_nodos"] else [],
                            switch=True
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Checklist(
                            id="param-mostrar-sismo",
                            options=[{"label": "Mostrar Sismo (C2)", "value": True}],
                            value=[True] if config["mostrar_sismo"] else [],
                            switch=True
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Checklist(
                            id="param-adc-3d",
                            options=[{"label": "Gráficos 3D", "value": True}],
                            value=[True] if config["usar_3d"] else [],
                            switch=True
                        )
                    ], md=4),
                ])
            ])
        ], className="mb-3"),
        
        # Botones
        dbc.Row([
            dbc.Col([
                dbc.Button("Generar Árboles de Carga", id="btn-generar-arboles", 
                          color="success", size="lg", className="w-100"),
            ], md=6),
            dbc.Col([
                dbc.Button("Cargar desde Cache", id="btn-cargar-cache-arboles", 
                          color="info", size="lg", className="w-100"),
            ], md=6)
        ], className="mb-4"),
        
        # Área de resultados
        html.Div(id="resultados-arboles-carga", children=resultados_previos, className="mt-4")
    ])


def generar_resultados_arboles(calculo_guardado, estructura_actual, mostrar_alerta_cache=False):
    """Generar HTML de resultados desde cálculo guardado"""
    try:
        imagenes = calculo_guardado.get('imagenes', [])
        
        if not imagenes:
            return dbc.Alert("No hay imágenes guardadas", color="info")
        
        # Verificar vigencia
        vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        
        imagenes_html = []
        if mostrar_alerta_cache:
            imagenes_html.append(ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=vigente))
        
        # Cargar DataFrame de cargas
        if calculo_guardado.get('df_cargas_completo'):
            df_dict = calculo_guardado['df_cargas_completo']
            
            # Reconstruir MultiIndex correctamente
            if 'columns' in df_dict and 'column_codes' in df_dict:
                # Método con codes (nuevo)
                arrays = []
                for level_idx in range(len(df_dict['columns'])):
                    level_values = df_dict['columns'][level_idx]
                    codes = df_dict['column_codes'][level_idx]
                    arrays.append([level_values[code] for code in codes])
                multi_idx = pd.MultiIndex.from_arrays(arrays)
                # Nombrar niveles para que aparezca la hipótesis en el header
                try:
                    multi_idx.names = ['Hipótesis', 'Componente']
                except Exception:
                    pass
                df_cargas = pd.DataFrame(df_dict['data'], columns=multi_idx)
            else:
                # Fallback: usar orient='split' para preservar MultiIndex
                df_cargas = pd.read_json(json.dumps(df_dict), orient='split')
                
                # Si no tiene MultiIndex, intentar reconstruirlo desde nombres de columnas
                
                # Si no tiene MultiIndex, intentar reconstruirlo desde nombres de columnas
                if not isinstance(df_cargas.columns, pd.MultiIndex) and len(df_cargas.columns) > 2:
                    # Extraer códigos de hipótesis de nombres de columnas
                    nivel_superior = ['', '']  # Nodo, Unidad
                    nivel_inferior = ['Nodo', 'Unidad']
                    
                    for col in df_cargas.columns[2:]:
                        if '_' in str(col):
                            # Extraer código de hipótesis del nombre completo
                            partes = str(col).split('_')
                            codigo = partes[-2] if len(partes) >= 2 else f'H{len(nivel_superior)//3}'
                        else:
                            codigo = f'H{(len(nivel_superior)-2)//3}'
                        
                        if len(nivel_superior) == 2 or nivel_superior[-3] != codigo:
                            # Nueva hipótesis
                            nivel_superior.extend([codigo] * 3)
                            nivel_inferior.extend(['x', 'y', 'z'])
                    
                    multi_idx = pd.MultiIndex.from_arrays([nivel_superior, nivel_inferior])
                    df_cargas.columns = multi_idx
            
            # Filtrar y formatear
            mask = (df_cargas.iloc[:, 2:].abs() > 0.001).any(axis=1)
            df_cargas = df_cargas[mask]
            df_cargas_fmt = df_cargas.round(2)
            
            imagenes_html.extend([
                html.H5("Cargas Aplicadas por Nodo", className="mt-4 mb-3"),
                ViewHelpers.crear_tabla_html_iframe(df_cargas_fmt)
            ])
        
        # Organizar imágenes en dos columnas (verificar si hay JSON para 3D)
        imagenes_cards = []
        for img_info in imagenes:
            # Intentar cargar JSON para gráfico 3D interactivo
            nombre_json = img_info['nombre'].replace('.png', '.json')
            fig_dict = ViewHelpers.cargar_figura_plotly_json(nombre_json)
            
            if fig_dict:
                # Gráfico 3D interactivo
                imagenes_cards.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6(f"{img_info['hipotesis']}", className="mb-0 text-center")),
                            dbc.CardBody([
                                dcc.Graph(
                                    figure=fig_dict,
                                    config={'displayModeBar': True, 'responsive': True},
                                    style={'height': '900px', 'width': '100%'}
                                )
                            ], style={'padding': '0.5rem'})
                        ], className="mb-3")
                    ], lg=12, md=12)
                )
            else:
                # Gráfico 2D estático
                img_str = ViewHelpers.cargar_imagen_base64(img_info['nombre'])
                if not img_str:
                    continue
                
                imagenes_cards.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6(f"Hipótesis: {img_info['hipotesis']}", className="mb-0 text-center")),
                            dbc.CardBody([
                                html.Img(src=f'data:image/png;base64,{img_str}', 
                                        style={'width': '50%', 'height': 'auto', 'display': 'block', 'margin': '0 auto'}, 
                                        className="img-fluid")
                            ], style={'padding': '0.5rem'})
                        ], className="mb-3")
                    ], lg=5, md=6)
                )
        
        # Crear filas de 2 columnas centradas
        if imagenes_cards:
            imagenes_html.extend([
                html.H5("Árboles de Carga por Hipótesis", className="mt-4 mb-3"),
                dbc.Row(imagenes_cards, justify="center")
            ])
        
        return html.Div(imagenes_html)
        
    except Exception as e:
        import traceback
        print(f"Error en generar_resultados_arboles: {traceback.format_exc()}")
        return dbc.Alert(f"Error cargando resultados: {str(e)}", color="warning")
