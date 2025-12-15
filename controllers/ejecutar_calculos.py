"""Funciones ejecutables centralizadas para todos los cálculos"""

def ejecutar_calculo_dme(estructura_actual, state):
    """Ejecuta cálculo DME y retorna resultados"""
    try:
        from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
        from EstructuraAEA_Graficos import EstructuraAEA_Graficos
        from utils.calculo_cache import CalculoCache
        from HipotesisMaestro_Especial import hipotesis_maestro as hipotesis_maestro_base
        from utils.hipotesis_manager import HipotesisManager
        from config.app_config import DATA_DIR
        import matplotlib.pyplot as plt
        
        estructura_geometria = state.calculo_objetos.estructura_geometria
        estructura_mecanica = EstructuraAEA_Mecanica(estructura_geometria)
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        estructura_json_path = str(DATA_DIR / f"{nombre_estructura}.estructura.json")
        hipotesis_maestro = HipotesisManager.cargar_o_crear_hipotesis(
            nombre_estructura, estructura_json_path, hipotesis_maestro_base
        )
        
        estructura_mecanica.asignar_cargas_hipotesis(
            state.calculo_mecanico.df_cargas_totales,
            state.calculo_mecanico.resultados_conductor,
            state.calculo_mecanico.resultados_guardia1,
            estructura_actual.get('L_vano'),
            hipotesis_maestro,
            estructura_actual.get('t_hielo')
        )
        
        nodes_key = estructura_geometria.nodes_key
        nodo_cima = "TOP" if "TOP" in nodes_key else ("HG1" if "HG1" in nodes_key else max(nodes_key.items(), key=lambda x: x[1][2])[0])
        
        df_reacciones = estructura_mecanica.calcular_reacciones_tiros_cima(nodo_apoyo="BASE", nodo_cima=nodo_cima)
        
        estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica)
        estructura_graficos.diagrama_polar_tiros()
        fig_polar = plt.gcf()
        estructura_graficos.diagrama_barras_tiros(mostrar_c2=estructura_actual.get('MOSTRAR_C2', False))
        fig_barras = plt.gcf()
        
        CalculoCache.guardar_calculo_dme(nombre_estructura, estructura_actual, df_reacciones, fig_polar, fig_barras)
        
        state.calculo_objetos.estructura_mecanica = estructura_mecanica
        
        return {"exito": True, "mensaje": "Cálculo DME completado", "df_reacciones": df_reacciones}
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}


def ejecutar_calculo_arboles(estructura_actual, state):
    """Ejecuta cálculo de árboles de carga y retorna resultados"""
    try:
        from utils.arboles_carga import generar_arboles_carga
        from utils.calculo_cache import CalculoCache
        
        estructura_mecanica = state.calculo_objetos.estructura_mecanica
        
        resultado_arboles = generar_arboles_carga(
            estructura_mecanica, estructura_actual,
            zoom=1.0, escala_flecha=1.0, grosor_linea=1.5,
            mostrar_nodos=True, fontsize_nodos=8, fontsize_flechas=8, mostrar_sismo=False
        )
        
        if resultado_arboles['exito']:
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            CalculoCache.guardar_calculo_arboles(nombre_estructura, estructura_actual, resultado_arboles['imagenes'])
        
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
            PRIORIDAD_DIMENSIONADO=estructura_actual.get('PRIORIDAD_DIMENSIONADO', 'longitud_total')
        )
        
        postes.imprimir_desarrollo_seleccion_postes()
        desarrollo_texto = buffer.getvalue()
        sys.stdout = old_stdout
        
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        calculo_sph = {
            'parametros': estructura_actual,
            'hash_parametros': hashlib.md5(json.dumps(estructura_actual, sort_keys=True).encode()).hexdigest(),
            'resultados': resultados_sph,
            'desarrollo_texto': desarrollo_texto
        }
        CalculoCache.guardar_calculo_sph(nombre_estructura, calculo_sph)
        
        return {"exito": True, "mensaje": "Cálculo SPH completado", "resultados": resultados_sph, "desarrollo_texto": desarrollo_texto}
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}
