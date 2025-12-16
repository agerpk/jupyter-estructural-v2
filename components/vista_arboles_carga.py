"""Vista para Árboles de Carga 2D"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def crear_vista_arboles_carga(estructura_actual, calculo_guardado=None):
    """Crear vista de árboles de carga"""
    
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
                        dcc.Slider(id="param-zoom-arboles", min=0.25, max=2.0, step=0.25, value=0.5,
                                  marks={i/4: f'{int(i*25)}%' for i in range(1, 9)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Escala de Flechas"),
                        dcc.Slider(id="param-escala-flechas", min=0.5, max=3.0, step=0.5, value=1.8,
                                  marks={i/2: f'{int(i*50)}%' for i in range(1, 7)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Grosor de Líneas"),
                        dcc.Slider(id="param-grosor-lineas", min=1, max=5, step=1, value=3.5,
                                  marks={i: str(i) for i in range(1, 6)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Tamaño letra nodos"),
                        dcc.Slider(id="param-fontsize-nodos", min=4, max=16, step=2, value=8,
                                  marks={i: str(i) for i in range(4, 17, 2)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Tamaño letra flechas"),
                        dcc.Slider(id="param-fontsize-flechas", min=4, max=16, step=2, value=10,
                                  marks={i: str(i) for i in range(4, 17, 2)},
                                  tooltip={"placement": "bottom", "always_visible": True})
                    ], md=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="param-mostrar-nodos",
                            options=[{"label": "Mostrar etiquetas de nodos", "value": True}],
                            value=[True],
                            switch=True
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Checklist(
                            id="param-mostrar-sismo",
                            options=[{"label": "Mostrar Sismo (C2)", "value": True}],
                            value=[],
                            switch=True
                        )
                    ], md=6),
                ])
            ])
        ], className="mb-3"),
        
        # Botón generar
        dbc.Row([
            dbc.Col([
                dbc.Button("Generar Árboles de Carga", id="btn-generar-arboles", 
                          color="success", size="lg", className="w-100"),
            ])
        ], className="mb-4"),
        
        # Área de resultados
        html.Div(id="resultados-arboles-carga", children=resultados_previos, className="mt-4")
    ])


def generar_resultados_arboles(calculo_guardado, estructura_actual):
    """Generar HTML de resultados desde cálculo guardado"""
    try:
        import base64
        import pandas as pd
        from config.app_config import DATA_DIR
        
        imagenes = calculo_guardado.get('imagenes', [])
        
        if not imagenes:
            return dbc.Alert("No hay imágenes guardadas", color="info")
        
        imagenes_html = [
            dbc.Alert(f"✓ Resultados cargados desde cálculo anterior ({len(imagenes)} imágenes)", 
                     color="info", className="mb-3")
        ]
        
        # Cargar DataFrame de cargas
        if calculo_guardado.get('df_cargas_completo'):
            df_dict = calculo_guardado['df_cargas_completo']
            
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
            
            # Crear HTML con estilos
            html_table = f'''<html><head><style>
                body {{ margin: 0; padding: 10px; background: white; font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; font-size: 11px; }}
                th, td {{ border: 1px solid #dee2e6; padding: 4px 6px; text-align: right; }}
                th {{ background-color: #f8f9fa; font-weight: 600; position: sticky; top: 0; z-index: 10; }}
                tr:nth-child(even) {{ background-color: #f8f9fa; }}
                tr:hover {{ background-color: #e9ecef; }}
            </style></head><body>{df_cargas_fmt.to_html(border=0, index=False)}</body></html>'''
            
            altura_tabla = min(max(len(df_cargas) * 25 + 80, 150), 600)
            
            imagenes_html.extend([
                html.H5("Cargas Aplicadas por Nodo", className="mt-4 mb-3"),
                html.Iframe(
                    srcDoc=html_table,
                    style={'width': '100%', 'height': f'{altura_tabla}px', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}
                )
            ])
        
        # Organizar imágenes en dos columnas
        imagenes_cards = []
        for img_info in imagenes:
            img_path = DATA_DIR / img_info['nombre']
            
            if not img_path.exists():
                continue
            
            # Leer imagen y convertir a base64
            with open(img_path, 'rb') as f:
                img_str = base64.b64encode(f.read()).decode()
            
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
        return dbc.Alert(f"Error cargando resultados: {str(e)}", color="warning")
