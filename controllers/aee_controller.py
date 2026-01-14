"""
Controller para Analisis Estatico de Esfuerzos (AEE)
"""

import dash
from dash import Input, Output, State, no_update
import threading
import numpy as np

def _make_serializable(data):
    """
    Recursively traverses a data structure and converts non-serializable
    numpy types to their serializable Python equivalents.
    """
    if isinstance(data, dict):
        return {k: _make_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_make_serializable(i) for i in data]
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, (np.integer,)):
        return int(data)
    elif isinstance(data, (np.floating,)):
        return float(data)
    else:
        return data

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
         State("aee-escala-graficos", "value"),
         State("aee-n-corta", "value"),
         State("aee-n-larga", "value"),
         State("aee-percentil", "value"),
         State("aee-diagramas", "value")],
        prevent_initial_call=True
    )
    def guardar_parametros_aee(n_clicks, estructura_actual, graficos_3d, escala_graficos, n_corta, n_larga, percentil, diagramas):
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
            estructura_actual['AnalisisEstaticoEsfuerzos']['escala_graficos'] = escala_graficos
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
        print(f"DEBUG: Estructura desde State: {estructura_actual.get('TITULO', 'N/A')}")
        
        try:
            from models.app_state import AppState
            from utils.calculo_cache import CalculoCache
            
            state = AppState()
            
            nombre_estructura = estructura_actual['TITULO']
            calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
            calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
            
            if not calculo_dge:
                return no_update, True, "Error", "Debe ejecutar DGE primero", "danger", "danger"
            
            if not calculo_dme:
                return no_update, True, "Error", "Debe ejecutar DME primero", "danger", "danger"
            
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
        
        print(f"🔵 DEBUG: Boton 'Cargar Cache AEE' presionado")
        
        try:
            from utils.calculo_cache import CalculoCache
            from components.vista_analisis_estatico import generar_resultados_aee
            
            nombre_estructura = estructura_actual.get('TITULO', '')
            print(f"🔵 DEBUG: Buscando cache para: '{nombre_estructura}'")
            
            calculo_guardado = CalculoCache.cargar_calculo_aee(nombre_estructura)
            
            if not calculo_guardado:
                print(f"❌ DEBUG: No se encontró archivo de cache")
                return no_update, True, "Advertencia", "No hay cache disponible", "warning", "warning"
            
            print(f"✅ DEBUG: Cache cargado - keys: {list(calculo_guardado.keys())}")
            
            vista = generar_resultados_aee(calculo_guardado, estructura_actual)
            
            return vista, True, "Éxito", "Cache AEE cargado", "success", "success"
            
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
        resultados_guardia2=state.calculo_mecanico.resultados_guardia2,
        estados_climaticos=estructura_actual.get('estados_climaticos')
    )
    
    print(f"DEBUG: Cargas asignadas - {len(geometria.nodos)} nodos")
    
    # Generar DataFrame de cargas
    mecanica.generar_dataframe_cargas()
    print(f"✅ DataFrame de cargas generado: {mecanica.df_cargas_completo is not None}")
    
    # Obtener hipótesis desde las cargas asignadas a los nodos (mantener orden)
    hipotesis_set = set()
    for nodo in geometria.nodos.values():
        hipotesis_set.update(nodo.listar_hipotesis())
    
    # Ordenar hipótesis alfabéticamente para mantener orden consistente (A0, A1, A2, B1, B2, C1, C2)
    hipotesis = sorted(list(hipotesis_set))
    if not hipotesis:
        raise ValueError("No se encontraron hipótesis con cargas asignadas")
    
    print(f"DEBUG: Analizando {len(hipotesis)} hipótesis: {hipotesis}")
    
    print(f"DEBUG: Analizando {len(hipotesis)} hipotesis: {hipotesis}")
    
    # Parametros AEE
    parametros_aee = estructura_actual.get('AnalisisEstaticoEsfuerzos', {})
    
    # Crear analizador
    analizador = AnalizadorEstatico(geometria, mecanica, parametros_aee)
    
    # Hash de parametros
    hash_params = CalculoCache.calcular_hash(estructura_actual)
    
    resultados = {
        'hash': hash_params,
        'esfuerzos': {},
        'diagramas': {},
        'nodos_info': {},
        'conexiones_info': [],
        'df_cargas_completo': None
    }
    
    # Guardar info de nodos
    for nombre, nodo in geometria.nodos.items():
        resultados['nodos_info'][nombre] = {
            'x': float(nodo.x),
            'y': float(nodo.y),
            'z': float(nodo.z),
            'tipo': nodo.tipo_nodo
        }
    
    # Guardar info de conexiones
    import numpy as np
    for conn in analizador.conexiones:
        nodo_i, nodo_j = conn
        
        # Obtener tipo de conexión desde geometria.conexiones (tupla de 3 elementos)
        tipo_conexion = 'barra'
        if hasattr(geometria, 'conexiones') and geometria.conexiones:
            for geom_conn in geometria.conexiones:
                if isinstance(geom_conn, (list, tuple)) and len(geom_conn) >= 3:
                    if geom_conn[0] == nodo_i and geom_conn[1] == nodo_j:
                        tipo_conexion = geom_conn[2]
                        break
        
        coord_i = geometria.nodos[nodo_i].coordenadas
        coord_j = geometria.nodos[nodo_j].coordenadas
        longitud = float(np.linalg.norm(np.array(coord_j) - np.array(coord_i)))
        
        resultados['conexiones_info'].append({
            'Nodo Inicial': nodo_i,
            'Nodo Final': nodo_j,
            'Longitud [m]': f"{longitud:.2f}",
            'Tipo': tipo_conexion
        })
    
    # Analizar cada hipotesis
    diagramas_activos = parametros_aee.get('DIAGRAMAS_ACTIVOS', {})
    graficos_3d = parametros_aee.get('GRAFICOS_3D_AEE', True)
    escala_graficos = parametros_aee.get('escala_graficos', 'logaritmica')
    
    for hip in hipotesis:
        print(f"  -> Analizando hipotesis: {hip}")
        
        try:
            esfuerzos = analizador.resolver_sistema(hip)
            # Convertir recursivamente tipos numpy a serializables para JSON
            esfuerzos_serializables = _make_serializable(esfuerzos)
            resultados['esfuerzos'][hip] = esfuerzos_serializables
            
            # Generar DataFrame de resultados por elemento
            if 'resultados_por_elemento' in esfuerzos:
                import pandas as pd
                filas = []
                for elem_key, subelems in esfuerzos['resultados_por_elemento'].items():
                    partes = elem_key.split('_')
                    ni = '_'.join(partes[:-1]) if len(partes) > 2 else partes[0]
                    nj = partes[-1]
                    for subelem in subelems:
                        filas.append({
                            'Elemento': elem_key,
                            'Nodo_Inicio': ni,
                            'Nodo_Fin': nj,
                            'Sub_Idx': subelem['sub_idx'],
                            'Tipo': subelem.get('tipo_elemento', 'N/A'),
                            'Eje_Long_Global': subelem.get('eje_longitudinal_global', 'N/A'),
                            'N_daN': round(subelem['N'], 2),
                            'Qy_daN': round(subelem['Qy'], 2),
                            'Qz_daN': round(subelem['Qz'], 2),
                            'Q_daN': round(subelem['Q'], 2),
                            'Mx_daN_m': round(subelem['Mx'], 2),
                            'My_daN_m': round(subelem['My'], 2),
                            'Mz_daN_m': round(subelem['Mz'], 2),
                            'M_daN_m': round(subelem['M'], 2),
                            'T_daN_m': round(subelem['T'], 2)
                        })
                
                if filas:
                    df_resultados = pd.DataFrame(filas)
                    resultados['esfuerzos'][hip]['df_resultados'] = df_resultados.to_dict(orient='split')
            
            # Generar diagramas MQNT
            if diagramas_activos.get('MQNT', True):
                try:
                    fig = analizador.generar_diagrama_mqnt(esfuerzos, hip, graficos_3d, escala_graficos)
                    
                    from pathlib import Path
                    filename = f"AEE_MQNT_{hip}.{hash_params}.png"
                    filepath = Path("data/cache") / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    fig.savefig(str(filepath), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    
                    # Guardar referencia en resultados
                    resultados['diagramas'][f'MQNT_{hip}'] = filename
                    print(f"✅ Diagrama MQNT guardado: {filename}")
                except Exception as e:
                    print(f"❌ Error guardando MQNT para {hip}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Generar diagramas segun configuracion
            if diagramas_activos.get('MRT', True):
                valores_mrt = analizador.calcular_momento_resultante_total(esfuerzos)
                # Convertir a formato serializable
                valores_mrt_serializables = _make_serializable(valores_mrt)
                resultados['diagramas'][f'MRT_{hip}'] = valores_mrt_serializables
                
                # Generar grafico estatico (PNG)
                try:
                    if graficos_3d:
                        fig = analizador.generar_diagrama_3d(valores_mrt, 'MRT', hip, escala_graficos)
                    else:
                        fig = analizador.generar_diagrama_2d(valores_mrt, 'MRT', hip, escala_graficos)
                    
                    # Guardar PNG directamente
                    from pathlib import Path
                    filename = f"AEE_MRT_{hip}.{hash_params}.png"
                    filepath = Path("data/cache") / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    fig.savefig(str(filepath), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    # Registrar nombre de archivo en resultados para que la vista pueda cargar la imagen
                    resultados['diagramas'][f'MRT_{hip}'] = filename
                except Exception as e:
                    print(f"Error guardando MRT para {hip}: {e}")
            
            if diagramas_activos.get('MFE', True):
                valores_mfe = analizador.calcular_momento_flector_equivalente(esfuerzos)
                # Convertir a formato serializable
                valores_mfe_serializables = _make_serializable(valores_mfe)
                resultados['diagramas'][f'MFE_{hip}'] = valores_mfe_serializables
                
                # Generar grafico estatico (PNG)
                try:
                    if graficos_3d:
                        fig = analizador.generar_diagrama_3d(valores_mfe, 'MFE', hip, escala_graficos)
                    else:
                        fig = analizador.generar_diagrama_2d(valores_mfe, 'MFE', hip, escala_graficos)
                    
                    # Guardar PNG directamente
                    from pathlib import Path
                    filename = f"AEE_MFE_{hip}.{hash_params}.png"
                    filepath = Path("data/cache") / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    fig.savefig(str(filepath), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    # Registrar nombre de archivo en resultados para que la vista pueda cargar la imagen
                    resultados['diagramas'][f'MFE_{hip}'] = filename
                except Exception as e:
                    print(f"Error guardando MFE para {hip}: {e}")
                
        except Exception as e:
            print(f"ERROR en hipotesis {hip}: {e}")
            continue
    
    # Guardar DataFrame de cargas en resultados
    if mecanica.df_cargas_completo is not None:
        resultados['df_cargas_completo'] = {
            'data': mecanica.df_cargas_completo.values.tolist(),
            'columns': [list(mecanica.df_cargas_completo.columns.get_level_values(i)) for i in range(mecanica.df_cargas_completo.columns.nlevels)],
            'column_codes': [mecanica.df_cargas_completo.columns.codes[i].tolist() for i in range(mecanica.df_cargas_completo.columns.nlevels)]
        }
        print(f"✅ DataFrame de cargas guardado en resultados")
    
    # Generar DataFrame de reacciones
    try:
        df_reacciones = analizador.generar_dataframe_reacciones(hipotesis)
        if not df_reacciones.empty:
            resultados['df_reacciones'] = {
                'data': df_reacciones.values.tolist(),
                'columns': df_reacciones.columns.tolist(),
                'index': df_reacciones.index.tolist()
            }
            print(f"✅ DataFrame de reacciones guardado: {len(df_reacciones)} hipótesis")
    except Exception as e:
        print(f"❌ Error generando DataFrame de reacciones: {e}")
    
    print(f"DEBUG: Analisis AEE completado")
    
    return resultados
