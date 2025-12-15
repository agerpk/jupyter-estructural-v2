"""Vista para Calcular Todo - Ejecución secuencial de todos los cálculos"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def crear_vista_calcular_todo(estructura_actual, calculo_guardado=None):
    """Vista para ejecutar todos los cálculos en secuencia"""
    
    # Si hay cálculo guardado, NO cargar desde aquí - se cargará con el callback
    output_inicial = [dbc.Alert("No hay resultados aún. Presione 'Ejecutar Cálculo Completo' para comenzar.", color="warning")]
    btn_disabled = True
    
    if calculo_guardado:
        output_inicial = [dbc.Alert("✅ Hay resultados guardados. Presione 'Ejecutar Cálculo Completo' para recalcular o ver resultados.", color="info")]
        btn_disabled = False
    
    # CÓDIGO ANTIGUO COMENTADO - Ya no se usa carga desde cache en la vista
    if False and calculo_guardado:
        from utils.calculo_cache import CalculoCache
        from config.app_config import DATA_DIR
        import base64
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        hash_params = calculo_guardado.get('hash_parametros')
        
        # Reconstruir output desde los caches individuales
        output_inicial.append(dbc.Alert("✅ Resultados cargados desde cache", color="info", className="mb-4"))
        
        # 1. CMC
        calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
        if calculo_cmc:
            output_inicial.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
            
            # Tablas
            import pandas as pd
            if calculo_cmc.get('resultados_conductor'):
                df_cond = pd.DataFrame(calculo_cmc['resultados_conductor']).T.round(2)
                output_inicial.append(html.H5("Resultados Conductor", className="mt-3"))
                output_inicial.append(dbc.Table.from_dataframe(df_cond, striped=True, bordered=True, hover=True, size="sm"))
            
            if calculo_cmc.get('resultados_guardia'):
                df_guard = pd.DataFrame(calculo_cmc['resultados_guardia']).T.round(2)
                output_inicial.append(html.H5("Resultados Cable de Guardia 1", className="mt-3"))
                output_inicial.append(dbc.Table.from_dataframe(df_guard, striped=True, bordered=True, hover=True, size="sm"))
            
            if calculo_cmc.get('resultados_guardia2'):
                df_guard2 = pd.DataFrame(calculo_cmc['resultados_guardia2']).T.round(2)
                output_inicial.append(html.H5("Resultados Cable de Guardia 2", className="mt-3"))
                output_inicial.append(dbc.Table.from_dataframe(df_guard2, striped=True, bordered=True, hover=True, size="sm"))
            
            # Imágenes CMC
            output_inicial.append(html.H5("Gráficos de Flechas", className="mt-4"))
            for tipo in ['Combinado', 'Conductor', 'Guardia']:
                img_path = DATA_DIR / f"CMC_{tipo}.{hash_params}.png"
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_str = base64.b64encode(f.read()).decode()
                    output_inicial.append(html.H6(f"{tipo}", className="mt-3"))
                    output_inicial.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%', 'maxWidth': '1000px'}))
        
        # 2. DGE
        calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
        if calculo_dge:
            output_inicial.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
            
            dims = calculo_dge.get('dimensiones', {})
            nodes_key = calculo_dge.get('nodes_key', {})
            
            texto_dge = f"""DIMENSIONES DE ESTRUCTURA
Altura total: {dims.get('altura_total', 0):.2f} m
Alturas: h1a={dims.get('h1a', 0):.2f}m, h2a={dims.get('h2a', 0):.2f}m
Ménsulas: lmen={dims.get('lmen', 0):.2f}m, lmenhg={dims.get('lmenhg', 0):.2f}m
Cable guardia: hhg={dims.get('hhg', 0):.2f}m

NODOS ESTRUCTURALES ({len(nodes_key)} nodos)"""
            
            for categoria, prefijo in [('BASE', 'BASE'), ('CRUCE', 'CROSS'), ('CONDUCTOR', 'C'), ('GUARDIA', 'HG')]:
                nodos_cat = {k: v for k, v in nodes_key.items() if k.startswith(prefijo)}
                if nodos_cat:
                    texto_dge += f"\n{categoria}:\n"
                    for k, v in nodos_cat.items():
                        texto_dge += f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})\n"
            
            output_inicial.append(html.Pre(texto_dge, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.85rem', 'whiteSpace': 'pre-wrap'}))
            
            # Imágenes DGE
            output_inicial.append(html.H5("Gráficos de Estructura", className="mt-4"))
            for tipo in ['Estructura', 'Cabezal']:
                img_path = DATA_DIR / f"{tipo}.{hash_params}.png"
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_str = base64.b64encode(f.read()).decode()
                    output_inicial.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '48%', 'margin': '5px', 'display': 'inline-block'}))
            
            # Memoria DGE
            if calculo_dge.get('memoria_calculo'):
                output_inicial.append(html.Hr(className="mt-4"))
                output_inicial.append(html.H5("Memoria de Cálculo: Diseño Geométrico de Estructura", className="mb-3"))
                output_inicial.append(html.Pre(calculo_dge['memoria_calculo'], style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
        
        # 3. DME
        calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
        if calculo_dme:
            output_inicial.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
            
            # Tabla de reacciones
            if calculo_dme.get('df_reacciones'):
                import pandas as pd
                df_reacciones = pd.DataFrame.from_dict(calculo_dme['df_reacciones'], orient='index').round(2)
                output_inicial.append(html.H5("Reacciones en BASE", className="mt-3"))
                output_inicial.append(dbc.Table.from_dataframe(df_reacciones.head(10), striped=True, bordered=True, hover=True, size="sm"))
            
            # Imágenes DME
            for tipo in ['Polar', 'Barras']:
                img_path = DATA_DIR / f"DME_{tipo}.{hash_params}.png"
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_str = base64.b64encode(f.read()).decode()
                    output_inicial.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '48%', 'margin': '5px', 'display': 'inline-block'}))
        
        # 4. Árboles
        calculo_arboles = CalculoCache.cargar_calculo_arboles(nombre_estructura)
        if calculo_arboles:
            output_inicial.append(html.H3("4. ÁRBOLES DE CARGA", className="mt-4"))
            
            imagenes_arboles = []
            for img_info in calculo_arboles.get('imagenes', [])[:6]:
                img_path = DATA_DIR / img_info['nombre']
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_str = base64.b64encode(f.read()).decode()
                    imagenes_arboles.append(
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H6(f"{img_info['hipotesis']}", className="mb-0 text-center")),
                                dbc.CardBody([html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%'})], style={'padding': '0.5rem'})
                            ], className="mb-3")
                        ], lg=4, md=6)
                    )
            if imagenes_arboles:
                output_inicial.append(dbc.Row(imagenes_arboles))
            output_inicial.append(html.P(f"Total de hipótesis generadas: {len(calculo_arboles.get('imagenes', []))}", className="mt-2"))
        
        # 5. SPH
        calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
        if calculo_sph:
            output_inicial.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
            
            resultados_sph = calculo_sph.get('resultados', {})
            if resultados_sph:
                info_postes = []
                for i, poste in enumerate(resultados_sph.get('postes_seleccionados', []), 1):
                    info_postes.append(html.Li(f"Poste {i}: {poste.get('nombre', 'N/A')} - {poste.get('longitud_total', 0):.1f}m"))
                
                output_inicial.append(dbc.Card([
                    dbc.CardBody([
                        html.H5("Postes Seleccionados:"),
                        html.Ul(info_postes),
                        html.P(f"Orientación: {resultados_sph.get('orientacion', 'N/A')}"),
                        html.P(f"Cantidad de postes: {resultados_sph.get('n_postes', 0)}")
                    ])
                ], className="mt-2"))
                
                # Memoria SPH
                if calculo_sph.get('desarrollo_texto'):
                    output_inicial.append(html.Hr(className="mt-4"))
                    output_inicial.append(html.H5("Memoria de Cálculo: Selección de Postes de Hormigón", className="mb-3"))
                    output_inicial.append(html.Pre(calculo_sph['desarrollo_texto'], style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
        
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
                    ], md=5),
                    dbc.Col([
                        dbc.Button(
                            "Cargar desde Cache",
                            id="btn-cargar-cache-todo",
                            color="info",
                            size="lg",
                            className="w-100",
                            disabled=btn_disabled
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Button(
                            "Descargar HTML",
                            id="btn-descargar-html-todo",
                            color="primary",
                            size="lg",
                            className="w-100",
                            disabled=btn_disabled
                        )
                    ], md=3)
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
