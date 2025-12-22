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
        
        resultado_arboles = generar_arboles_carga(
            estructura_mecanica, estructura_actual,
            zoom=config["zoom"], 
            escala_flecha=config["escala_flecha"], 
            grosor_linea=config["grosor_linea"],
            mostrar_nodos=config["mostrar_nodos"], 
            fontsize_nodos=config["fontsize_nodos"], 
            fontsize_flechas=config["fontsize_flechas"], 
            mostrar_sismo=config["mostrar_sismo"],
            usar_3d=config["usar_3d"],
            estructura_geometria=state.calculo_objetos.estructura_geometria
        )
        
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
            PRIORIDAD_DIMENSIONADO=estructura_actual.get('PRIORIDAD_DIMENSIONADO', 'longitud_total')
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
