"""Controlador de Árboles de Carga"""

import dash
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc
import base64
from models.app_state import AppState
from utils.arboles_carga import generar_arboles_carga
from utils.calculo_cache import CalculoCache
from config.app_config import DATA_DIR


def register_callbacks(app):
    """Registrar callbacks de árboles de carga"""
    
    state = AppState()
    
    @app.callback(
        Output("resultados-arboles-carga", "children", allow_duplicate=True),
        Input("url", "pathname"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_arboles_desde_cache(pathname, estructura_actual):
        """Carga árboles desde cache al entrar a la vista"""
        if pathname != "/arboles-carga":
            raise dash.exceptions.PreventUpdate
        
        if not estructura_actual:
            raise dash.exceptions.PreventUpdate
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        calculo_arboles = CalculoCache.cargar_calculo_arboles(nombre_estructura)
        
        if not calculo_arboles:
            return html.Div([
                dbc.Alert("No hay árboles de carga calculados. Haga clic en 'Generar Árboles' para calcular.", color="info")
            ])
        
        print(f"🔄 Cargando árboles desde cache para {nombre_estructura}")
        
        imagenes_html = [
            dbc.Alert("✓ Árboles cargados desde cache", color="info", className="mb-3")
        ]
        
        # Cargar DataFrame de cargas
        if calculo_arboles.get('df_cargas_completo'):
            import pandas as pd
            df_dict = calculo_arboles['df_cargas_completo']
            print(f"✅ DataFrame encontrado en cache")
            
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
        
        # Cargar imágenes
        imagenes_cards = []
        for img_info in calculo_arboles.get('imagenes', []):
            img_path = DATA_DIR / img_info['nombre']
            if img_path.exists():
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
        
        if imagenes_cards:
            imagenes_html.extend([
                html.H5("Árboles de Carga por Hipótesis", className="mt-4 mb-3"),
                dbc.Row(imagenes_cards, justify="center")
            ])
        
        return html.Div(imagenes_html)
    
    @app.callback(
        Output("resultados-arboles-carga", "children"),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-generar-arboles", "n_clicks"),
        State("param-zoom-arboles", "value"),
        State("param-escala-flechas", "value"),
        State("param-grosor-lineas", "value"),
        State("param-fontsize-nodos", "value"),
        State("param-fontsize-flechas", "value"),
        State("param-mostrar-nodos", "value"),
        State("param-mostrar-sismo", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def generar_arboles_callback(n_clicks, zoom, escala, grosor, fontsize_nodos, fontsize_flechas, mostrar_nodos, mostrar_sismo, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
            from EstructuraAEA_Geometria import EstructuraAEA_Geometria
            from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
            from HipotesisMaestro import hipotesis_maestro
            
            # ENCADENAMIENTO AUTOMÁTICO: CMC -> DGE -> DME
            # 1. Verificar/ejecutar CMC
            if not state.calculo_mecanico.resultados_conductor or not state.calculo_mecanico.resultados_guardia1:
                calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
                if calculo_cmc:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_cmc, estructura_actual)
                    if vigente:
                        import pandas as pd
                        state.calculo_mecanico.resultados_conductor = calculo_cmc.get('resultados_conductor', {})
                        state.calculo_mecanico.resultados_guardia1 = calculo_cmc.get('resultados_guardia', {})
                        state.calculo_mecanico.resultados_guardia2 = calculo_cmc.get('resultados_guardia2', None)
                        if calculo_cmc.get('df_cargas_totales'):
                            state.calculo_mecanico.df_cargas_totales = pd.DataFrame(calculo_cmc['df_cargas_totales'])
                        if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                            state.calculo_objetos.crear_todos_objetos(estructura_actual)
                    else:
                        resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                        if not resultado_auto["exito"]:
                            return (html.Div(), True, "Error", f"CMC automático: {resultado_auto['mensaje']}", "danger", "danger")
                else:
                    resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                    if not resultado_auto["exito"]:
                        return (html.Div(), True, "Error", f"CMC automático: {resultado_auto['mensaje']}", "danger", "danger")
            
            # 2. Verificar/ejecutar DGE
            if not state.calculo_objetos.estructura_geometria:
                calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
                if calculo_dge:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_dge, estructura_actual)
                    if not vigente:
                        calculo_dge = None
                
                if not calculo_dge:
                    if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                        state.calculo_objetos.crear_todos_objetos(estructura_actual)
                    
                    fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
                    fmax_guardia1 = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia1.values()])
                    fmax_guardia2 = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia2.values()]) if state.calculo_mecanico.resultados_guardia2 else fmax_guardia1
                    fmax_guardia = max(fmax_guardia1, fmax_guardia2)
                    
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
                else:
                    # Cargar desde cache y reconstruir geometría
                    if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                        state.calculo_objetos.crear_todos_objetos(estructura_actual)
                    
                    fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
                    fmax_guardia1 = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia1.values()])
                    fmax_guardia2 = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia2.values()]) if state.calculo_mecanico.resultados_guardia2 else fmax_guardia1
                    fmax_guardia = max(fmax_guardia1, fmax_guardia2)
                    
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
            
            # 3. Verificar/ejecutar DME
            if not state.calculo_objetos.estructura_mecanica:
                estructura_mecanica = EstructuraAEA_Mecanica(state.calculo_objetos.estructura_geometria)
                if state.calculo_objetos.cable_guardia2:
                    state.calculo_objetos.estructura_geometria.cable_guardia2 = state.calculo_objetos.cable_guardia2
                estructura_mecanica.asignar_cargas_hipotesis(
                    state.calculo_mecanico.df_cargas_totales,
                    state.calculo_mecanico.resultados_conductor,
                    state.calculo_mecanico.resultados_guardia1,
                    estructura_actual.get('L_vano'),
                    hipotesis_maestro,
                    estructura_actual.get('t_hielo'),
                    hipotesis_a_incluir="Todas",
                    resultados_guardia2=state.calculo_mecanico.resultados_guardia2
                )
                
                nodes_key = state.calculo_objetos.estructura_geometria.nodes_key
                if "TOP" in nodes_key:
                    nodo_cima = "TOP"
                elif "HG1" in nodes_key:
                    nodo_cima = "HG1"
                else:
                    nodo_cima = max(nodes_key.items(), key=lambda x: x[1][2])[0]
                
                estructura_mecanica.calcular_reacciones_tiros_cima(
                    nodo_apoyo="BASE",
                    nodo_cima=nodo_cima
                )
                
                # Crear DataFrame de cargas completo
                estructura_mecanica.generar_dataframe_cargas()
                
                state.calculo_objetos.estructura_mecanica = estructura_mecanica
            
            estructura_poo = state.calculo_objetos.estructura_mecanica
            

            
            # Generar árboles
            resultado = generar_arboles_carga(
                estructura_poo,
                estructura_actual,
                zoom=float(zoom),
                escala_flecha=float(escala),
                grosor_linea=float(grosor),
                mostrar_nodos=bool(mostrar_nodos),
                fontsize_nodos=int(fontsize_nodos),
                fontsize_flechas=int(fontsize_flechas),
                mostrar_sismo=bool(mostrar_sismo)
            )
            
            if not resultado['exito']:
                return (
                    html.Div(),
                    True, "Error",
                    resultado['mensaje'],
                    "danger", "danger"
                )
            
            # PERSISTENCIA: Guardar en cache
            print(f"💾 Guardando en cache. DataFrame: {estructura_poo.df_cargas_completo is not None}")
            if estructura_poo.df_cargas_completo is not None:
                print(f"   Shape: {estructura_poo.df_cargas_completo.shape}")
            CalculoCache.guardar_calculo_arboles(nombre_estructura, estructura_actual, resultado['imagenes'], estructura_poo.df_cargas_completo)
            
            # Crear HTML con las imágenes generadas en dos columnas
            imagenes_html = [
                dbc.Alert(f"✓ {resultado['mensaje']}", color="success", className="mb-3")
            ]
            
            # Agregar DataFrame de cargas por nodo
            if estructura_poo.df_cargas_completo is not None:
                import pandas as pd
                df_cargas = estructura_poo.df_cargas_completo.copy()
                
                # Filtrar filas que tienen al menos un valor != 0 (excepto primeras 2 columnas)
                mask = (df_cargas.iloc[:, 2:].abs() > 0.001).any(axis=1)
                df_cargas = df_cargas[mask]
                
                # Formatear floats a 2 decimales
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
                
                altura_tabla = min(max(len(df_cargas) * 25 + 80, 150), 600)
                
                imagenes_html.extend([
                    html.H5("Cargas Aplicadas por Nodo", className="mt-4 mb-3"),
                    html.Iframe(
                        srcDoc=html_table,
                        style={'width': '100%', 'height': f'{altura_tabla}px', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}
                    )
                ])
            
            imagenes_cards = []
            for img_info in resultado['imagenes']:
                # Leer imagen y convertir a base64
                with open(img_info['ruta'], 'rb') as f:
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
            
            imagenes_html.extend([
                html.H5("Árboles de Carga por Hipótesis", className="mt-4 mb-3"),
                dbc.Row(imagenes_cards, justify="center")
            ])
            
            return (
                html.Div(imagenes_html),
                True, "Éxito",
                f"Se generaron {len(resultado['imagenes'])} árboles de carga",
                "success", "success"
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return (
                html.Div(),
                True, "Error",
                f"Error generando árboles: {str(e)}",
                "danger", "danger"
            )
