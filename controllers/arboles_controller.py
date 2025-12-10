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
        State("param-mostrar-nodos", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def generar_arboles_callback(n_clicks, zoom, escala, grosor, mostrar_nodos, estructura_actual):
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
            if not state.calculo_mecanico.resultados_conductor or not state.calculo_mecanico.resultados_guardia:
                calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
                if calculo_cmc:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_cmc, estructura_actual)
                    if vigente:
                        import pandas as pd
                        state.calculo_mecanico.resultados_conductor = calculo_cmc.get('resultados_conductor', {})
                        state.calculo_mecanico.resultados_guardia = calculo_cmc.get('resultados_guardia', {})
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
                else:
                    # Cargar desde cache y reconstruir geometría
                    if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                        state.calculo_objetos.crear_todos_objetos(estructura_actual)
                    
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
            
            # 3. Verificar/ejecutar DME
            if not state.calculo_objetos.estructura_mecanica:
                estructura_mecanica = EstructuraAEA_Mecanica(state.calculo_objetos.estructura_geometria)
                estructura_mecanica.asignar_cargas_hipotesis(
                    state.calculo_mecanico.df_cargas_totales,
                    state.calculo_mecanico.resultados_conductor,
                    state.calculo_mecanico.resultados_guardia,
                    estructura_actual.get('L_vano'),
                    hipotesis_maestro,
                    estructura_actual.get('t_hielo')
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
                
                state.calculo_objetos.estructura_mecanica = estructura_mecanica
            
            estructura_poo = state.calculo_objetos.estructura_mecanica
            
            # Generar árboles
            resultado = generar_arboles_carga(
                estructura_poo,
                estructura_actual,
                zoom=float(zoom),
                escala_flecha=float(escala),
                grosor_linea=float(grosor),
                mostrar_nodos=bool(mostrar_nodos)
            )
            
            if not resultado['exito']:
                return (
                    html.Div(),
                    True, "Error",
                    resultado['mensaje'],
                    "danger", "danger"
                )
            
            # PERSISTENCIA: Guardar en cache
            CalculoCache.guardar_calculo_arboles(nombre_estructura, estructura_actual, resultado['imagenes'])
            
            # Crear HTML con las imágenes generadas
            imagenes_html = [
                dbc.Alert(f"✓ {resultado['mensaje']}", color="success", className="mb-3")
            ]
            
            for img_info in resultado['imagenes']:
                # Leer imagen y convertir a base64
                with open(img_info['ruta'], 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                
                imagenes_html.extend([
                    html.H5(f"Hipótesis: {img_info['hipotesis']}", className="mt-4"),
                    html.P(f"Archivo: {img_info['nombre']}", className="text-muted small"),
                    html.Img(src=f'data:image/png;base64,{img_str}', 
                            style={'width': '100%', 'maxWidth': '1200px'}, 
                            className="mb-4")
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
