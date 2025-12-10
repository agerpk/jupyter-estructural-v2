"""Controlador para Calcular Todo - Carga resultados de cache de cada vista"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState
import base64


def register_callbacks(app):
    """Registrar callbacks de calcular todo"""
    
    state = AppState()
    calculo_en_progreso = {'paso': 0, 'resultados': []}
    
    @app.callback(
        Output("calculo-todo-interval", "disabled"),
        Output("calculo-todo-interval", "n_intervals"),
        Output("btn-calcular-todo", "disabled"),
        Input("btn-calcular-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def iniciar_calculo_completo(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        # Iniciar el proceso
        calculo_en_progreso['paso'] = 0
        calculo_en_progreso['resultados'] = []
        calculo_en_progreso['estructura_actual'] = estructura_actual
        calculo_en_progreso['state'] = state
        
        return False, 0, True  # Habilitar interval, resetear contador, deshabilitar botón
    
    @app.callback(
        Output("output-calcular-todo", "children"),
        Output("btn-descargar-html-todo", "disabled"),
        Output("calculo-todo-interval", "disabled", allow_duplicate=True),
        Output("btn-calcular-todo", "disabled", allow_duplicate=True),
        Input("calculo-todo-interval", "n_intervals"),
        prevent_initial_call=True
    )
    def ejecutar_paso_calculo(n_intervals):
        if calculo_en_progreso['paso'] == 0:
            # Inicializar
            estructura_actual = calculo_en_progreso['estructura_actual']
            state = calculo_en_progreso['state']
            
            from utils.calculo_cache import CalculoCache
            from config.app_config import DATA_DIR
            from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            resultados = []
            
            # 1. CMC
            resultados.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
            resultado_cmc = ejecutar_calculo_cmc_automatico(estructura_actual, state)
            if not resultado_cmc["exito"]:
                return [dbc.Alert(f"Error en CMC: {resultado_cmc['mensaje']}", color="danger")], True
            
            calculo_en_progreso['resultados'] = resultados
            calculo_en_progreso['paso'] = 1
            return resultados, True, False, True  # Continuar interval
        
        elif calculo_en_progreso['paso'] == 1:
            # Paso 2: DGE
            estructura_actual = calculo_en_progreso['estructura_actual']
            state = calculo_en_progreso['state']
            resultados = calculo_en_progreso['resultados']
            
            from utils.calculo_cache import CalculoCache
            from config.app_config import DATA_DIR
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            # Agregar tablas de resultados CMC
            import pandas as pd
            if state.calculo_mecanico.resultados_conductor:
                df_cond = pd.DataFrame(state.calculo_mecanico.resultados_conductor).T
                resultados.append(html.H5("Resultados Conductor", className="mt-3"))
                resultados.append(dbc.Table.from_dataframe(df_cond, striped=True, bordered=True, hover=True, size="sm"))
            
            if state.calculo_mecanico.resultados_guardia:
                df_guard = pd.DataFrame(state.calculo_mecanico.resultados_guardia).T
                resultados.append(html.H5("Resultados Cable de Guardia", className="mt-3"))
                resultados.append(dbc.Table.from_dataframe(df_guard, striped=True, bordered=True, hover=True, size="sm"))
            
            # Generar gráficos interactivos de flechas (igual que en vista CMC)
            from utils.plot_flechas import crear_grafico_flechas
            try:
                fig_combinado, fig_conductor, fig_guardia = crear_grafico_flechas(
                    state.calculo_mecanico.resultados_conductor,
                    state.calculo_mecanico.resultados_guardia,
                    estructura_actual.get('L_vano')
                )
                resultados.append(html.H5("Gráficos de Flechas", className="mt-4"))
                resultados.append(html.H6("Conductor y Guardia", className="mt-3"))
                resultados.append(dcc.Graph(figure=fig_combinado, config={'displayModeBar': True}))
                resultados.append(html.H6("Solo Conductor", className="mt-3"))
                resultados.append(dcc.Graph(figure=fig_conductor, config={'displayModeBar': True}))
                resultados.append(html.H6("Solo Cable de Guardia", className="mt-3"))
                resultados.append(dcc.Graph(figure=fig_guardia, config={'displayModeBar': True}))
            except Exception as e:
                print(f"Error generando gráficos de flechas: {e}")
            
            resultados.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
            from EstructuraAEA_Geometria import EstructuraAEA_Geometria
            from HipotesisMaestro import hipotesis_maestro
            
            fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
            fmax_guardia = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia.values()])
            
            estructura_geometria = EstructuraAEA_Geometria(
                tipo_estructura=estructura_actual.get("TIPO_ESTRUCTURA"),
                tension_nominal=estructura_actual.get("TENSION"),
                zona_estructura=estructura_actual.get("Zona_estructura"),
                disposicion=estructura_actual.get("DISPOSICION"),
                terna=estructura_actual.get("TERNA"),
                cant_hg=estructura_actual.get("CANT_HG"),
                alpha_quiebre=estructura_actual.get("alpha"),
                altura_minima_cable=estructura_actual.get("ALTURA_MINIMA_CABLE"),
                long_mensula_min_conductor=estructura_actual.get("LONGITUD_MENSULA_MINIMA_CONDUCTOR"),
                long_mensula_min_guardia=estructura_actual.get("LONGITUD_MENSULA_MINIMA_GUARDIA"),
                hadd=estructura_actual.get("HADD"),
                hadd_entre_amarres=estructura_actual.get("HADD_ENTRE_AMARRES"),
                lk=estructura_actual.get("Lk"),
                ancho_cruceta=estructura_actual.get("ANCHO_CRUCETA"),
                cable_conductor=state.calculo_objetos.cable_conductor,
                cable_guardia=state.calculo_objetos.cable_guardia,
                peso_estructura=estructura_actual.get("PESTRUCTURA"),
                peso_cadena=estructura_actual.get("PCADENA"),
                hg_centrado=estructura_actual.get("HG_CENTRADO"),
                ang_apantallamiento=estructura_actual.get("ANG_APANTALLAMIENTO"),
                hadd_hg=estructura_actual.get("HADD_HG"),
                hadd_lmen=estructura_actual.get("HADD_LMEN"),
                dist_reposicionar_hg=estructura_actual.get("DIST_REPOSICIONAR_HG"),
                ajustar_por_altura_msnm=estructura_actual.get("AJUSTAR_POR_ALTURA_MSNM"),
                metodo_altura_msnm=estructura_actual.get("METODO_ALTURA_MSNM"),
                altura_msnm=estructura_actual.get("Altura_MSNM")
            )
            
            estructura_geometria.dimensionar_unifilar(
                estructura_actual.get("L_vano"),
                fmax_conductor,
                fmax_guardia,
                dist_reposicionar_hg=estructura_actual.get("DIST_REPOSICIONAR_HG"),
                autoajustar_lmenhg=estructura_actual.get("AUTOAJUSTAR_LMENHG")
            )
            
            state.calculo_objetos.estructura_geometria = estructura_geometria
            
            # Generar memoria de cálculo DGE
            from utils.memoria_calculo_dge import gen_memoria_calculo_DGE
            memoria_dge = gen_memoria_calculo_DGE(estructura_geometria)
            
            nodes_key = estructura_geometria.obtener_nodes_key()
            dims = estructura_geometria.dimensiones
            resultados.append(html.H6(f"Flechas máximas: conductor={fmax_conductor:.2f}m, guardia={fmax_guardia:.2f}m", className="mb-3"))
            
            # Texto detallado de nodos y dimensiones
            texto_dge = f"""PARÁMETROS DE DISEÑO
Tipo estructura: {estructura_actual.get('TIPO_ESTRUCTURA')}
Tensión nominal: {estructura_actual.get('TENSION')} kV
Zona: {estructura_actual.get('Zona_estructura')}
Disposición: {estructura_actual.get('DISPOSICION')}
Terna: {estructura_actual.get('TERNA')}
Cantidad HG: {estructura_actual.get('CANT_HG')}
Vano: {estructura_actual.get('L_vano')} m

DIMENSIONES DE ESTRUCTURA
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
            
            resultados.append(html.Pre(texto_dge, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.85rem', 'whiteSpace': 'pre-wrap'}))
            
            # Generar y guardar gráficos DGE
            from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
            from EstructuraAEA_Graficos import EstructuraAEA_Graficos
            import matplotlib.pyplot as plt
            
            estructura_mecanica_temp = EstructuraAEA_Mecanica(estructura_geometria)
            estructura_mecanica_temp.asignar_cargas_hipotesis(
                state.calculo_mecanico.df_cargas_totales,
                state.calculo_mecanico.resultados_conductor,
                state.calculo_mecanico.resultados_guardia,
                estructura_actual.get('L_vano'),
                hipotesis_maestro,
                estructura_actual.get('t_hielo')
            )
            
            estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica_temp)
            
            # Graficar estructura
            estructura_graficos.graficar_estructura(
                zoom_cabezal=estructura_actual.get('ZOOM_CABEZAL', 0.95),
                titulo_reemplazo=estructura_actual.get('TITULO_REEMPLAZO', estructura_actual.get('TIPO_ESTRUCTURA'))
            )
            fig_estructura = plt.gcf()
            
            # Graficar cabezal
            estructura_graficos.graficar_cabezal(
                zoom_cabezal=estructura_actual.get('ZOOM_CABEZAL', 0.95) * 1.5,
                titulo_reemplazo=estructura_actual.get('TITULO_REEMPLAZO', estructura_actual.get('TIPO_ESTRUCTURA'))
            )
            fig_cabezal = plt.gcf()
            
            # Guardar en cache
            CalculoCache.guardar_calculo_dge(
                nombre_estructura,
                estructura_actual,
                dims,
                nodes_key,
                fig_estructura,
                fig_cabezal,
                memoria_dge
            )
            
            # Mostrar gráficos
            calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
            if calculo_dge:
                hash_dge = calculo_dge.get('hash_parametros')
                resultados.append(html.H5("Gráficos de Estructura", className="mt-4"))
                for tipo in ['Estructura', 'Cabezal']:
                    img_path = DATA_DIR / f"{tipo}.{hash_dge}.png"
                    if img_path.exists():
                        with open(img_path, 'rb') as f:
                            img_str = base64.b64encode(f.read()).decode()
                        resultados.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '48%', 'margin': '5px', 'display': 'inline-block'}))
            
            # Memoria de cálculo DGE
            resultados.append(html.Hr(className="mt-4"))
            resultados.append(html.H5("Memoria de Cálculo: Diseño Geométrico de Estructura", className="mb-3"))
            resultados.append(html.Pre(memoria_dge, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
            
            calculo_en_progreso['resultados'] = resultados
            calculo_en_progreso['paso'] = 2
            return resultados, True, False, True  # Continuar interval
        
        elif calculo_en_progreso['paso'] == 2:
            # Paso 3: DME
            estructura_actual = calculo_en_progreso['estructura_actual']
            state = calculo_en_progreso['state']
            resultados = calculo_en_progreso['resultados']
            
            from utils.calculo_cache import CalculoCache
            from config.app_config import DATA_DIR
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            estructura_geometria = state.calculo_objetos.estructura_geometria
            
            resultados.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
            from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
            from HipotesisMaestro import hipotesis_maestro
            
            estructura_mecanica = EstructuraAEA_Mecanica(estructura_geometria)
            estructura_mecanica.asignar_cargas_hipotesis(
                state.calculo_mecanico.df_cargas_totales,
                state.calculo_mecanico.resultados_conductor,
                state.calculo_mecanico.resultados_guardia,
                estructura_actual.get('L_vano'),
                hipotesis_maestro,
                estructura_actual.get('t_hielo')
            )
            
            nodes_key = estructura_geometria.nodes_key
            nodo_cima = "TOP" if "TOP" in nodes_key else ("HG1" if "HG1" in nodes_key else max(nodes_key.items(), key=lambda x: x[1][2])[0])
            estructura_mecanica.calcular_reacciones_tiros_cima(nodo_apoyo="BASE", nodo_cima=nodo_cima)
            state.calculo_objetos.estructura_mecanica = estructura_mecanica
            
            # Agregar outputs de texto DME
            df_reacciones = estructura_mecanica.df_reacciones
            if df_reacciones is not None and not df_reacciones.empty:
                resultados.append(html.H5("Reacciones en BASE", className="mt-3"))
                resultados.append(dbc.Table.from_dataframe(df_reacciones.head(10), striped=True, bordered=True, hover=True, size="sm"))
            
            calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
            if calculo_dme:
                hash_dme = calculo_dme.get('hash_parametros')
                for tipo in ['Polar', 'Barras']:
                    img_path = DATA_DIR / f"DME_{tipo}.{hash_dme}.png"
                    if img_path.exists():
                        with open(img_path, 'rb') as f:
                            img_str = base64.b64encode(f.read()).decode()
                        resultados.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '48%', 'margin': '5px', 'display': 'inline-block'}))
            
            calculo_en_progreso['resultados'] = resultados
            calculo_en_progreso['paso'] = 3
            return resultados, True, False, True  # Continuar interval
        
        elif calculo_en_progreso['paso'] == 3:
            # Paso 4: Árboles
            estructura_actual = calculo_en_progreso['estructura_actual']
            state = calculo_en_progreso['state']
            resultados = calculo_en_progreso['resultados']
            
            from utils.calculo_cache import CalculoCache
            from config.app_config import DATA_DIR
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            estructura_mecanica = state.calculo_objetos.estructura_mecanica
            
            resultados.append(html.H3("4. ÁRBOLES DE CARGA", className="mt-4"))
            try:
                from utils.arboles_carga import generar_arboles_carga
                resultado_arboles = generar_arboles_carga(
                    estructura_mecanica, estructura_actual,
                    zoom=1.0, escala_flecha=1.0, grosor_linea=1.5,
                    mostrar_nodos=True, fontsize_nodos=8, fontsize_flechas=8, mostrar_sismo=False
                )
                
                if resultado_arboles['exito']:
                    CalculoCache.guardar_calculo_arboles(nombre_estructura, estructura_actual, resultado_arboles['imagenes'])
                    
                    imagenes_arboles = []
                    for img_info in resultado_arboles['imagenes'][:6]:
                        with open(img_info['ruta'], 'rb') as f:
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
                        resultados.append(dbc.Row(imagenes_arboles))
                    resultados.append(html.P(f"Total de hipótesis generadas: {len(resultado_arboles['imagenes'])}", className="mt-2"))
                else:
                    resultados.append(dbc.Alert(f"⚠️ {resultado_arboles['mensaje']}", color="warning"))
            except Exception as e:
                resultados.append(dbc.Alert(f"⚠️ Error en Árboles: {str(e)}", color="warning"))
            
            calculo_en_progreso['resultados'] = resultados
            calculo_en_progreso['paso'] = 4
            return resultados, True, False, True  # Continuar interval
        
        elif calculo_en_progreso['paso'] == 4:
            # Paso 5: SPH
            estructura_actual = calculo_en_progreso['estructura_actual']
            state = calculo_en_progreso['state']
            resultados = calculo_en_progreso['resultados']
            
            from utils.calculo_cache import CalculoCache
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            estructura_geometria = state.calculo_objetos.estructura_geometria
            estructura_mecanica = state.calculo_objetos.estructura_mecanica
            
            resultados.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
            try:
                from PostesHormigon import PostesHormigon
                import io, sys, hashlib, json
                
                postes = PostesHormigon()
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                
                resultados_sph = postes.calcular_seleccion_postes(
                    geometria=estructura_geometria,
                    mecanica=estructura_mecanica,
                    FORZAR_N_POSTES=estructura_actual.get('FORZAR_N_POSTES', 0),
                    FORZAR_ORIENTACION=estructura_actual.get('FORZAR_ORIENTACION', 'No'),
                    ANCHO_CRUCETA=estructura_actual.get('ANCHO_CRUCETA', 0.2),
                    PRIORIDAD_DIMENSIONADO=estructura_actual.get('PRIORIDAD_DIMENSIONADO', 'longitud_total')
                )
                
                postes.imprimir_desarrollo_seleccion_postes()
                desarrollo_texto = buffer.getvalue()
                sys.stdout = old_stdout
                
                calculo_sph = {
                    'parametros': estructura_actual,
                    'hash_parametros': hashlib.md5(json.dumps(estructura_actual, sort_keys=True).encode()).hexdigest(),
                    'resultados': resultados_sph,
                    'desarrollo_texto': desarrollo_texto
                }
                CalculoCache.guardar_calculo_sph(nombre_estructura, calculo_sph)
                
                if resultados_sph:
                    info_postes = []
                    for i, poste in enumerate(resultados_sph.get('postes_seleccionados', []), 1):
                        info_postes.append(html.Li(f"Poste {i}: {poste.get('nombre', 'N/A')} - {poste.get('longitud_total', 0):.1f}m"))
                    
                    resultados.append(dbc.Card([
                        dbc.CardBody([
                            html.H5("Postes Seleccionados:"),
                            html.Ul(info_postes),
                            html.P(f"Orientación: {resultados_sph.get('orientacion', 'N/A')}"),
                            html.P(f"Cantidad de postes: {resultados_sph.get('n_postes', 0)}")
                        ])
                    ], className="mt-2"))
                    
                    # Memoria de cálculo SPH (desarrollo completo)
                    resultados.append(html.Hr(className="mt-4"))
                    resultados.append(html.H5("Memoria de Cálculo: Selección de Postes de Hormigón", className="mb-3"))
                    resultados.append(html.Pre(desarrollo_texto,
                        style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
            except Exception as e:
                resultados.append(dbc.Alert(f"⚠️ Error en SPH: {str(e)}", color="warning"))
            
            resultados.insert(0, dbc.Alert("✅ CÁLCULO COMPLETO FINALIZADO EXITOSAMENTE", color="success", className="mb-4"))
            CalculoCache.guardar_calculo_todo(nombre_estructura, estructura_actual, {'componentes': resultados})
            
            calculo_en_progreso['paso'] = 5
            return resultados, False, True, False  # Detener interval, habilitar descarga y botón
        
        else:
            # Ya terminó
            return calculo_en_progreso['resultados'], False, True, False
    
    @app.callback(
        Output("download-html-completo", "data"),
        Input("btn-descargar-html-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def descargar_html_completo(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        from utils.calculo_cache import CalculoCache
        from config.app_config import DATA_DIR
        import pandas as pd
        
        titulo = estructura_actual.get("TITULO", "estructura")
        tipo = estructura_actual.get("TIPO_ESTRUCTURA", "")
        tension = estructura_actual.get("TENSION", "")
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        
        # Reconstruir HTML desde los caches
        html_parts = []
        
        # Verificar que existan los caches
        calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
        if not calculo_cmc:
            return dict(content="<html><body><p>No hay resultados para exportar. Ejecute el cálculo primero.</p></body></html>", filename=f"{titulo}_error.html")
        
        hash_params = calculo_cmc.get('hash_parametros')
        
        # 1. CMC
        html_parts.append('<h3>1. CÁLCULO MECÁNICO DE CABLES (CMC)</h3>')
        
        if calculo_cmc.get('resultados_conductor'):
            df_cond = pd.DataFrame(calculo_cmc['resultados_conductor']).T
            html_parts.append('<h5>Resultados Conductor</h5>')
            html_parts.append(df_cond.to_html(classes='table table-striped table-bordered', border=0))
        
        if calculo_cmc.get('resultados_guardia'):
            df_guard = pd.DataFrame(calculo_cmc['resultados_guardia']).T
            html_parts.append('<h5>Resultados Cable de Guardia</h5>')
            html_parts.append(df_guard.to_html(classes='table table-striped table-bordered', border=0))
        
        # Imágenes CMC
        html_parts.append('<h5>Gráficos de Flechas</h5>')
        for tipo_img in ['Combinado', 'Conductor', 'Guardia']:
            img_path = DATA_DIR / f"CMC_{tipo_img}.{hash_params}.png"
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                html_parts.append(f'<h6>{tipo_img}</h6>')
                html_parts.append(f'<img src="data:image/png;base64,{img_str}" style="width:100%;max-width:1000px;margin:10px 0">')
        
        # 2. DGE
        calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
        if calculo_dge:
            html_parts.append('<h3>2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)</h3>')
            
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
            
            html_parts.append(f'<pre style="background-color:#1e1e1e;color:#d4d4d4;padding:15px;border-radius:5px">{texto_dge}</pre>')
            
            # Imágenes DGE
            html_parts.append('<h5>Gráficos de Estructura</h5>')
            for tipo_img in ['Estructura', 'Cabezal']:
                img_path = DATA_DIR / f"{tipo_img}.{hash_params}.png"
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_str = base64.b64encode(f.read()).decode()
                    html_parts.append(f'<img src="data:image/png;base64,{img_str}" style="width:48%;margin:5px;display:inline-block">')
            
            # Memoria DGE
            if calculo_dge.get('memoria_calculo'):
                html_parts.append('<hr style="margin-top:30px">')
                html_parts.append('<h5>Memoria de Cálculo: Diseño Geométrico de Estructura</h5>')
                html_parts.append(f'<pre style="background-color:#1e1e1e;color:#d4d4d4;padding:15px;border-radius:5px;max-height:500px;overflow-y:auto">{calculo_dge["memoria_calculo"]}</pre>')
        
        # 3. DME
        calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
        if calculo_dme:
            html_parts.append('<h3>3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)</h3>')
            
            if calculo_dme.get('df_reacciones'):
                df_reacciones = pd.DataFrame.from_dict(calculo_dme['df_reacciones'], orient='index')
                html_parts.append('<h5>Reacciones en BASE</h5>')
                html_parts.append(df_reacciones.head(10).to_html(classes='table table-striped table-bordered', border=0))
            
            # Imágenes DME
            for tipo_img in ['Polar', 'Barras']:
                img_path = DATA_DIR / f"DME_{tipo_img}.{hash_params}.png"
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_str = base64.b64encode(f.read()).decode()
                    html_parts.append(f'<img src="data:image/png;base64,{img_str}" style="width:48%;margin:5px;display:inline-block">')
        
        # 4. Árboles
        calculo_arboles = CalculoCache.cargar_calculo_arboles(nombre_estructura)
        if calculo_arboles:
            html_parts.append('<h3>4. ÁRBOLES DE CARGA</h3>')
            
            html_parts.append('<div class="row">')
            for img_info in calculo_arboles.get('imagenes', [])[:6]:
                img_path = DATA_DIR / img_info['nombre']
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_str = base64.b64encode(f.read()).decode()
                    html_parts.append(f'''
                    <div class="col-md-4">
                        <div class="card mb-3">
                            <div class="card-header text-center"><h6>{img_info['hipotesis']}</h6></div>
                            <div class="card-body" style="padding:0.5rem">
                                <img src="data:image/png;base64,{img_str}" style="width:100%">
                            </div>
                        </div>
                    </div>
                    ''')
            html_parts.append('</div>')
            html_parts.append(f'<p>Total de hipótesis generadas: {len(calculo_arboles.get("imagenes", []))}</p>')
        
        # 5. SPH
        calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
        if calculo_sph:
            html_parts.append('<h3>5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)</h3>')
            
            resultados_sph = calculo_sph.get('resultados', {})
            if resultados_sph:
                html_parts.append('<div class="card mt-2"><div class="card-body">')
                html_parts.append('<h5>Postes Seleccionados:</h5><ul>')
                for i, poste in enumerate(resultados_sph.get('postes_seleccionados', []), 1):
                    html_parts.append(f'<li>Poste {i}: {poste.get("nombre", "N/A")} - {poste.get("longitud_total", 0):.1f}m</li>')
                html_parts.append('</ul>')
                html_parts.append(f'<p>Orientación: {resultados_sph.get("orientacion", "N/A")}</p>')
                html_parts.append(f'<p>Cantidad de postes: {resultados_sph.get("n_postes", 0)}</p>')
                html_parts.append('</div></div>')
                
                # Memoria SPH
                if calculo_sph.get('desarrollo_texto'):
                    html_parts.append('<hr style="margin-top:30px">')
                    html_parts.append('<h5>Memoria de Cálculo: Selección de Postes de Hormigón</h5>')
                    html_parts.append(f'<pre style="background-color:#1e1e1e;color:#d4d4d4;padding:15px;border-radius:5px;max-height:500px;overflow-y:auto">{calculo_sph["desarrollo_texto"]}</pre>')
        
        html_content = ''.join(html_parts)
        
        def dash_to_html_legacy(component, depth=0):
            try:
                if isinstance(component, str):
                    return component
                if isinstance(component, (int, float)):
                    return str(component)
                if isinstance(component, (list, tuple)):
                    return ''.join([dash_to_html(c, depth) for c in component])
                if component is None:
                    return ''
                
                # Manejar dcc.Graph - convertir a imagen
                if hasattr(component, 'type'):
                    type_str = str(component.type)
                    if 'Graph' in type_str:
                        props = getattr(component, 'props', {})
                        figure = props.get('figure')
                        if figure:
                            try:
                                import plotly.io as pio
                                img_bytes = pio.to_image(figure, format='png', width=1200, height=600)
                                img_b64 = base64.b64encode(img_bytes).decode()
                                return f'<img src="data:image/png;base64,{img_b64}" style="width:100%;max-width:1000px;margin:10px 0">'
                            except Exception as e:
                                print(f"Error convirtiendo gráfico: {e}")
                                return '<p>[Gráfico interactivo]</p>'
                        return ''
                
                # Obtener tag
                tag = 'div'
                if hasattr(component, 'type'):
                    tag_obj = component.type
                    if hasattr(tag_obj, '__name__'):
                        tag = tag_obj.__name__.lower()
                    elif isinstance(tag_obj, str):
                        tag = tag_obj.lower()
                
                props = getattr(component, 'props', {})
                children = props.get('children', '')
                class_name = props.get('className', '')
                style = props.get('style', {})
                src = props.get('src', '')
                
                attrs = []
                if class_name:
                    attrs.append(f'class="{class_name}"')
                if style:
                    style_str = ';'.join([f'{k.replace("_", "-")}:{v}' for k, v in style.items()])
                    attrs.append(f'style="{style_str}"')
                if src:
                    attrs.append(f'src="{src}"')
                
                attrs_str = ' ' + ' '.join(attrs) if attrs else ''
                children_html = dash_to_html(children, depth+1)
                
                return f'<{tag}{attrs_str}>{children_html}</{tag}>'
            except Exception as e:
                print(f"Error en dash_to_html (depth={depth}): {e}")
                return ''

        
        from datetime import datetime
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cálculo Completo - {titulo}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; background-color: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h3 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #95a5a6; padding-bottom: 5px; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        pre {{ background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .alert {{ padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .alert-success {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
        .info-box {{ background-color: #e7f3ff; padding: 20px; border-radius: 5px; margin-bottom: 30px; border-left: 4px solid #2196F3; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Cálculo Completo - {titulo}</h1>
        <div class="info-box">
            <p><strong>Tipo de Estructura:</strong> {tipo}</p>
            <p><strong>Tensión:</strong> {tension} kV</p>
            <p><strong>Fecha:</strong> {fecha}</p>
        </div>
        {html_content}
        <hr style="margin-top: 50px;">
        <p style="text-align: center; color: #7f8c8d; margin-top: 40px;">
            Generado por AGP - Análisis General de Postaciones
        </p>
    </div>
</body>
</html>"""
        
        nombre_archivo = f"{titulo}_calculo_completo.html"
        return dict(content=html_template, filename=nombre_archivo)
