"""
Vista para Analisis Estatico de Esfuerzos (AEE)
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def crear_vista_analisis_estatico(estructura_actual=None, calculo_guardado=None):
    """Crear vista de analisis estatico de esfuerzos"""
    
    # Indicador de estructura activa
    if estructura_actual:
        titulo = estructura_actual.get('TITULO', 'Sin titulo')
        indicador = dbc.Alert(f"Estructura: {titulo}", color="info", className="mb-3")
    else:
        indicador = dbc.Alert("No hay estructura activa", color="warning", className="mb-3")
    
    # Parametros AEE
    aee_params = estructura_actual.get('AnalisisEstaticoEsfuerzos', {}) if estructura_actual else {}
    diagramas = aee_params.get('DIAGRAMAS_ACTIVOS', {})
    
    # Controles AEE
    controles = dbc.Card([
        dbc.CardHeader(html.H6("Parametros AEE")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Graficos 3D"),
                    dbc.Switch(
                        id="aee-graficos-3d",
                        value=aee_params.get('GRAFICOS_3D_AEE', True)
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Escala graficos"),
                    dbc.Select(
                        id="aee-escala-graficos",
                        options=[
                            {"label": "Lineal", "value": "lineal"},
                            {"label": "Logaritmica", "value": "logaritmica"}
                        ],
                        value=aee_params.get('escala_graficos', 'lineal')
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Elementos conexion corta"),
                    dbc.Input(
                        id="aee-n-corta",
                        type="number",
                        value=aee_params.get('n_segmentar_conexion_corta', 10),
                        min=5, max=50, step=1
                    )
                ], width=4)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Elementos conexion larga"),
                    dbc.Input(
                        id="aee-n-larga",
                        type="number",
                        value=aee_params.get('n_segmentar_conexion_larga', 30),
                        min=10, max=100, step=1
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Percentil separacion"),
                    dbc.Input(
                        id="aee-percentil",
                        type="number",
                        value=aee_params.get('percentil_separacion_corta_larga', 50),
                        min=0, max=100, step=1
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Mostrar tablas elemento"),
                    dbc.Switch(
                        id="aee-mostrar-tablas",
                        value=aee_params.get('mostrar_tablas_resultados_por_elemento', False)
                    )
                ], width=4)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Plots interactivos"),
                    dbc.Switch(
                        id="aee-plots-interactivos",
                        value=aee_params.get('plots_interactivos', True)
                    )
                ], width=4)
            ], className="mb-3"),
            html.Label("Diagramas activos:"),
            dbc.Checklist(
                id="aee-diagramas",
                options=[
                    {"label": "MQNT", "value": "MQNT"},
                    {"label": "MRT", "value": "MRT"},
                    {"label": "MFE", "value": "MFE"}
                ],
                value=[k for k, v in diagramas.items() if v],
                inline=True
            ),
            html.Hr(),
            dbc.Button("Guardar Parametros", id="btn-guardar-params-aee", color="info", size="sm", className="w-100")
        ])
    ], className="mb-3")
    
    # Botones de accion
    botones = dbc.Row([
        dbc.Col(
            dbc.Button(
                "Calcular AEE",
                id="btn-calcular-aee",
                color="primary",
                size="lg",
                className="w-100"
            ),
            width=6
        ),
        dbc.Col(
            dbc.Button(
                "Cargar desde Cache",
                id="btn-cargar-cache-aee",
                color="secondary",
                size="lg",
                className="w-100"
            ),
            width=6
        )
    ], className="mb-3")
    
    # Area de resultados
    if calculo_guardado:
        resultados = generar_resultados_aee(calculo_guardado, estructura_actual)
    else:
        resultados = html.Div([
            html.P("Presione 'Calcular AEE' para ejecutar el analisis estatico de esfuerzos.", 
                   className="text-muted text-center mt-5")
        ], id="resultados-aee")
    
    return html.Div([
        indicador,
        dbc.Card([
            dbc.CardHeader(html.H4("Analisis Estatico de Esfuerzos (AEE)", className="mb-0")),
            dbc.CardBody([
                controles,
                botones,
                html.Hr(),
                resultados
            ])
        ])
    ])

def generar_resultados_aee(calculo_guardado, estructura_actual):
    """Genera vista de resultados desde cache"""
    from utils.view_helpers import ViewHelpers
    import pandas as pd
    import json
    
    resultados = calculo_guardado.get('resultados', {})
    hash_params = calculo_guardado.get('hash_parametros', '')
    
    # Alerta de cache - solo mostrar si realmente viene de cache
    es_cache = 'fecha_calculo' in calculo_guardado
    
    if es_cache:
        vigente = True
        if estructura_actual:
            from utils.calculo_cache import CalculoCache
            vigente = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        
        alerta = ViewHelpers.crear_alerta_cache(
            mostrar_vigencia=True,
            vigente=vigente
        )
        componentes = [alerta]
    else:
        componentes = []
    
    # DataFrame de cargas aplicadas por nodo
    if resultados.get('df_cargas_completo'):
        df_dict = resultados['df_cargas_completo']
        
        # Reconstruir MultiIndex
        arrays = []
        for level_idx in range(len(df_dict['columns'])):
            level_values = df_dict['columns'][level_idx]
            codes = df_dict['column_codes'][level_idx]
            arrays.append([level_values[code] for code in codes])
        multi_idx = pd.MultiIndex.from_arrays(arrays)
        df_cargas = pd.DataFrame(df_dict['data'], columns=multi_idx)
        
        # Filtrar y formatear
        mask = (df_cargas.iloc[:, 2:].abs() > 0.001).any(axis=1)
        df_cargas = df_cargas[mask]
        df_cargas_fmt = df_cargas.round(2)
        
        componentes.extend([
            html.H5("Cargas Aplicadas por Nodo", className="mt-4 mb-3"),
            ViewHelpers.crear_tabla_html_iframe(
                df_cargas_fmt,
                altura_fila=25,
                altura_min=150,
                altura_max=600
            )
        ])
    
    # Tabla de nodos y conexiones
    if resultados:
        try:
            import numpy as np
            
            # Obtener nodos y conexiones desde resultados guardados
            # Los guardamos en el controller durante el análisis
            nodos_info = resultados.get('nodos_info', {})
            conexiones_info = resultados.get('conexiones_info', [])
            
            if nodos_info:
                # Crear DataFrame de nodos
                nodos_data = []
                for nombre, info in nodos_info.items():
                    nodos_data.append({
                        'Nodo': nombre,
                        'X [m]': f"{info['x']:.2f}",
                        'Y [m]': f"{info['y']:.2f}",
                        'Z [m]': f"{info['z']:.2f}",
                        'Tipo': info['tipo']
                    })
                
                df_nodos = pd.DataFrame(nodos_data)
                
                # Agregar tabla de nodos
                componentes.append(html.H5("Nodos de la Estructura", className="mt-4 mb-3"))
                componentes.append(dbc.Table.from_dataframe(
                    df_nodos, 
                    striped=True, 
                    bordered=True, 
                    hover=True, 
                    size="sm"
                ))
            
            # Tabla de reacciones por hipótesis
            if resultados.get('df_reacciones'):
                df_dict = resultados['df_reacciones']
                df_reacciones = pd.DataFrame(df_dict['data'], columns=df_dict['columns'], index=df_dict['index'])
                
                componentes.append(html.H5("Reacciones en Base por Hipótesis", className="mt-4 mb-3"))
                componentes.append(dbc.Table.from_dataframe(
                    df_reacciones.reset_index(), 
                    striped=True, 
                    bordered=True, 
                    hover=True, 
                    size="sm"
                ))
            
            if conexiones_info:
                # Crear DataFrame de conexiones
                df_conexiones = pd.DataFrame(conexiones_info)
                
                # Agregar tabla de conexiones
                componentes.append(html.H5("Conexiones", className="mt-4 mb-3"))
                componentes.append(dbc.Table.from_dataframe(
                    df_conexiones, 
                    striped=True, 
                    bordered=True, 
                    hover=True, 
                    size="sm"
                ))
                
        except Exception as e:
            print(f"Error generando tablas de nodos/conexiones: {e}")
    
    # Seccion de diagramas
    diagramas = resultados.get('diagramas', {})
    esfuerzos = resultados.get('esfuerzos', {})
    plots_interactivos = estructura_actual.get('AnalisisEstaticoEsfuerzos', {}).get('plots_interactivos', True) if estructura_actual else True
    
    # Resumen Comparativo
    if resultados.get('resumen_comparativo'):
        df_dict = resultados['resumen_comparativo']
        df_resumen = pd.DataFrame(df_dict['data'], columns=df_dict['columns'])
        
        componentes.append(html.H5("Resumen Comparativo - Maximos por Conexion", className="mt-4 mb-3"))
        componentes.append(dbc.Table.from_dataframe(
            df_resumen,
            striped=True,
            bordered=True,
            hover=True,
            size="sm"
        ))
    
    if diagramas:
        componentes.append(html.H5("Diagramas de Esfuerzos", className="mt-4 mb-3"))
        
        for nombre_diagrama in diagramas.keys():
            # Intentar cargar JSON si plots_interactivos
            if plots_interactivos:
                json_filename = f"AEE_{nombre_diagrama}.{hash_params}.json"
                fig_dict = ViewHelpers.cargar_figura_plotly_json(json_filename)
                
                if fig_dict:
                    componentes.append(html.H6(nombre_diagrama.replace('_', ' '), className="mt-3"))
                    componentes.append(dcc.Graph(
                        figure=fig_dict,
                        config={'displayModeBar': True}
                    ))
                    continue
            
            # Fallback a PNG
            img_filename = f"AEE_{nombre_diagrama}.{hash_params}.png"
            img_str = ViewHelpers.cargar_imagen_base64(img_filename)
            
            if img_str:
                componentes.append(html.Div([
                    html.H6(nombre_diagrama.replace('_', ' '), className="mt-3"),
                    html.Img(
                        src=f'data:image/png;base64,{img_str}',
                        style={'width': '100%', 'maxWidth': '1200px'}
                    )
                ]))
    else:
        componentes.append(html.P("No se generaron diagramas.", className="text-muted"))

    
    # Tablas de resultados por hipótesis
    mostrar_tablas = estructura_actual.get('AnalisisEstaticoEsfuerzos', {}).get('mostrar_tablas_resultados_por_elemento', False) if estructura_actual else False
    
    if mostrar_tablas and esfuerzos:
        componentes.append(html.H5("Resultados por Elemento", className="mt-4 mb-3"))
        
        for hip_nombre, hip_data in esfuerzos.items():
            if 'df_resultados' in hip_data:
                df_dict = hip_data['df_resultados']
                df = pd.DataFrame(df_dict['data'], columns=df_dict['columns'])
                
                componentes.extend([
                    html.H6(f"Hipótesis: {hip_nombre}", className="mt-3"),
                    ViewHelpers.crear_tabla_html_iframe(
                        df,
                        altura_fila=25,
                        altura_min=200,
                        altura_max=600
                    )
                ])
    
    return html.Div(componentes, id="resultados-aee")
