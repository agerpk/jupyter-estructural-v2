"""
Plotear resultados AEE existentes sin recalcular
"""

import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

def plotear_resultados_existentes(estructura_actual):
    """
    Carga resultados AEE existentes y regenera solo los gráficos
    Lee configuración actual de la estructura para determinar qué plotear
    """
    from utils.calculo_cache import CalculoCache
    from utils.analisis_estatico import AnalizadorEstatico
    from models.app_state import AppState
    
    nombre_estructura = estructura_actual['TITULO']
    
    # Cargar cache AEE
    calculo_aee = CalculoCache.cargar_calculo_aee(nombre_estructura)
    if not calculo_aee:
        raise ValueError("No hay resultados AEE guardados para esta estructura")
    
    resultados = calculo_aee.get('resultados', {})
    esfuerzos_dict = resultados.get('esfuerzos', {})
    
    if not esfuerzos_dict:
        raise ValueError("No hay esfuerzos calculados en el cache")
    
    # Cargar DGE para obtener geometría
    calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
    if not calculo_dge:
        raise ValueError("Debe ejecutar DGE primero")
    
    # Recrear objetos necesarios
    state = AppState()
    from controllers.geometria_controller import ejecutar_calculo_cmc_automatico, ejecutar_calculo_dge
    
    resultado_cmc = ejecutar_calculo_cmc_automatico(estructura_actual, state, generar_plots=False)
    if not resultado_cmc["exito"]:
        raise ValueError(f"Error en CMC: {resultado_cmc['mensaje']}")
    
    resultado_dge = ejecutar_calculo_dge(estructura_actual, state, generar_plots=False)
    if not resultado_dge["exito"]:
        raise ValueError(f"Error en DGE: {resultado_dge['mensaje']}")
    
    geometria = state.calculo_objetos.estructura_geometria
    
    # Crear mecánica
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
    
    # Leer configuración ACTUAL de la estructura
    parametros_aee = estructura_actual.get('AnalisisEstaticoEsfuerzos', {})
    diagramas_activos = parametros_aee.get('DIAGRAMAS_ACTIVOS', {})
    graficos_3d = parametros_aee.get('GRAFICOS_3D_AEE', True)
    escala_graficos = parametros_aee.get('escala_graficos', 'logaritmica')
    plots_interactivos = parametros_aee.get('plots_interactivos', True)
    
    print(f"📊 Configuración de ploteo:")
    print(f"  - Gráficos 3D: {graficos_3d}")
    print(f"  - Plots interactivos: {plots_interactivos}")
    print(f"  - Escala: {escala_graficos}")
    print(f"  - Diagramas activos: {diagramas_activos}")
    
    # Crear analizador
    analizador = AnalizadorEstatico(geometria, mecanica, parametros_aee)
    
    # Hash de parámetros
    hash_params = CalculoCache.calcular_hash(estructura_actual)
    
    diagramas_generados = 0
    
    # Regenerar gráficos para cada hipótesis
    for hip, esfuerzos_data in esfuerzos_dict.items():
        print(f"  -> Ploteando hipótesis: {hip}")
        
        # Reconstruir esfuerzos desde cache
        esfuerzos = {
            'valores': esfuerzos_data.get('valores', {}),
            'reacciones': esfuerzos_data.get('reacciones', {}),
            'elementos_dict': esfuerzos_data.get('elementos_dict', {}),
            'resultados_por_elemento': esfuerzos_data.get('resultados_por_elemento', {})
        }
        
        # Convertir valores a numpy arrays si es necesario
        for key, val in esfuerzos['valores'].items():
            if isinstance(val, list):
                esfuerzos['valores'][key] = np.array(val)
        
        try:
            # MQNT
            if diagramas_activos.get('MQNT', True):
                if plots_interactivos:
                    fig = analizador.generar_diagrama_mqnt_interactivo(esfuerzos, hip, graficos_3d, escala_graficos)
                    filename_png = f"AEE_MQNT_{hip}.{hash_params}.png"
                    filename_json = f"AEE_MQNT_{hip}.{hash_params}.json"
                    filepath_png = Path("data/cache") / filename_png
                    filepath_json = Path("data/cache") / filename_json
                    filepath_png.parent.mkdir(parents=True, exist_ok=True)
                    fig.write_image(str(filepath_png), width=1200, height=800)
                    fig.write_json(str(filepath_json))
                    diagramas_generados += 1
                else:
                    fig = analizador.generar_diagrama_mqnt(esfuerzos, hip, graficos_3d, escala_graficos)
                    filename_png = f"AEE_MQNT_{hip}.{hash_params}.png"
                    filepath_png = Path("data/cache") / filename_png
                    filepath_png.parent.mkdir(parents=True, exist_ok=True)
                    fig.savefig(str(filepath_png), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    diagramas_generados += 1
            
            # MRT
            if diagramas_activos.get('MRT', True):
                valores_mrt = analizador.calcular_momento_resultante_total(esfuerzos)
                if plots_interactivos:
                    if graficos_3d:
                        fig = analizador.generar_diagrama_3d_interactivo(valores_mrt, 'MRT', hip, escala_graficos)
                    else:
                        fig = analizador.generar_diagrama_2d_interactivo(valores_mrt, 'MRT', hip, escala_graficos)
                    filename_png = f"AEE_MRT_{hip}.{hash_params}.png"
                    filename_json = f"AEE_MRT_{hip}.{hash_params}.json"
                    filepath_png = Path("data/cache") / filename_png
                    filepath_json = Path("data/cache") / filename_json
                    filepath_png.parent.mkdir(parents=True, exist_ok=True)
                    fig.write_image(str(filepath_png), width=1200, height=600)
                    fig.write_json(str(filepath_json))
                    diagramas_generados += 1
                else:
                    if graficos_3d:
                        fig = analizador.generar_diagrama_3d(valores_mrt, 'MRT', hip, escala_graficos)
                    else:
                        fig = analizador.generar_diagrama_2d(valores_mrt, 'MRT', hip, escala_graficos)
                    filename_png = f"AEE_MRT_{hip}.{hash_params}.png"
                    filepath_png = Path("data/cache") / filename_png
                    filepath_png.parent.mkdir(parents=True, exist_ok=True)
                    fig.savefig(str(filepath_png), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    diagramas_generados += 1
            
            # MFE
            if diagramas_activos.get('MFE', True):
                valores_mfe = analizador.calcular_momento_flector_equivalente(esfuerzos)
                if plots_interactivos:
                    if graficos_3d:
                        fig = analizador.generar_diagrama_3d_interactivo(valores_mfe, 'MFE', hip, escala_graficos)
                    else:
                        fig = analizador.generar_diagrama_2d_interactivo(valores_mfe, 'MFE', hip, escala_graficos)
                    filename_png = f"AEE_MFE_{hip}.{hash_params}.png"
                    filename_json = f"AEE_MFE_{hip}.{hash_params}.json"
                    filepath_png = Path("data/cache") / filename_png
                    filepath_json = Path("data/cache") / filename_json
                    filepath_png.parent.mkdir(parents=True, exist_ok=True)
                    fig.write_image(str(filepath_png), width=1200, height=600)
                    fig.write_json(str(filepath_json))
                    diagramas_generados += 1
                else:
                    if graficos_3d:
                        fig = analizador.generar_diagrama_3d(valores_mfe, 'MFE', hip, escala_graficos)
                    else:
                        fig = analizador.generar_diagrama_2d(valores_mfe, 'MFE', hip, escala_graficos)
                    filename_png = f"AEE_MFE_{hip}.{hash_params}.png"
                    filepath_png = Path("data/cache") / filename_png
                    filepath_png.parent.mkdir(parents=True, exist_ok=True)
                    fig.savefig(str(filepath_png), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    diagramas_generados += 1
                    
        except Exception as e:
            print(f"❌ Error ploteando {hip}: {e}")
            continue
    
    return {
        'exito': True,
        'diagramas_generados': diagramas_generados,
        'mensaje': f'{diagramas_generados} diagramas regenerados'
    }
