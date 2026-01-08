"""
Controller para Analisis Estatico de Esfuerzos (AEE)
"""

import dash
from dash import Input, Output, State, no_update
import threading

def register_callbacks(app):
    """Registrar callbacks del controller AEE"""
    
    @app.callback(
        [Output("estructura-actual", "data", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-guardar-params-aee", "n_clicks"),
        [State("estructura-actual", "data"),
         State("aee-graficos-3d", "value"),
         State("aee-n-corta", "value"),
         State("aee-n-larga", "value"),
         State("aee-percentil", "value"),
         State("aee-diagramas", "value")],
        prevent_initial_call=True
    )
    def guardar_parametros_aee(n_clicks, estructura_actual, graficos_3d, n_corta, n_larga, percentil, diagramas):
        """Guarda parametros AEE en estructura"""
        
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        try:
            from models.app_state import AppState
            from config.app_config import DATA_DIR
            
            state = AppState()
            ruta_actual = state.get_estructura_actual_path()
            
            # Recargar estructura
            estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
            
            # Actualizar parametros AEE
            if 'AnalisisEstaticoEsfuerzos' not in estructura_actual:
                estructura_actual['AnalisisEstaticoEsfuerzos'] = {}
            
            estructura_actual['AnalisisEstaticoEsfuerzos']['GRAFICOS_3D_AEE'] = graficos_3d
            estructura_actual['AnalisisEstaticoEsfuerzos']['n_segmentar_conexion_corta'] = n_corta
            estructura_actual['AnalisisEstaticoEsfuerzos']['n_segmentar_conexion_larga'] = n_larga
            estructura_actual['AnalisisEstaticoEsfuerzos']['percentil_separacion_corta_larga'] = percentil
            
            # Actualizar diagramas activos
            estructura_actual['AnalisisEstaticoEsfuerzos']['DIAGRAMAS_ACTIVOS'] = {
                'MQNT': 'MQNT' in diagramas,
                'MRT': 'MRT' in diagramas,
                'MFE': 'MFE' in diagramas
            }
            
            # Guardar estructura
            state.estructura_manager.guardar_estructura(estructura_actual, ruta_actual)
            
            return estructura_actual, True, "Exito", "Parametros AEE guardados", "success", "success"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return no_update, True, "Error", f"Error guardando: {str(e)}", "danger", "danger"
    
    @app.callback(
        [Output("resultados-aee", "children"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-calcular-aee", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def calcular_aee(n_clicks, estructura_actual):
        """Ejecuta analisis estatico de esfuerzos"""
        
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"DEBUG: Boton 'Calcular AEE' presionado - n_clicks: {n_clicks}")
        
        try:
            # Recargar estructura desde archivo activo
            from models.app_state import AppState
            from config.app_config import DATA_DIR
            
            state = AppState()
            ruta_actual = state.get_estructura_actual_path()
            
            estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
            print(f"DEBUG: Estructura recargada: {estructura_actual.get('TITULO', 'N/A')}")
            print(f"DEBUG AEE: restricciones_cables presente: {'restricciones_cables' in estructura_actual}")
            print(f"DEBUG AEE: estados_climaticos presente: {'estados_climaticos' in estructura_actual}")
            
            # Verificar prerequisitos DGE/DME
            from utils.calculo_cache import CalculoCache
            
            nombre_estructura = estructura_actual['TITULO']
            calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
            calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
            
            if not calculo_dge:
                return no_update, True, "Error", "Debe ejecutar DGE primero", "danger", "danger"
            
            if not calculo_dme:
                return no_update, True, "Error", "Debe ejecutar DME primero", "danger", "danger"
            
            # Verificar que existan datos necesarios
            if 'restricciones_cables' not in estructura_actual:
                return no_update, True, "Error", "Debe configurar restricciones de cables en 'Ajustar Parámetros > Modificar Estados Climáticos y Restricciones'", "danger", "danger"
            
            if 'estados_climaticos' not in estructura_actual:
                return no_update, True, "Error", "Debe configurar estados climáticos en 'Ajustar Parámetros > Modificar Estados Climáticos y Restricciones'", "danger", "danger"
            
            # Ejecutar analisis
            resultados = ejecutar_analisis_aee(estructura_actual, calculo_dge, calculo_dme)
            
            print(f"DEBUG: Analisis completado - {len(resultados.get('diagramas', {}))} diagramas generados")
            
            # Guardar cache en background
            def guardar_async():
                try:
                    CalculoCache.guardar_calculo_aee(
                        nombre_estructura,
                        estructura_actual,
                        resultados
                    )
                    print("DEBUG: Cache AEE guardado")
                except Exception as e:
                    print(f"ERROR guardando cache: {e}")
            
            threading.Thread(target=guardar_async, daemon=True).start()
            
            # Generar vista
            from components.vista_analisis_estatico import generar_resultados_aee
            
            calculo_guardado = {
                'resultados': resultados,
                'hash_parametros': resultados.get('hash', '')
            }
            
            vista = generar_resultados_aee(calculo_guardado, estructura_actual)
            
            return vista, True, "Exito", "Analisis AEE completado", "success", "success"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return no_update, True, "Error", f"Error en analisis: {str(e)}", "danger", "danger"
    
    @app.callback(
        [Output("resultados-aee", "children", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-cargar-cache-aee", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_cache_aee(n_clicks, estructura_actual):
        """Carga resultados desde cache"""
        
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"DEBUG: Boton 'Cargar Cache AEE' presionado")
        
        try:
            from utils.calculo_cache import CalculoCache
            from components.vista_analisis_estatico import generar_resultados_aee
            
            nombre_estructura = estructura_actual.get('TITULO', '')
            calculo_guardado = CalculoCache.cargar_calculo_aee(nombre_estructura)
            
            if not calculo_guardado:
                return no_update, True, "Advertencia", "No hay cache disponible", "warning", "warning"
            
            print("DEBUG: Cache AEE cargado")
            
            vista = generar_resultados_aee(calculo_guardado, estructura_actual)
            
            return vista, True, "Exito", "Cache AEE cargado", "success", "success"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return no_update, True, "Error", f"Error cargando cache: {str(e)}", "danger", "danger"

def ejecutar_analisis_aee(estructura_actual, calculo_dge, calculo_dme):
    """Ejecuta analisis estatico de esfuerzos (unidades: daN, daN.m)"""
    import matplotlib.pyplot as plt
    from utils.analisis_estatico import AnalizadorEstatico
    from utils.view_helpers import ViewHelpers
    from utils.calculo_cache import CalculoCache
    from models.app_state import AppState
    from controllers.geometria_controller import ejecutar_calculo_cmc_automatico, ejecutar_calculo_dge
    
    print("DEBUG: Iniciando analisis AEE...")
    
    # Debug: verificar datos en estructura
    print(f"DEBUG: estructura_actual tiene 'restricciones_cables': {'restricciones_cables' in estructura_actual}")
    print(f"DEBUG: estructura_actual tiene 'estados_climaticos': {'estados_climaticos' in estructura_actual}")
    
    state = AppState()
    
    # SIEMPRE ejecutar CMC (forzar recalculo)
    resultado_cmc = ejecutar_calculo_cmc_automatico(estructura_actual, state, generar_plots=False)
    if not resultado_cmc["exito"]:
        raise ValueError(f"Error en CMC: {resultado_cmc['mensaje']}")
    
    # SIEMPRE ejecutar DGE (forzar recalculo)
    resultado_dge = ejecutar_calculo_dge(estructura_actual, state, generar_plots=False)
    if not resultado_dge["exito"]:
        raise ValueError(f"Error en DGE: {resultado_dge['mensaje']}")
    
    # Obtener objetos
    geometria = state.calculo_objetos.estructura_geometria
    
    # Crear mecanica
    from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
    from HipotesisMaestro_Especial import hipotesis_maestro
    
    mecanica = EstructuraAEA_Mecanica(geometria)
    mecanica.asignar_cargas_hipotesis(
        state.calculo_mecanico.df_cargas_totales,
        state.calculo_mecanico.resultados_conductor,
        state.calculo_mecanico.resultados_guardia1,
        estructura_actual.get('L_vano'),
        hipotesis_maestro,
        estructura_actual.get('t_hielo'),
        resultados_guardia2=state.calculo_mecanico.resultados_guardia2
    )
    
    print(f"DEBUG: Objetos listos - {len(geometria.nodos)} nodos")
    
    # Parametros AEE
    parametros_aee = estructura_actual.get('AnalisisEstaticoEsfuerzos', {})
    
    # Crear analizador
    analizador = AnalizadorEstatico(geometria, mecanica, parametros_aee)
    
    # Obtener hipotesis activas
    hipotesis = estructura_actual.get('hipotesis_activas', [])
    
    if not hipotesis:
        # Fallback: usar hipotesis de DME
        df_reacciones = calculo_dme['resultados'].get('df_reacciones')
        if df_reacciones:
            import pandas as pd
            df = pd.read_json(df_reacciones, orient='split')
            hipotesis = df.columns.get_level_values(0).unique().tolist()
    
    print(f"DEBUG: Analizando {len(hipotesis)} hipotesis")
    
    # Hash de parametros
    hash_params = CalculoCache.calcular_hash(estructura_actual)
    
    resultados = {
        'hash': hash_params,
        'esfuerzos': {},
        'diagramas': {}
    }
    
    # Analizar cada hipotesis
    diagramas_activos = parametros_aee.get('DIAGRAMAS_ACTIVOS', {})
    graficos_3d = parametros_aee.get('GRAFICOS_3D_AEE', True)
    
    for hip in hipotesis:
        print(f"  -> Analizando hipotesis: {hip}")
        
        try:
            esfuerzos = analizador.resolver_sistema(hip)
            resultados['esfuerzos'][hip] = esfuerzos
            
            # Generar diagramas segun configuracion
            if diagramas_activos.get('MRT', True):
                valores_mrt = analizador.calcular_momento_resultante_total(esfuerzos)
                resultados['diagramas'][f'MRT_{hip}'] = valores_mrt
                
                # Generar grafico estatico (PNG)
                if graficos_3d:
                    fig = analizador.generar_diagrama_3d(valores_mrt, 'MRT', hip)
                else:
                    fig = analizador.generar_diagrama_2d(valores_mrt, 'MRT', hip)
                
                # Guardar PNG
                ViewHelpers.guardar_imagen_matplotlib(fig, f"AEE_MRT_{hip}", hash_params)
                plt.close(fig)
            
            if diagramas_activos.get('MFE', True):
                valores_mfe = analizador.calcular_momento_flector_equivalente(esfuerzos)
                resultados['diagramas'][f'MFE_{hip}'] = valores_mfe
                
                # Generar grafico estatico (PNG)
                if graficos_3d:
                    fig = analizador.generar_diagrama_3d(valores_mfe, 'MFE', hip)
                else:
                    fig = analizador.generar_diagrama_2d(valores_mfe, 'MFE', hip)
                
                # Guardar PNG
                ViewHelpers.guardar_imagen_matplotlib(fig, f"AEE_MFE_{hip}", hash_params)
                plt.close(fig)
                
        except Exception as e:
            print(f"ERROR en hipotesis {hip}: {e}")
            continue
    
    print(f"DEBUG: Analisis AEE completado")
    
    return resultados
