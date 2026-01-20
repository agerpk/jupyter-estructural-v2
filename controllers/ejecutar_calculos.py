"""Funciones ejecutables centralizadas para todos los cálculos"""

def ejecutar_calculo_dme(estructura_actual, state, generar_plots=True):
    """Ejecuta cálculo DME y retorna resultados"""
    try:
        from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
        from EstructuraAEA_Graficos import EstructuraAEA_Graficos
        from utils.calculo_cache import CalculoCache
        from HipotesisMaestro_Especial import hipotesis_maestro
        import matplotlib.pyplot as plt
        
        estructura_geometria = state.calculo_objetos.estructura_geometria
        estructura_mecanica = EstructuraAEA_Mecanica(estructura_geometria)
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        
        estructura_mecanica.asignar_cargas_hipotesis(
            state.calculo_mecanico.df_cargas_totales,
            state.calculo_mecanico.resultados_conductor,
            state.calculo_mecanico.resultados_guardia1,
            estructura_actual.get('L_vano'),
            hipotesis_maestro,
            estructura_actual.get('t_hielo'),
            resultados_guardia2=state.calculo_mecanico.resultados_guardia2
        )
        
        nodes_key = estructura_geometria.nodes_key
        nodo_cima = "TOP" if "TOP" in nodes_key else ("HG1" if "HG1" in nodes_key else max(nodes_key.items(), key=lambda x: x[1][2])[0])
        
        df_reacciones = estructura_mecanica.calcular_reacciones_tiros_cima(nodo_apoyo="BASE", nodo_cima=nodo_cima)
        
        if generar_plots:
            estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica)
            fig_polar = estructura_graficos.diagrama_polar_tiros()
            fig_barras = estructura_graficos.diagrama_barras_tiros(mostrar_c2=estructura_actual.get('MOSTRAR_C2', False))
        else:
            fig_polar = None
            fig_barras = None
        
        CalculoCache.guardar_calculo_dme(nombre_estructura, estructura_actual, df_reacciones, fig_polar, fig_barras)
        
        state.calculo_objetos.estructura_mecanica = estructura_mecanica
        
        return {"exito": True, "mensaje": "Cálculo DME completado", "df_reacciones": df_reacciones}
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}


def ejecutar_calculo_arboles(estructura_actual, state, generar_plots=True):
    """Ejecuta cálculo de árboles de carga y retorna resultados"""
    try:
        from utils.arboles_carga import generar_arboles_carga
        from utils.calculo_cache import CalculoCache
        from config.app_config import DATA_DIR
        import json
        
        # Cargar configuración persistente
        config_path = DATA_DIR / "arboles_config.json"
        config_default = {
            "zoom": 0.5,
            "escala_flecha": 2.0,
            "grosor_linea": 3,
            "fontsize_nodos": 6,
            "fontsize_flechas": 6,
            "mostrar_nodos": True,
            "mostrar_sismo": False,
            "usar_3d": True
        }
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except:
            config = config_default
        
        estructura_mecanica = state.calculo_objetos.estructura_mecanica
        
        # Usar ADC_3D de la estructura, no del config global
        usar_3d = estructura_actual.get('ADC_3D', config["usar_3d"])
        
        if generar_plots:
            resultado_arboles = generar_arboles_carga(
                estructura_mecanica, estructura_actual,
                zoom=config["zoom"], 
                escala_flecha=config["escala_flecha"], 
                grosor_linea=config["grosor_linea"],
                mostrar_nodos=config["mostrar_nodos"], 
                fontsize_nodos=config["fontsize_nodos"], 
                fontsize_flechas=config["fontsize_flechas"], 
                mostrar_sismo=config["mostrar_sismo"],
                usar_3d=usar_3d,
                estructura_geometria=state.calculo_objetos.estructura_geometria
            )
        else:
            resultado_arboles = {'exito': True, 'imagenes': [], 'mensaje': 'Árboles omitidos (generar_plots=False)'}
        
        if resultado_arboles['exito']:
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            # Generar DataFrame de cargas si no existe
            if not hasattr(estructura_mecanica, 'df_cargas_completo') or estructura_mecanica.df_cargas_completo is None:
                estructura_mecanica.generar_dataframe_cargas()
            df_cargas = estructura_mecanica.df_cargas_completo
            CalculoCache.guardar_calculo_arboles(nombre_estructura, estructura_actual, resultado_arboles['imagenes'], df_cargas)
        
        return resultado_arboles
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}


def ejecutar_calculo_sph(estructura_actual, state):
    """Ejecuta cálculo de selección de postes y retorna resultados"""
    try:
        from PostesHormigon import PostesHormigon
        from utils.calculo_cache import CalculoCache
        import io, sys, hashlib, json
        
        estructura_geometria = state.calculo_objetos.estructura_geometria
        estructura_mecanica = state.calculo_objetos.estructura_mecanica
        
        postes = PostesHormigon()
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        resultados_sph = postes.calcular_seleccion_postes(
            geometria=estructura_geometria,
            mecanica=estructura_mecanica,
            FORZAR_N_POSTES=estructura_actual.get('FORZAR_N_POSTES', 0),
            FORZAR_ORIENTACION=estructura_actual.get('FORZAR_ORIENTACION', 'No'),
            ANCHO_CRUCETA=estructura_actual.get('ANCHO_CRUCETA', 0.2),
            PRIORIDAD_DIMENSIONADO=estructura_actual.get('PRIORIDAD_DIMENSIONADO', 'longitud_total'),
            AJUSTE_RO_POR_HT=estructura_actual.get('AJUSTE_RO_POR_HT', False),
            KE_estructura_ensayada=estructura_actual.get('KE_estructura_ensayada', 1.0)
        )
        
        postes.imprimir_desarrollo_seleccion_postes()
        desarrollo_texto = buffer.getvalue()
        sys.stdout = old_stdout
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        
        # Remover objetos no serializables
        resultados_serializables = resultados_sph.copy()
        if 'geometria' in resultados_serializables:
            del resultados_serializables['geometria']
        if 'mecanica' in resultados_serializables:
            del resultados_serializables['mecanica']
        
        CalculoCache.guardar_calculo_sph(nombre_estructura, estructura_actual, resultados_serializables, desarrollo_texto)
        
        return {"exito": True, "mensaje": "Cálculo SPH completado", "resultados": resultados_serializables, "desarrollo_texto": desarrollo_texto}
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}


def ejecutar_calculo_fundacion(estructura_actual, state, generar_plots=True):
    """Ejecuta cálculo de fundación y retorna resultados"""
    try:
        from utils.validacion_prerequisitos import validar_prerequisitos_fundacion
        from utils.Sulzberger import Sulzberger
        from utils.calculo_cache import CalculoCache
        import threading
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        
        # Validar prerequisitos
        prerequisitos_ok, mensaje_prereq = validar_prerequisitos_fundacion(nombre_estructura)
        if not prerequisitos_ok:
            return {"exito": False, "mensaje": f"Prerequisitos faltantes: {mensaje_prereq}"}
        
        # Obtener parámetros desde SPH usando la lógica del controlador
        from controllers.fundacion_controller import obtener_parametros_desde_sph
        parametros_estructura = obtener_parametros_desde_sph(nombre_estructura, estructura_actual)
        
        if not parametros_estructura:
            return {"exito": False, "mensaje": "No se pudieron obtener parámetros de SPH"}
        
        # Configurar parámetros usando valores del JSON
        parametros_suelo = {
            'C': estructura_actual.get('indice_compresibilidad', 5000000),
            'sigma_adm': estructura_actual.get('presion_admisible', 50000),
            'beta': estructura_actual.get('angulo_tierra_gravante', 8.0),
            'mu': estructura_actual.get('coef_friccion_terreno_hormigon', 0.4),
            'gamma_hor': estructura_actual.get('densidad_hormigon', 2200),
            'gamma_tierra': estructura_actual.get('densidad_tierra', 3800)
        }
        parametros_calculo = {
            'FS': estructura_actual.get('coef_seguridad_volcamiento', 1.5),
            'tg_alfa_adm': estructura_actual.get('inclinacion_desplazamiento', 0.01),
            't_he_max': estructura_actual.get('relacion_max_sin_armadura', 1.25),
            'sigma_max_adm': estructura_actual.get('superacion_presion_admisible', 1.33),
            'incremento': estructura_actual.get('incremento_calculo', 0.01),
            'cacb': estructura_actual.get('coef_aumento_cb_ct', 1.2),
            'max_iteraciones': 10000,
            't_max': 3.0,
            'factor_rombica': 0.5
        }
        
        parametros_poste = {
            'dml': estructura_actual.get('distancia_molde_hueco_lateral', 0.15),
            'dmf': estructura_actual.get('distancia_molde_hueco_fondo', 0.2),
            'dmol': estructura_actual.get('diametro_molde', 0.6),
            'spc': estructura_actual.get('separacion_postes_cima', 0.3),
            'pp': estructura_actual.get('pendiente_postes_multiples', 4),
            'con': estructura_actual.get('conicidad_poste', 1.5)
        }
        
        dimensiones = {
            'tin': estructura_actual.get('profundidad_propuesta', 1.7),
            'ain': estructura_actual.get('longitud_colineal_inferior', 1.3),
            'bin': estructura_actual.get('longitud_transversal_inferior', 1.3)
        }
        
        # Crear instancia Sulzberger
        parametros_estructura_completos = {
            'Gp': parametros_estructura['Gp'],
            'h': parametros_estructura.get('h', 15.0),
            'hl': parametros_estructura.get('hl', 13.5),
            'he': parametros_estructura['he'],
            'dc': parametros_estructura.get('dc', 0.31),
            'n_postes': 1,
            'hipotesis_fuerzas': parametros_estructura['hipotesis_fuerzas']
        }
        
        sulzberger = Sulzberger(
            parametros_estructura=parametros_estructura_completos,
            parametros_suelo=parametros_suelo,
            parametros_calculo=parametros_calculo
        )
        
        # Ejecutar cálculo
        resultados = sulzberger.calcular_fundacion_multiples_hipotesis(
            tin=dimensiones['tin'],
            ain=dimensiones['ain'],
            bin=dimensiones['bin'],
            tipo_base=estructura_actual.get('tipo_base_fundacion', 'cuadrada')
        )
        
        # Generar DataFrame y memoria
        df_resultados = sulzberger.obtener_dataframe_todas_hipotesis()
        memoria_calculo = sulzberger.generar_memoria_calculo_ingenieria()
        
        # Generar gráfico 3D para hipótesis dimensionante
        fig_3d = None
        if generar_plots:
            try:
                from utils.grafico_sulzberger_monobloque import GraficoSulzbergerMonobloque
                grafico_obj = GraficoSulzbergerMonobloque(nombre_estructura)
                grafico_obj.parametros = {
                    'estructura': parametros_estructura_completos,
                    'suelo': parametros_suelo,
                    'calculo': parametros_calculo,
                    'poste': parametros_poste
                }
                grafico_obj.todas_hipotesis = resultados['todas_hipotesis']
                
                hipotesis_dim = resultados['hipotesis_dimensionante']
                fig_3d = grafico_obj._crear_grafico_hipotesis(hipotesis_dim)
            except Exception as e:
                print(f"Advertencia: No se pudo generar gráfico 3D: {e}")
        
        # Guardar en cache
        parametros_cache = {
            'estructura': parametros_estructura,
            'suelo': parametros_suelo,
            'calculo': parametros_calculo,
            'poste': parametros_poste,
            'dimensiones': dimensiones
        }
        
        resultados_cache = {
            'resultados': resultados,
            'dataframe_html': df_resultados.to_json(orient='split'),
            'memoria_calculo': memoria_calculo
        }
        
        # Corregir llamada al cache - usar estructura_actual como estructura_data
        CalculoCache.guardar_calculo_fund(
            nombre_estructura,
            estructura_actual,    # estructura_data
            parametros_cache,     # parametros
            resultados_cache,     # resultados
            fig_3d               # fig_3d
        )
        
        return {"exito": True, "mensaje": "Cálculo de fundación completado", "resultados": resultados}
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}


def ejecutar_calculo_costeo(estructura_actual, state):
    """Ejecuta cálculo de costeo y retorna resultados"""
    try:
        # Usar lógica del controlador de costeo
        from utils.calculo_costeo import verificar_cadena_completa_costeo, ejecutar_cadena_completa_costeo, extraer_datos_para_costeo, calcular_costeo_completo
        from utils.calculo_cache import CalculoCache
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        
        # Obtener parámetros de costeo desde estructura
        parametros_costeo = estructura_actual.get('costeo', {})
        if not parametros_costeo or not parametros_costeo.get('fundaciones', {}).get('precio_m3_hormigon'):
            return {"exito": False, "mensaje": "No hay parámetros de costeo configurados"}
        
        # Verificar prerequisitos usando lógica del controlador
        cadena_completa = verificar_cadena_completa_costeo(nombre_estructura, estructura_actual)
        
        if not cadena_completa:
            exito_cadena = ejecutar_cadena_completa_costeo(nombre_estructura, estructura_actual)
            if not exito_cadena:
                return {"exito": False, "mensaje": "No se pudo completar la cadena de cálculos prerequisitos"}
        
        # Extraer datos necesarios
        datos_estructura = extraer_datos_para_costeo(nombre_estructura)
        if not datos_estructura:
            return {"exito": False, "mensaje": "No se pudieron extraer datos de SPH y Fundaciones"}
        
        # Obtener tensión de la estructura
        tension_kv = estructura_actual.get('TENSION', 220)
        
        # Ejecutar cálculo de costeo
        resultados = calcular_costeo_completo(datos_estructura, parametros_costeo, tension_kv)
        
        # Guardar en cache
        CalculoCache.guardar_calculo_costeo(
            nombre_estructura,
            estructura_actual,
            parametros_costeo,
            resultados
        )
        
        return {"exito": True, "mensaje": "Cálculo de costeo completado", "resultados": resultados}
    except Exception as e:
        import traceback
        print(f"Error en costeo: {traceback.format_exc()}")
        return {"exito": False, "mensaje": str(e)}


def ejecutar_calculo_aee(estructura_actual, state):
    """Ejecuta el cálculo de Análisis Estático de Esfuerzos (AEE)"""
    try:
        from utils.calculo_cache import CalculoCache
        from controllers.aee_controller import ejecutar_analisis_aee
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        
        # Verificar prerequisitos
        calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
        if not calculo_dge:
            return {"exito": False, "mensaje": "AEE requiere el resultado de un cálculo DGE previo."}
        
        calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
        if not calculo_dme:
            return {"exito": False, "mensaje": "AEE requiere el resultado de un cálculo DME previo."}
        
        # El guardado en cache se maneja dentro de ejecutar_analisis_aee
        resultados = ejecutar_analisis_aee(estructura_actual, calculo_dge, calculo_dme)
        
        if resultados:
            # Guardar explícitamente en cache para el flujo de "Calcular Todo"
            CalculoCache.guardar_calculo_aee(
                nombre_estructura,
                estructura_actual,
                resultados
            )
            return {"exito": True, "mensaje": "Cálculo AEE completado"}
        else:
            return {"exito": False, "mensaje": "El análisis AEE no produjo resultados."}

    except Exception as e:
        import traceback
        print(f"Error en AEE: {traceback.format_exc()}")
        return {"exito": False, "mensaje": str(e)}
