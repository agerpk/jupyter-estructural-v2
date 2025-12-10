"""Controlador para Calcular Todo - Carga resultados de cache de cada vista"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de calcular todo"""
    
    state = AppState()
    
    @app.callback(
        Output("output-calcular-todo", "children"),
        Output("btn-descargar-html-todo", "disabled"),
        Input("btn-calcular-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def ejecutar_calculo_completo(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
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
            
            resultados.append(dbc.Alert("✅ CMC completado", color="success"))
            
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
            
            # 2. DGE - Ejecutar lógica directamente
            resultados.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
            from EstructuraAEA_Geometria import EstructuraAEA_Geometria
            
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
            resultados.append(dbc.Alert(f"✅ DGE completado: {len(nodes_key)} nodos creados", color="success"))
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
            
            # Memoria de cálculo DGE
            resultados.append(html.Hr(className="mt-4"))
            resultados.append(html.H5("Memoria de Cálculo: Diseño Geométrico de Estructura", className="mb-3"))
            resultados.append(html.Pre(memoria_dge, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
            
            calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
            if calculo_dge:
                hash_dge = calculo_dge.get('hash_parametros')
                for tipo in ['Estructura', 'Cabezal']:
                    img_path = DATA_DIR / f"{tipo}.{hash_dge}.png"
                    if img_path.exists():
                        with open(img_path, 'rb') as f:
                            img_str = base64.b64encode(f.read()).decode()
                        resultados.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '48%', 'margin': '5px', 'display': 'inline-block'}))
            
            # 3. DME - Ejecutar lógica directamente
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
            resultados.append(dbc.Alert("✅ DME completado", color="success"))
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
            
            # 4. Árboles
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
                    resultados.append(dbc.Alert(f"✅ {resultado_arboles['mensaje']}", color="success"))
                    
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
            
            # 5. SPH
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
                
                resultados.append(dbc.Alert("✅ SPH completado", color="success"))
                
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
            
            return resultados, False
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return [dbc.Alert(f"Error en cálculo completo: {str(e)}", color="danger")], True
    
    @app.callback(
        Output("download-html-completo", "data"),
        Input("btn-descargar-html-todo", "n_clicks"),
        State("output-calcular-todo", "children"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def descargar_html_completo(n_clicks, output_children, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        titulo = estructura_actual.get("TITULO", "estructura")
        tipo = estructura_actual.get("TIPO_ESTRUCTURA", "")
        tension = estructura_actual.get("TENSION", "")
        
        def dash_to_html(component):
            if isinstance(component, str):
                return component
            if isinstance(component, (list, tuple)):
                return ''.join([dash_to_html(c) for c in component])
            if component is None:
                return ''
            
            tag = getattr(component, 'type', 'div')
            if hasattr(tag, '__name__'):
                tag = tag.__name__.lower()
            
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
            children_html = dash_to_html(children)
            
            return f'<{tag}{attrs_str}>{children_html}</{tag}>'
        
        html_content = dash_to_html(output_children)
        
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
            Generado por Sistema de Cálculo Estructural
        </p>
    </div>
</body>
</html>"""
        
        nombre_archivo = f"{titulo}_calculo_completo.html"
        return dict(content=html_template, filename=nombre_archivo)
