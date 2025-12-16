"""Controlador para Calcular Todo - Carga resultados de cache de cada vista"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState
import base64


def _cargar_desde_cache(nombre_estructura, estructura_actual, state):
    """Carga resultados desde cache y los formatea igual que el cálculo nuevo"""
    from utils.calculo_cache import CalculoCache
    from config.app_config import DATA_DIR
    from pathlib import Path
    import pandas as pd
    from utils.format_helpers import formatear_resultados_cmc, formatear_dataframe_cmc
    
    resultados = [dbc.Alert("✅ Resultados cargados desde cache", color="info", className="mb-4")]
    
    # 1. CMC
    calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
    if calculo_cmc:
        resultados.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
        
        if calculo_cmc.get('resultados_conductor'):
            res_fmt = formatear_resultados_cmc(calculo_cmc['resultados_conductor'])
            df_cond = pd.DataFrame(res_fmt).T
            df_cond = formatear_dataframe_cmc(df_cond, calculo_cmc.get('estado_determinante_conductor'))
            resultados.append(html.H6("Resultados Conductor", className="mt-3", style={'fontSize': '0.9rem'}))
            resultados.append(html.Div(dbc.Table.from_dataframe(df_cond, striped=True, bordered=True, hover=True, size="sm"), style={'fontSize': '0.75rem', 'overflowX': 'auto'}, className="table-responsive"))
        
        if calculo_cmc.get('resultados_guardia'):
            res_fmt = formatear_resultados_cmc(calculo_cmc['resultados_guardia'])
            df_guard = pd.DataFrame(res_fmt).T
            df_guard = formatear_dataframe_cmc(df_guard, calculo_cmc.get('estado_determinante_guardia1'))
            resultados.append(html.H6("Resultados Cable de Guardia 1", className="mt-3", style={'fontSize': '0.9rem'}))
            resultados.append(html.Div(dbc.Table.from_dataframe(df_guard, striped=True, bordered=True, hover=True, size="sm"), style={'fontSize': '0.75rem', 'overflowX': 'auto'}, className="table-responsive"))
        
        if calculo_cmc.get('resultados_guardia2'):
            res_fmt = formatear_resultados_cmc(calculo_cmc['resultados_guardia2'])
            df_guard2 = pd.DataFrame(res_fmt).T
            df_guard2 = formatear_dataframe_cmc(df_guard2, calculo_cmc.get('estado_determinante_guardia2'))
            resultados.append(html.H6("Resultados Cable de Guardia 2", className="mt-3", style={'fontSize': '0.9rem'}))
            resultados.append(html.Div(dbc.Table.from_dataframe(df_guard2, striped=True, bordered=True, hover=True, size="sm"), style={'fontSize': '0.75rem', 'overflowX': 'auto'}, className="table-responsive"))
        
        # Output de consola
        if calculo_cmc.get('console_output'):
            resultados.append(html.Hr(className="mt-4"))
            resultados.append(html.H6("Output de Cálculo", className="mb-2"))
            resultados.append(html.Pre(calculo_cmc['console_output'], style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.75rem', 'maxHeight': '300px', 'overflowY': 'auto'}))
        
        # Gráficos CMC
        hash_params = calculo_cmc.get('hash_parametros')
        resultados.append(html.H5("Gráficos de Flechas", className="mt-4"))
        img_path = DATA_DIR / f"CMC_Combinado.{hash_params}.png"
        if img_path.exists():
            with open(img_path, 'rb') as f:
                img_str = base64.b64encode(f.read()).decode()
            resultados.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%', 'maxWidth': '1000px'}))
    
    # 2. DGE
    calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
    if calculo_dge:
        resultados.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
        
        dims = calculo_dge.get('dimensiones', {})
        nodes_key = calculo_dge.get('nodes_key', {})
        
        # Calcular flechas desde resultados CMC
        if calculo_cmc:
            fmax_conductor = max([r["flecha_vertical_m"] for r in calculo_cmc['resultados_conductor'].values()])
            fmax_guardia1 = max([r["flecha_vertical_m"] for r in calculo_cmc['resultados_guardia'].values()])
            if calculo_cmc.get('resultados_guardia2'):
                fmax_guardia2 = max([r["flecha_vertical_m"] for r in calculo_cmc['resultados_guardia2'].values()])
                resultados.append(html.H6(f"Flechas máximas: conductor={fmax_conductor:.2f}m, guardia1={fmax_guardia1:.2f}m, guardia2={fmax_guardia2:.2f}m", className="mb-3"))
            else:
                resultados.append(html.H6(f"Flechas máximas: conductor={fmax_conductor:.2f}m, guardia={fmax_guardia1:.2f}m", className="mb-3"))
        
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
        
        # Imágenes DGE
        hash_dge = calculo_dge.get('hash_parametros')
        resultados.append(html.H5("Gráficos de Estructura", className="mt-4"))
        for tipo in ['Estructura', 'Cabezal']:
            img_path = DATA_DIR / f"{tipo}.{hash_dge}.png"
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                resultados.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '48%', 'margin': '5px', 'display': 'inline-block'}))
        
        # Memoria DGE
        if calculo_dge.get('memoria_calculo'):
            resultados.append(html.Hr(className="mt-4"))
            resultados.append(html.H5("Memoria de Cálculo: Diseño Geométrico de Estructura", className="mb-3"))
            resultados.append(html.Pre(calculo_dge['memoria_calculo'], style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
    
    # 3. DME
    calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
    if calculo_dme:
        resultados.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
        
        if calculo_dme.get('df_reacciones'):
            df_reacciones = pd.DataFrame.from_dict(calculo_dme['df_reacciones'], orient='index').round(2)
            df_reacciones.index = [idx.split('_')[-2] if len(idx.split('_')) >= 2 else idx for idx in df_reacciones.index]
            df_reacciones.index.name = 'Hipótesis'
            df_reacciones = df_reacciones.reset_index()
            df_reacciones = df_reacciones[['Hipótesis', 'Reaccion_Fx_daN', 'Reaccion_Fy_daN', 'Reaccion_Fz_daN', 'Reaccion_Mx_daN_m', 'Reaccion_My_daN_m', 'Reaccion_Mz_daN_m', 'Tiro_X_daN', 'Tiro_Y_daN', 'Tiro_resultante_daN', 'Angulo_grados']]
            df_reacciones.columns = ['Hipótesis', 'Fx [daN]', 'Fy [daN]', 'Fz [daN]', 'Mx [daN·m]', 'My [daN·m]', 'Mz [daN·m]', 'Tiro_X [daN]', 'Tiro_Y [daN]', 'Tiro_Res [daN]', 'Ángulo [°]']
            resultados.append(html.H5("Reacciones en BASE", className="mt-3"))
            resultados.append(html.Div(dbc.Table.from_dataframe(df_reacciones.head(10), striped=True, bordered=True, hover=True, size="sm"), style={'fontSize': '0.75rem', 'overflowX': 'auto'}, className="table-responsive"))
        
        # Imágenes DME
        hash_dme = calculo_dme.get('hash_parametros')
        for tipo in ['Polar', 'Barras']:
            img_path = DATA_DIR / f"DME_{tipo}.{hash_dme}.png"
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                resultados.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '48%', 'margin': '5px', 'display': 'inline-block'}))
    
    # 4. Árboles
    calculo_arboles = CalculoCache.cargar_calculo_arboles(nombre_estructura)
    if calculo_arboles:
        resultados.append(html.H3("4. ÁRBOLES DE CARGA", className="mt-4"))
        
        # DataFrame de cargas
        if calculo_arboles.get('df_cargas_completo'):
            df_dict = calculo_arboles['df_cargas_completo']
            # Reconstruir MultiIndex desde levels y codes
            arrays = []
            for level_idx in range(len(df_dict['columns'])):
                level_values = df_dict['columns'][level_idx]
                codes = df_dict['column_codes'][level_idx]
                arrays.append([level_values[code] for code in codes])
            
            multi_idx = pd.MultiIndex.from_arrays(arrays)
            df_cargas = pd.DataFrame(df_dict['data'], columns=multi_idx)
            
            # Filtrar filas con al menos un valor != 0
            mask = (df_cargas.iloc[:, 2:].abs() > 0.001).any(axis=1)
            df_cargas = df_cargas[mask]
            
            # Formatear a 2 decimales
            df_cargas_fmt = df_cargas.round(2)
            
            # Crear HTML con estilos embebidos
            html_table = f'''<html><head><style>
                body {{ margin: 0; padding: 10px; background: white; font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; font-size: 11px; }}
                th, td {{ border: 1px solid #dee2e6; padding: 4px 6px; text-align: right; }}
                th {{ background-color: #f8f9fa; font-weight: 600; position: sticky; top: 0; z-index: 10; }}
                tr:nth-child(even) {{ background-color: #f8f9fa; }}
                tr:hover {{ background-color: #e9ecef; }}
            </style></head><body>{df_cargas_fmt.to_html(border=0, index=False)}</body></html>'''
            
            resultados.extend([
                html.H5("Cargas Aplicadas por Nodo", className="mt-4 mb-3"),
                html.Iframe(
                    srcDoc=html_table,
                    style={'width': '100%', 'height': '400px', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}
                )
            ])
        
        resultados.append(html.P(f"Total de hipótesis generadas: {len(calculo_arboles.get('imagenes', []))}", className="mb-3"))
        
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
            resultados.append(dbc.Row(imagenes_arboles))
            if len(calculo_arboles.get('imagenes', [])) > 6:
                resultados.append(html.P(f"Mostrando 6 de {len(calculo_arboles.get('imagenes', []))} hipótesis", className="text-muted mt-2"))
    
    # 5. SPH
    calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
    if calculo_sph:
        resultados.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
        
        resultados_sph = calculo_sph.get('resultados', {})
        if resultados_sph:
            config = resultados_sph.get('config_seleccionada', 'N/A')
            rc_adopt = resultados_sph.get('Rc_adopt', 0)
            dims = resultados_sph.get('dimensiones', {})
            ht = dims.get('Ht_comercial', 0)
            he = dims.get('He_final', 0)
            
            info_postes = [html.Li(f"Configuración: {config}"),
                          html.Li(f"Resistencia adoptada: {rc_adopt} daN"),
                          html.Li(f"Altura total: {ht:.1f} m"),
                          html.Li(f"Empotramiento: {he:.2f} m")]
            
            resultados.append(dbc.Card([
                dbc.CardBody([
                    html.H5("Resultado Selección de Poste:"),
                    html.Ul(info_postes)
                ])
            ], className="mt-2"))
            
            if calculo_sph.get('desarrollo_texto'):
                resultados.append(html.Hr(className="mt-4"))
                resultados.append(html.H5("Memoria de Cálculo: Selección de Postes de Hormigón", className="mb-3"))
                resultados.append(html.Pre(calculo_sph['desarrollo_texto'], style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
    
    return resultados, False, False


def register_callbacks(app):
    """Registrar callbacks de calcular todo"""
    
    state = AppState()
    
    @app.callback(
        Output("output-calcular-todo", "children", allow_duplicate=True),
        Output("btn-descargar-html-todo", "disabled", allow_duplicate=True),
        Output("btn-calcular-todo", "disabled", allow_duplicate=True),
        Input("btn-cargar-cache-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_desde_cache_callback(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            return _cargar_desde_cache(nombre_estructura, estructura_actual, state)
        except Exception as e:
            import traceback
            error_msg = f"Error cargando desde cache: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return [dbc.Alert(error_msg, color="danger")], True, False
    
    @app.callback(
        Output("output-calcular-todo", "children"),
        Output("btn-descargar-html-todo", "disabled"),
        Output("btn-calcular-todo", "disabled"),
        Input("btn-calcular-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def ejecutar_calculo_completo(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            from controllers.geometria_controller import ejecutar_calculo_cmc_automatico, ejecutar_calculo_dge
            from controllers.ejecutar_calculos import ejecutar_calculo_dme, ejecutar_calculo_arboles, ejecutar_calculo_sph
            from utils.calculo_cache import CalculoCache
            from config.app_config import DATA_DIR
            import pandas as pd
            
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            # SIEMPRE eliminar cache y recalcular (no usar cache en este botón)
            CalculoCache.eliminar_cache(nombre_estructura)
            
            resultados = []
            
            # 1. CMC
            resultados.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
            resultado_cmc = ejecutar_calculo_cmc_automatico(estructura_actual, state)
            if not resultado_cmc["exito"]:
                return [dbc.Alert(f"Error en CMC: {resultado_cmc['mensaje']}", color="danger")], True, False
            
            from utils.format_helpers import formatear_resultados_cmc, formatear_dataframe_cmc
            
            if state.calculo_mecanico.resultados_conductor:
                res_fmt = formatear_resultados_cmc(state.calculo_mecanico.resultados_conductor)
                df_cond = pd.DataFrame(res_fmt).T
                estado_det = df_cond['porcentaje_rotura'].idxmax() if 'porcentaje_rotura' in df_cond.columns else None
                df_cond = formatear_dataframe_cmc(df_cond, estado_det)
                resultados.append(html.H6("Resultados Conductor", className="mt-3", style={'fontSize': '0.9rem'}))
                resultados.append(html.Div(dbc.Table.from_dataframe(df_cond, striped=True, bordered=True, hover=True, size="sm"), style={'fontSize': '0.75rem', 'overflowX': 'auto'}, className="table-responsive"))
            
            if state.calculo_mecanico.resultados_guardia1:
                res_fmt = formatear_resultados_cmc(state.calculo_mecanico.resultados_guardia1)
                df_guard = pd.DataFrame(res_fmt).T
                estado_det = df_guard['porcentaje_rotura'].idxmax() if 'porcentaje_rotura' in df_guard.columns else None
                df_guard = formatear_dataframe_cmc(df_guard, estado_det)
                resultados.append(html.H6("Resultados Cable de Guardia 1", className="mt-3", style={'fontSize': '0.9rem'}))
                resultados.append(html.Div(dbc.Table.from_dataframe(df_guard, striped=True, bordered=True, hover=True, size="sm"), style={'fontSize': '0.75rem', 'overflowX': 'auto'}, className="table-responsive"))
            
            if state.calculo_mecanico.resultados_guardia2:
                res_fmt = formatear_resultados_cmc(state.calculo_mecanico.resultados_guardia2)
                df_guard2 = pd.DataFrame(res_fmt).T
                estado_det = df_guard2['porcentaje_rotura'].idxmax() if 'porcentaje_rotura' in df_guard2.columns else None
                df_guard2 = formatear_dataframe_cmc(df_guard2, estado_det)
                resultados.append(html.H6("Resultados Cable de Guardia 2", className="mt-3", style={'fontSize': '0.9rem'}))
                resultados.append(html.Div(dbc.Table.from_dataframe(df_guard2, striped=True, bordered=True, hover=True, size="sm"), style={'fontSize': '0.75rem', 'overflowX': 'auto'}, className="table-responsive"))
            
            # Cargar console output desde cache
            calculo_cmc_cache = CalculoCache.cargar_calculo_cmc(nombre_estructura)
            if calculo_cmc_cache and calculo_cmc_cache.get('console_output'):
                resultados.append(html.Hr(className="mt-4"))
                resultados.append(html.H6("Output de Cálculo", className="mb-2"))
                resultados.append(html.Pre(calculo_cmc_cache['console_output'], style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.75rem', 'maxHeight': '300px', 'overflowY': 'auto'}))
            
            # Gráficos de flechas
            from utils.plot_flechas import crear_grafico_flechas
            try:
                fig_combinado, fig_conductor, fig_guardia = crear_grafico_flechas(
                    state.calculo_mecanico.resultados_conductor,
                    state.calculo_mecanico.resultados_guardia1,
                    estructura_actual.get('L_vano')
                )
                resultados.append(html.H5("Gráficos de Flechas", className="mt-4"))
                resultados.append(dcc.Graph(figure=fig_combinado, config={'displayModeBar': False}, style={'height': '400px'}))
            except Exception as e:
                print(f"Error generando gráficos de flechas: {e}")
            
            # 2. DGE
            resultados.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
            resultado_dge = ejecutar_calculo_dge(estructura_actual, state)
            if not resultado_dge["exito"]:
                return [dbc.Alert(f"Error en DGE: {resultado_dge['mensaje']}", color="danger")], True, False
            
            dims = resultado_dge["dimensiones"]
            nodes_key = resultado_dge["nodes_key"]
            memoria_dge = resultado_dge["memoria_calculo"]
            fmax_conductor = resultado_dge["fmax_conductor"]
            fmax_guardia = resultado_dge["fmax_guardia"]
            resultados.append(html.H6(f"Flechas máximas: conductor={fmax_conductor:.2f}m, guardia={fmax_guardia:.2f}m", className="mb-3"))
            
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
            
            resultados.append(html.Hr(className="mt-4"))
            resultados.append(html.H5("Memoria de Cálculo: Diseño Geométrico de Estructura", className="mb-3"))
            resultados.append(html.Pre(memoria_dge, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
            
            # 3. DME
            resultados.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
            resultado_dme = ejecutar_calculo_dme(estructura_actual, state)
            if not resultado_dme["exito"]:
                return [dbc.Alert(f"Error en DME: {resultado_dme['mensaje']}", color="danger")], True, False
            
            df_reacciones = resultado_dme["df_reacciones"]
            if df_reacciones is not None and not df_reacciones.empty:
                df_reacciones_display = df_reacciones.copy().round(2)
                df_reacciones_display.index = [idx.split('_')[-2] if len(idx.split('_')) >= 2 else idx for idx in df_reacciones_display.index]
                df_reacciones_display.index.name = 'Hipótesis'
                df_reacciones_display = df_reacciones_display.reset_index()
                df_reacciones_display = df_reacciones_display[['Hipótesis', 'Reaccion_Fx_daN', 'Reaccion_Fy_daN', 'Reaccion_Fz_daN', 'Reaccion_Mx_daN_m', 'Reaccion_My_daN_m', 'Reaccion_Mz_daN_m', 'Tiro_X_daN', 'Tiro_Y_daN', 'Tiro_resultante_daN', 'Angulo_grados']]
                df_reacciones_display.columns = ['Hipótesis', 'Fx [daN]', 'Fy [daN]', 'Fz [daN]', 'Mx [daN·m]', 'My [daN·m]', 'Mz [daN·m]', 'Tiro_X [daN]', 'Tiro_Y [daN]', 'Tiro_Res [daN]', 'Ángulo [°]']
                resultados.append(html.H5("Reacciones en BASE", className="mt-3"))
                resultados.append(html.Div(dbc.Table.from_dataframe(df_reacciones_display.head(10), striped=True, bordered=True, hover=True, size="sm"), style={'fontSize': '0.75rem', 'overflowX': 'auto'}, className="table-responsive"))
            
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
            resultado_arboles = ejecutar_calculo_arboles(estructura_actual, state)
            if resultado_arboles['exito']:
                # DataFrame de cargas
                if state.calculo_objetos.estructura_mecanica and state.calculo_objetos.estructura_mecanica.df_cargas_completo is not None:
                    df_cargas = state.calculo_objetos.estructura_mecanica.df_cargas_completo.copy()
                    mask = (df_cargas.iloc[:, 2:].abs() > 0.001).any(axis=1)
                    df_cargas = df_cargas[mask]
                    
                    # Formatear a 2 decimales
                    df_cargas_fmt = df_cargas.round(2)
                    
                    # Crear HTML con estilos embebidos
                    html_table = f'''<html><head><style>
                        body {{ margin: 0; padding: 10px; background: white; font-family: Arial, sans-serif; }}
                        table {{ border-collapse: collapse; width: 100%; font-size: 11px; }}
                        th, td {{ border: 1px solid #dee2e6; padding: 4px 6px; text-align: right; }}
                        th {{ background-color: #f8f9fa; font-weight: 600; position: sticky; top: 0; z-index: 10; }}
                        tr:nth-child(even) {{ background-color: #f8f9fa; }}
                        tr:hover {{ background-color: #e9ecef; }}
                    </style></head><body>{df_cargas_fmt.to_html(border=0, index=False)}</body></html>'''
                    
                    resultados.extend([
                        html.H5("Cargas Aplicadas por Nodo", className="mt-4 mb-3"),
                        html.Iframe(
                            srcDoc=html_table,
                            style={'width': '100%', 'height': '400px', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}
                        )
                    ])
                
                resultados.append(html.P(f"Total de hipótesis generadas: {len(resultado_arboles['imagenes'])}", className="mb-3"))
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
                    if len(resultado_arboles['imagenes']) > 6:
                        resultados.append(html.P(f"Mostrando 6 de {len(resultado_arboles['imagenes'])} hipótesis", className="text-muted mt-2"))
            else:
                resultados.append(dbc.Alert(f"⚠️ {resultado_arboles.get('mensaje', 'Error en árboles')}", color="warning"))
            
            # 5. SPH
            resultados.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
            try:
                resultado_sph = ejecutar_calculo_sph(estructura_actual, state)
                if resultado_sph["exito"]:
                    resultados_sph = resultado_sph["resultados"]
                    desarrollo_texto = resultado_sph.get("desarrollo_texto", "")
                    
                    # SPH retorna config_seleccionada, dimensiones, Rc_adopt, etc.
                    config = resultados_sph.get('config_seleccionada', 'N/A')
                    rc_adopt = resultados_sph.get('Rc_adopt', 0)
                    dims = resultados_sph.get('dimensiones', {})
                    ht = dims.get('Ht_comercial', 0)
                    he = dims.get('He_final', 0)
                    
                    info_postes = [html.Li(f"Configuración: {config}"),
                                  html.Li(f"Resistencia adoptada: {rc_adopt} daN"),
                                  html.Li(f"Altura total: {ht:.1f} m"),
                                  html.Li(f"Empotramiento: {he:.2f} m")]
                    
                    if info_postes:
                        resultados.append(dbc.Card([
                            dbc.CardBody([
                                html.H5("Resultado Selección de Poste:"),
                                html.Ul(info_postes)
                            ])
                        ], className="mt-2"))
                        
                        if desarrollo_texto:
                            resultados.append(html.Hr(className="mt-4"))
                            resultados.append(html.H5("Memoria de Cálculo SPH", className="mb-3"))
                            resultados.append(html.Pre(desarrollo_texto, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '15px', 'borderRadius': '5px', 'fontSize': '0.8rem', 'whiteSpace': 'pre', 'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'}))
                    else:
                        resultados.append(dbc.Alert("No se encontraron resultados SPH", color="warning"))
                else:
                    resultados.append(dbc.Alert(f"Error en SPH: {resultado_sph.get('mensaje', 'Error desconocido')}", color="warning"))
            except Exception as e:
                import traceback
                resultados.append(dbc.Alert(f"Error en SPH: {str(e)}\n{traceback.format_exc()}", color="danger"))
            
            resultados.insert(0, dbc.Alert("✅ CÁLCULO COMPLETO FINALIZADO EXITOSAMENTE", color="success", className="mb-4"))
            CalculoCache.guardar_calculo_todo(nombre_estructura, estructura_actual, {'componentes': resultados})
            
            return resultados, False, False
            
        except Exception as e:
            import traceback
            error_msg = f"Error en cálculo completo: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return [dbc.Alert(error_msg, color="danger")], True, False

    
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
            df_cond = pd.DataFrame(calculo_cmc['resultados_conductor']).T.round(2)
            html_parts.append('<h5>Resultados Conductor</h5>')
            html_parts.append(df_cond.to_html(classes='table table-striped table-bordered', border=0))
        
        if calculo_cmc.get('resultados_guardia'):
            df_guard = pd.DataFrame(calculo_cmc['resultados_guardia']).T.round(2)
            html_parts.append('<h5>Resultados Cable de Guardia 1</h5>')
            html_parts.append(df_guard.to_html(classes='table table-striped table-bordered', border=0))
        
        if calculo_cmc.get('resultados_guardia2'):
            df_guard2 = pd.DataFrame(calculo_cmc['resultados_guardia2']).T.round(2)
            html_parts.append('<h5>Resultados Cable de Guardia 2</h5>')
            html_parts.append(df_guard2.to_html(classes='table table-striped table-bordered', border=0))
        
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
                df_reacciones = pd.DataFrame.from_dict(calculo_dme['df_reacciones'], orient='index').round(2)
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
