"""Controlador para Selección de Postes de Hormigón"""

import io
import sys
import dash
from dash import Input, Output, State
from models.app_state import AppState
from utils.calculo_cache import CalculoCache
import hashlib
import json

def register_callbacks(app):
    """Registrar callbacks de selección de postes"""
    
    state = AppState()
    
    # Callback para cargar resultados guardados
    @app.callback(
        Output("resultados-sph", "children", allow_duplicate=True),
        Input("store-calculo-sph", "data"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_resultados_sph(calculo_guardado, estructura_actual):
        """Cargar resultados guardados al iniciar la vista"""
        print(f"DEBUG SPH: Callback cargar_resultados_sph ejecutado. Tiene datos: {calculo_guardado is not None}")
        if not calculo_guardado:
            return []
        from components.vista_seleccion_poste import _crear_area_resultados
        return _crear_area_resultados(calculo_guardado, estructura_actual)
    
    @app.callback(
        [Output("estructura-actual", "data", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-guardar-params-sph", "n_clicks"),
        [State("slider-forzar-n-postes", "value"),
         State("select-forzar-orientacion", "value"),
         State("select-prioridad-dimensionado", "value"),
         State("input-ancho-cruceta", "value"),
         State("estructura-actual", "data")],
        prevent_initial_call=True
    )
    def guardar_parametros_sph(n_clicks, forzar_n, orientacion, prioridad, ancho_cruceta, estructura_actual):
        """Guardar parámetros de selección de postes"""
        
        if not n_clicks or not estructura_actual:
            return estructura_actual, False, "", "", "info"
        
        # Actualizar parámetros
        estructura_actual['FORZAR_N_POSTES'] = forzar_n
        estructura_actual['FORZAR_ORIENTACION'] = orientacion
        estructura_actual['PRIORIDAD_DIMENSIONADO'] = prioridad
        estructura_actual['ANCHO_CRUCETA'] = ancho_cruceta
        
        # Guardar en archivo
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        archivo = state.estructura_manager.data_dir / f"{nombre_estructura}.estructura.json"
        state.estructura_manager.guardar_estructura(estructura_actual, archivo)
        state.estructura_manager.guardar_estructura(estructura_actual, state.archivo_actual)
        
        return (
            estructura_actual,
            True,
            "Parámetros de selección de postes guardados correctamente",
            "Éxito",
            "success"
        )
    
    @app.callback(
        [Output("store-calculo-sph", "data"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-calcular-sph", "n_clicks"),
        [State("slider-forzar-n-postes", "value"),
         State("select-forzar-orientacion", "value"),
         State("select-prioridad-dimensionado", "value"),
         State("input-ancho-cruceta", "value"),
         State("estructura-actual", "data")],
        prevent_initial_call=True
    )
    def calcular_seleccion_poste(n_clicks, forzar_n, orientacion, prioridad, ancho_cruceta, estructura_actual):
        """Ejecutar cálculo de selección de postes con encadenamiento automático"""
        
        if not n_clicks or not estructura_actual:
            return dash.no_update, False, "", "", "info"
        
        try:
            from PostesHormigon import PostesHormigon
            from EstructuraAEA_Geometria import EstructuraAEA_Geometria
            from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
            from HipotesisMaestro_Especial import hipotesis_maestro
            from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
            import pandas as pd
            
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            # PASO 1: Auto-ejecutar CMC si no existe
            tiene_guardia1 = bool(state.calculo_mecanico.resultados_guardia1)
            tiene_guardia2 = bool(getattr(state.calculo_mecanico, 'resultados_guardia2', None))
            
            if not state.calculo_mecanico.resultados_conductor or not tiene_guardia1:
                calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
                if calculo_cmc:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_cmc, estructura_actual)
                    if vigente:
                        state.calculo_mecanico.resultados_conductor = calculo_cmc.get('resultados_conductor', {})
                        state.calculo_mecanico.resultados_guardia1 = calculo_cmc.get('resultados_guardia1', {})
                        if calculo_cmc.get('resultados_guardia2'):
                            state.calculo_mecanico.resultados_guardia2 = calculo_cmc.get('resultados_guardia2', {})
                        if calculo_cmc.get('df_cargas_totales'):
                            state.calculo_mecanico.df_cargas_totales = pd.DataFrame(calculo_cmc['df_cargas_totales'])
                        if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                            state.calculo_objetos.crear_todos_objetos(estructura_actual)
                    else:
                        resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                        if not resultado_auto["exito"]:
                            return None, True, f"Error en CMC: {resultado_auto['mensaje']}", "Error", "danger"
                else:
                    resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                    if not resultado_auto["exito"]:
                        return None, True, f"Error en CMC: {resultado_auto['mensaje']}", "Error", "danger"
            
            # PASO 2: Auto-ejecutar DGE si no existe
            if not state.calculo_objetos.estructura_geometria:
                if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                    state.calculo_objetos.crear_todos_objetos(estructura_actual)
                
                fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
                flechas_guardia = [r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia1.values()]
                if hasattr(state.calculo_mecanico, 'resultados_guardia2') and state.calculo_mecanico.resultados_guardia2:
                    flechas_guardia.extend([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia2.values()])
                fmax_guardia = max(flechas_guardia) if flechas_guardia else 0.0
                
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
            
            # PASO 3: Auto-ejecutar DME si no existe
            if not state.calculo_objetos.estructura_mecanica:
                estructura_mecanica = EstructuraAEA_Mecanica(state.calculo_objetos.estructura_geometria)
                # Combinar resultados de guardia para compatibilidad
                resultados_guardia_combinados = state.calculo_mecanico.resultados_guardia1.copy()
                if hasattr(state.calculo_mecanico, 'resultados_guardia2') and state.calculo_mecanico.resultados_guardia2:
                    resultados_guardia_combinados.update(state.calculo_mecanico.resultados_guardia2)
                
                estructura_mecanica.asignar_cargas_hipotesis(
                    state.calculo_mecanico.df_cargas_totales,
                    state.calculo_mecanico.resultados_conductor,
                    resultados_guardia_combinados,
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
                
                estructura_mecanica.calcular_reacciones_tiros_cima(nodo_apoyo="BASE", nodo_cima=nodo_cima)
                state.calculo_objetos.estructura_mecanica = estructura_mecanica
            
            # Recuperar objetos
            geometria = state.calculo_objetos.estructura_geometria
            mecanica = state.calculo_objetos.estructura_mecanica
            
            # Crear objeto PostesHormigon y calcular
            postes = PostesHormigon()
            
            # Capturar salida de imprimir_desarrollo
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            
            resultados = postes.calcular_seleccion_postes(
                geometria=geometria,
                mecanica=mecanica,
                FORZAR_N_POSTES=forzar_n,
                FORZAR_ORIENTACION=orientacion,
                ANCHO_CRUCETA=ancho_cruceta,
                PRIORIDAD_DIMENSIONADO=prioridad
            )
            
            postes.imprimir_desarrollo_seleccion_postes()
            
            desarrollo_texto = buffer.getvalue()
            sys.stdout = old_stdout
            
            # Preparar datos para guardar (remover objetos no serializables)
            resultados_serializables = resultados.copy()
            if 'geometria' in resultados_serializables:
                del resultados_serializables['geometria']
            if 'mecanica' in resultados_serializables:
                del resultados_serializables['mecanica']
            
            calculo_sph = {
                'parametros': estructura_actual,
                'resultados': resultados_serializables,
                'desarrollo_texto': desarrollo_texto
            }
            
            # Guardar cálculo (el hash se calcula dentro de guardar_calculo_sph)
            CalculoCache.guardar_calculo_sph(nombre_estructura, estructura_actual, resultados_serializables, desarrollo_texto)
            
            return (
                calculo_sph,
                True,
                "Cálculo de selección de postes completado exitosamente",
                "Éxito",
                "success"
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return (
                None,
                True,
                f"Error en el cálculo: {str(e)}",
                "Error",
                "danger"
            )
