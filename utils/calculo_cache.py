"""Utilidad para cache y persistencia de cálculos"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from config.app_config import CACHE_DIR, DATA_DIR
import glob


class CalculoCache:
    """Gestiona cache y persistencia de cálculos"""
    
    @staticmethod
    def calcular_hash(estructura_data):
        """Calcula hash MD5 de los parámetros de estructura relevantes para cálculos"""
        # Excluir campos que no afectan cálculos
        params_relevantes = {k: v for k, v in estructura_data.items() 
                            if k not in ['fecha_creacion', 'fecha_modificacion', 'version']}
        # Incluir nodos_editados en hash para invalidar cache si cambian
        data_str = json.dumps(params_relevantes, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    @staticmethod
    def guardar_calculo_cmc(nombre_estructura, estructura_data, resultados_conductor, resultados_guardia, df_cargas_totales, fig_combinado=None, fig_conductor=None, fig_guardia=None, fig_guardia2=None, resultados_guardia2=None, console_output=None, df_conductor_html=None, df_guardia1_html=None, df_guardia2_html=None):
        """Guarda resultados de Cálculo Mecánico de Cables"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        # Guardar imágenes (figuras Plotly) - PNG + JSON
        imagenes_guardadas = []
        figuras = [(fig_combinado, "Combinado"), (fig_conductor, "Conductor"), (fig_guardia, "Guardia")]
        if fig_guardia2:
            figuras.append((fig_guardia2, "Guardia2"))
        
        for fig, nombre in figuras:
            if fig:
                # PNG para exportar
                img_path = CACHE_DIR / f"CMC_{nombre}.{hash_params}.png"
                try:
                    fig.write_image(str(img_path), width=1200, height=600)
                except Exception as e:
                    print(f"Advertencia: No se pudo guardar PNG {nombre}: {e}")
                
                # JSON para interactividad
                json_path = CACHE_DIR / f"CMC_{nombre}.{hash_params}.json"
                try:
                    fig.write_json(str(json_path))
                    imagenes_guardadas.append(nombre)
                except Exception as e:
                    print(f"Advertencia: No se pudo guardar JSON {nombre}: {e}")
        
        if imagenes_guardadas:
            print(f"✅ Gráficos CMC guardados (PNG+JSON): {', '.join(imagenes_guardadas)}")
        else:
            print(f"Advertencia: No se pudieron guardar gráficos CMC")
        
        # Identificar estados determinantes (el de mayor porcentaje de rotura)
        estado_det_cond = max(resultados_conductor.items(), key=lambda x: x[1].get('porcentaje_rotura', 0))[0] if resultados_conductor else None
        estado_det_guard = max(resultados_guardia.items(), key=lambda x: x[1].get('porcentaje_rotura', 0))[0] if resultados_guardia else None
        estado_det_guard2 = max(resultados_guardia2.items(), key=lambda x: x[1].get('porcentaje_rotura', 0))[0] if resultados_guardia2 else None
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "resultados_conductor": resultados_conductor,
            "resultados_guardia": resultados_guardia,
            "resultados_guardia2": resultados_guardia2,
            "estado_determinante_conductor": estado_det_cond,
            "estado_determinante_guardia1": estado_det_guard,
            "estado_determinante_guardia2": estado_det_guard2,
            "df_cargas_totales": df_cargas_totales.to_dict() if df_cargas_totales is not None else None,
            "df_conductor_html": df_conductor_html,
            "df_guardia1_html": df_guardia1_html,
            "df_guardia2_html": df_guardia2_html,
            "imagen_combinado": f"CMC_Combinado.{hash_params}.png" if fig_combinado else None,
            "imagen_conductor": f"CMC_Conductor.{hash_params}.png" if fig_conductor else None,
            "imagen_guardia": f"CMC_Guardia.{hash_params}.png" if fig_guardia else None,
            "console_output": console_output
        }
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoCMC.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_cmc(nombre_estructura):
        """Carga resultados de Cálculo Mecánico de Cables"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoCMC.json"
        if not archivo.exists():
            return None
        
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_dge(nombre_estructura, estructura_data, dimensiones, nodes_key, fig_estructura, fig_cabezal, fig_nodos=None, memoria_calculo=None, conexiones=None):
        """Guarda resultados de Diseño Geométrico de Estructura"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        # Guardar imágenes matplotlib (estructura y cabezal)
        try:
            if fig_estructura:
                img_path = CACHE_DIR / f"Estructura.{hash_params}.png"
                fig_estructura.savefig(str(img_path), format='png', dpi=150, bbox_inches='tight')
            
            if fig_cabezal:
                img_path = CACHE_DIR / f"Cabezal.{hash_params}.png"
                fig_cabezal.savefig(str(img_path), format='png', dpi=150, bbox_inches='tight')
        except Exception as e:
            print(f"Advertencia: No se pudieron guardar imágenes matplotlib DGE: {e}")
        
        # Guardar figura Plotly de nodos (JSON para interactividad)
        if fig_nodos:
            try:
                json_path = CACHE_DIR / f"Nodos.{hash_params}.json"
                fig_nodos.write_json(str(json_path))
                print(f"✅ Gráfico 3D de nodos guardado: Nodos.{hash_params}.json")
            except Exception as e:
                print(f"Advertencia: No se pudo guardar gráfico 3D de nodos: {e}")
        
        # Incluir nodos_editados en cache DGE
        nodos_editados = estructura_data.get("nodos_editados", [])
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "dimensiones": dimensiones,
            "nodes_key": nodes_key,
            "nodos_editados": nodos_editados,
            "conexiones": conexiones if conexiones else [],
            "imagen_estructura": f"Estructura.{hash_params}.png",
            "imagen_cabezal": f"Cabezal.{hash_params}.png",
            "imagen_nodos": f"Nodos.{hash_params}.json" if fig_nodos else None,
            "memoria_calculo": memoria_calculo
        }
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoDGE.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_dge(nombre_estructura):
        """Carga resultados de Diseño Geométrico de Estructura"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoDGE.json"
        if not archivo.exists():
            return None
        
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_dme(nombre_estructura, estructura_data, df_reacciones, fig_polar, fig_barras):
        """Guarda resultados de Diseño Mecánico de Estructura"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        # Guardar imágenes (figuras matplotlib)
        try:
            if fig_polar:
                img_path = CACHE_DIR / f"DME_Polar.{hash_params}.png"
                fig_polar.savefig(str(img_path), format='png', dpi=100)
            
            if fig_barras:
                img_path = CACHE_DIR / f"DME_Barras.{hash_params}.png"
                fig_barras.savefig(str(img_path), format='png', dpi=100)
        except Exception as e:
            print(f"Advertencia: No se pudieron guardar imágenes DME: {e}")
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "df_reacciones": df_reacciones.to_dict(orient='index') if df_reacciones is not None else None,
            "imagen_polar": f"DME_Polar.{hash_params}.png" if fig_polar else None,
            "imagen_barras": f"DME_Barras.{hash_params}.png" if fig_barras else None
        }
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoDME.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_dme(nombre_estructura):
        """Carga resultados de Diseño Mecánico de Estructura"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoDME.json"
        if not archivo.exists():
            return None
        
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_sph(nombre_estructura, estructura_data, resultados, desarrollo_texto):
        """Guarda resultados de Selección de Postes de Hormigón"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "resultados": resultados,
            "desarrollo_texto": desarrollo_texto
        }
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoSPH.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_sph(nombre_estructura):
        """Carga resultados de Selección de Postes de Hormigón"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoSPH.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_arboles(nombre_estructura, estructura_data, imagenes_generadas, df_cargas_completo=None, config_arboles=None):
        """Guarda resultados de Árboles de Carga"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        # Convertir DataFrame con MultiIndex a formato serializable
        df_dict = None
        if df_cargas_completo is not None:
            print(f"📊 Guardando DataFrame de cargas: {df_cargas_completo.shape}")
            # Guardar MultiIndex como listas
            df_dict = {
                'data': df_cargas_completo.values.tolist(),
                'columns': [[str(c) for c in level] for level in df_cargas_completo.columns.levels],
                'column_codes': [level.tolist() for level in df_cargas_completo.columns.codes]
            }
        else:
            print("⚠️ DataFrame de cargas es None, no se guardará")
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "imagenes": [{
                "hipotesis": img['hipotesis'],
                "nombre": img['nombre']
            } for img in imagenes_generadas],
            "df_cargas_completo": df_dict,
            "config_arboles": config_arboles
        }
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoARBOLES.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✅ Cache árboles guardado: {archivo.name}")
        return hash_params
    
    @staticmethod
    def cargar_calculo_arboles(nombre_estructura):
        """Carga resultados de Árboles de Carga"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoARBOLES.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def verificar_vigencia(calculo_guardado, estructura_actual):
        """Verifica si el cálculo guardado sigue vigente"""
        if not calculo_guardado:
            return False, "No hay cálculo guardado"
        
        hash_actual = CalculoCache.calcular_hash(estructura_actual)
        hash_guardado = calculo_guardado.get("hash_parametros")
        
        if hash_actual == hash_guardado:
            return True, "Cálculo vigente"
        else:
            return False, "Se debe recalcular (parámetros modificados)"

    @staticmethod
    def guardar_calculo_todo(nombre_estructura, estructura_data, resultados_completos):
        """Guarda resultados de Calcular Todo"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "resultados": resultados_completos
        }
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoTODO.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_todo(nombre_estructura):
        """Carga resultados de Calcular Todo"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoTODO.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_comparar_cmc(nombre_comparativa, parametros_comparativa, resultados_cables):
        """Guarda resultados de Comparativa CMC"""
        nombre_comparativa = str(nombre_comparativa).replace(' ', '_') if nombre_comparativa else "Sin_Titulo"
        
        # Validar parámetros
        if not parametros_comparativa:
            parametros_comparativa = {}
        if not resultados_cables:
            resultados_cables = {}
            
        hash_params = hashlib.md5(json.dumps(parametros_comparativa, sort_keys=True).encode()).hexdigest()
        
        # Procesar resultados por cable
        dataframes_serializados = {}
        graficos_guardados = {}
        console_output_completo = ""
        
        for cable_nombre, resultado in resultados_cables.items():
            if not resultado or "error" in resultado:
                continue
                
            # Serializar DataFrame
            if "dataframe_html" in resultado and resultado["dataframe_html"]:
                dataframes_serializados[cable_nombre] = resultado["dataframe_html"]
            
            # Guardar gráficos Plotly (JSON para interactividad)
            if "graficos" in resultado and resultado["graficos"]:
                for nombre_grafico, fig in resultado["graficos"].items():
                    if fig:
                        try:
                            # Sanitizar nombres de archivo
                            cable_safe = str(cable_nombre).replace(' ', '_').replace('/', '_')
                            grafico_safe = str(nombre_grafico).replace(' ', '_').replace('/', '_')
                            
                            # Guardar como JSON para interactividad
                            json_path = CACHE_DIR / f"CC_{cable_safe}_{grafico_safe}.{hash_params}.json"
                            fig.write_json(str(json_path))
                            
                            # También PNG para exportar
                            png_path = CACHE_DIR / f"CC_{cable_safe}_{grafico_safe}.{hash_params}.png"
                            fig.write_image(str(png_path), width=1200, height=600)
                            
                            if cable_nombre not in graficos_guardados:
                                graficos_guardados[cable_nombre] = {}
                            graficos_guardados[cable_nombre][nombre_grafico] = {
                                "json": f"CC_{cable_safe}_{grafico_safe}.{hash_params}.json",
                                "png": f"CC_{cable_safe}_{grafico_safe}.{hash_params}.png"
                            }
                        except Exception as e:
                            print(f"Error guardando gráfico {nombre_grafico} para {cable_nombre}: {e}")
        
        # Crear gráfico comparativo y guardarlo
        try:
            from utils.comparativa_cmc_calculo import crear_grafico_comparativo
            fig_flechas, fig_tiros = crear_grafico_comparativo(resultados_cables)
            if fig_flechas and fig_tiros:
                # Guardar gráfico de flechas
                json_path_flechas = CACHE_DIR / f"CC_Flechas.{hash_params}.json"
                png_path_flechas = CACHE_DIR / f"CC_Flechas.{hash_params}.png"
                fig_flechas.write_json(str(json_path_flechas))
                fig_flechas.write_image(str(png_path_flechas), width=1200, height=600)
                
                # Guardar gráfico de tiros
                json_path_tiros = CACHE_DIR / f"CC_Tiros.{hash_params}.json"
                png_path_tiros = CACHE_DIR / f"CC_Tiros.{hash_params}.png"
                fig_tiros.write_json(str(json_path_tiros))
                fig_tiros.write_image(str(png_path_tiros), width=1200, height=600)
                
                graficos_guardados["comparativo"] = {
                    "flechas": {
                        "json": f"CC_Flechas.{hash_params}.json",
                        "png": f"CC_Flechas.{hash_params}.png"
                    },
                    "tiros": {
                        "json": f"CC_Tiros.{hash_params}.json",
                        "png": f"CC_Tiros.{hash_params}.png"
                    }
                }
        except Exception as e:
            print(f"Error guardando gráfico comparativo: {e}")
        
        calculo_data = {
            "nombre_comparativa": str(nombre_comparativa),
            "parametros": parametros_comparativa,
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "resultados": {
                "cables_calculados": [str(cable) for cable in resultados_cables.keys() if resultados_cables.get(cable) and "error" not in resultados_cables[cable]],
                "dataframes": dataframes_serializados,
                "graficos": graficos_guardados,
                "errores": {str(cable): str(resultado.get("error", "Error desconocido")) for cable, resultado in resultados_cables.items() if resultado and "error" in resultado},
                "console_output": str(console_output_completo)
            }
        }
        
        archivo = CACHE_DIR / f"{nombre_comparativa}.calculoCompararCMC.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✅ Cache comparativa guardado: {archivo.name}")
        return hash_params
    
    @staticmethod
    def cargar_calculo_comparar_cmc(nombre_comparativa):
        """Carga resultados de Comparativa CMC"""
        nombre_comparativa = nombre_comparativa.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_comparativa}.calculoCompararCMC.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_fund(nombre_estructura, estructura_data, parametros, resultados, fig_3d=None):
        """Guarda resultados de Cálculo de Fundaciones"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        # Guardar gráfico 3D si existe (PNG + JSON)
        if fig_3d:
            try:
                # PNG para exportar
                png_path = CACHE_DIR / f"FUND_3D.{hash_params}.png"
                fig_3d.write_image(str(png_path), width=1200, height=800)
                
                # JSON para interactividad
                json_path = CACHE_DIR / f"FUND_3D.{hash_params}.json"
                fig_3d.write_json(str(json_path))
                
                print(f"✅ Gráfico 3D fundación guardado: PNG + JSON")
            except Exception as e:
                print(f"Advertencia: No se pudo guardar gráfico 3D: {e}")
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "parametros": parametros,
            "resultados": resultados,
            "imagen_3d": f"FUND_3D.{hash_params}.json" if fig_3d else None
        }
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoFUND.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_fund(nombre_estructura):
        """Carga resultados de Cálculo de Fundaciones"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoFUND.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_costeo(nombre_estructura, estructura_data, parametros_precios, resultados):
        """Guarda resultados de Cálculo de Costeo"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        
        # Hash basado solo en estructura (los precios no afectan la validez estructural)
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "parametros_precios": parametros_precios,
            "resultados": resultados
        }
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoCOSTEO.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_costeo(nombre_estructura):
        """Carga resultados de Cálculo de Costeo"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoCOSTEO.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def eliminar_cache_estructura(nombre_estructura):
        """Elimina todos los archivos de cache de una estructura"""
        tipos = ['CMC', 'DGE', 'DME', 'ARBOLES', 'SPH', 'TODO', 'FUND', 'COSTEO']
        eliminados = []
        
        for tipo in tipos:
            archivo = CACHE_DIR / f"{nombre_estructura}.calculo{tipo}.json"
            if archivo.exists():
                archivo.unlink()
                eliminados.append(tipo)
        
        # Eliminar imágenes asociadas
        patrones = [
            f"CMC_*.*.png",
            f"CMC_*.*.json",
            f"Estructura.*.png",
            f"Cabezal.*.png",
            f"Nodos.*.json",
            f"DME_*.*.png",
            f"FUND_3D.*.png",
            f"FUND_3D.*.json",
            f"{nombre_estructura}.arbolcarga.*.*.png"
        ]
        
        for patron in patrones:
            for archivo in CACHE_DIR.glob(patron):
                try:
                    archivo.unlink()
                except Exception as e:
                    print(f"No se pudo eliminar {archivo}: {e}")
        
        if eliminados:
            print(f"✅ Cache eliminado: {', '.join(eliminados)}")
        return eliminados
    
    @staticmethod
    def calcular_hash_familia(familia_data):
        """Calcula hash MD5 de familia para validación de cache"""
        familia_hash = {k: v for k, v in familia_data.items() 
                        if k not in ['fecha_creacion', 'fecha_modificacion']}
        data_str = json.dumps(familia_hash, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def guardar_calculo_familia(nombre_familia, familia_data, resultados_familia):
        """Guarda referencias a caches individuales de cada estructura"""
        nombre_familia = nombre_familia.replace(' ', '_')
        hash_params = CalculoCache.calcular_hash_familia(familia_data)
        
        # Solo guardar referencias a caches individuales, no duplicar datos
        referencias_estructuras = {}
        for nombre_estr, datos in resultados_familia.get("resultados_estructuras", {}).items():
            titulo = datos.get("titulo", nombre_estr)
            referencias_estructuras[nombre_estr] = {
                "titulo": titulo,
                "cantidad": datos.get("cantidad", 1),
                "costo_individual": datos.get("costo_individual", 0),
                # Referencias a caches individuales existentes
                "cache_refs": {
                    "cmc": f"{titulo}.calculoCMC.json",
                    "dge": f"{titulo}.calculoDGE.json",
                    "dme": f"{titulo}.calculoDME.json",
                    "arboles": f"{titulo}.calculoARBOLES.json",
                    "sph": f"{titulo}.calculoSPH.json",
                    "fundacion": f"{titulo}.calculoFUND.json",
                    "costeo": f"{titulo}.calculoCOSTEO.json"
                }
            }
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "estructuras": referencias_estructuras,
            "costeo_global": resultados_familia.get("costeo_global", {})
        }
        
        archivo = CACHE_DIR / f"{nombre_familia}.calculoFAMILIA.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✅ Cache familia guardado: {archivo.name}")
        return hash_params
    
    @staticmethod
    def cargar_calculo_familia(nombre_familia):
        """Carga cache de familia y reconstruye desde caches individuales"""
        nombre_familia = nombre_familia.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_familia}.calculoFAMILIA.json"
        
        if not archivo.exists():
            return None
        
        cache_familia = json.loads(archivo.read_text(encoding="utf-8"))
        
        # Reconstruir resultados desde caches individuales
        resultados_estructuras = {}
        for nombre_estr, datos in cache_familia.get("estructuras", {}).items():
            titulo = datos["titulo"]
            
            # Cargar caches individuales
            resultados = {}
            for tipo, archivo_ref in datos.get("cache_refs", {}).items():
                archivo_cache = CACHE_DIR / archivo_ref
                if archivo_cache.exists():
                    try:
                        resultados[tipo] = json.loads(archivo_cache.read_text(encoding="utf-8"))
                    except:
                        pass
            
            resultados_estructuras[nombre_estr] = {
                "titulo": titulo,
                "cantidad": datos.get("cantidad", 1),
                "costo_individual": datos.get("costo_individual", 0),
                "resultados": resultados
            }
        
        return {
            "hash_parametros": cache_familia.get("hash_parametros"),
            "fecha_calculo": cache_familia.get("fecha_calculo"),
            "resultados": {
                "exito": True,
                "resultados_estructuras": resultados_estructuras,
                "costeo_global": cache_familia.get("costeo_global", {})
            }
        }
    
    @staticmethod
    def verificar_vigencia_familia(calculo_guardado, familia_actual):
        """Verifica si el cache de familia sigue vigente"""
        if not calculo_guardado:
            return False, "Cache no disponible"
        
        hash_actual = CalculoCache.calcular_hash_familia(familia_actual)
        hash_guardado = calculo_guardado.get("hash_parametros")
        
        if hash_actual == hash_guardado:
            return True, "Cache vigente"
        else:
            return False, "Hash no coincide, recalcular"
    
    @staticmethod
    def guardar_calculo_vano_economico(nombre_familia, parametros, resultados):
        """Guarda resultados de Vano Económico"""
        nombre_familia = nombre_familia.replace(' ', '_')
        
        # Hash basado en parámetros de vano
        hash_params = hashlib.md5(json.dumps(parametros, sort_keys=True).encode()).hexdigest()
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "parametros": parametros,
            "resultados": resultados
        }
        
        archivo = CACHE_DIR / f"{nombre_familia}.calculoVANOECONOMICO.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✅ Cache vano económico guardado: {archivo.name}")
        return hash_params
    
    @staticmethod
    def cargar_calculo_vano_economico(nombre_familia):
        """Carga resultados de Vano Económico"""
        nombre_familia = nombre_familia.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_familia}.calculoVANOECONOMICO.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_aee(nombre_estructura, estructura_data, resultados):
        """Guarda resultados de Análisis Estático de Esfuerzos (AEE)"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        # Preferir el hash calculado en los resultados si está disponible (evita inconsistencias al re-escribir cache)
        hash_params = resultados.get('hash') if isinstance(resultados, dict) and 'hash' in resultados else CalculoCache.calcular_hash(estructura_data)
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "resultados": resultados
        }
        
        # Reconstruir/añadir entradas de 'diagramas' si existen PNGs ya generados con este hash
        try:
            png_pattern = f"AEE_*.{hash_params}.png"
            for png_path in CACHE_DIR.glob(png_pattern):
                nombre_png = png_path.name
                # Extraer la clave: remover prefijo 'AEE_' y sufijo '.{hash}.png'
                clave = nombre_png[len('AEE_'):-len(f'.{hash_params}.png')]
                if 'resultados' not in calculo_data:
                    calculo_data['resultados'] = {}
                if 'diagramas' not in calculo_data['resultados']:
                    calculo_data['resultados']['diagramas'] = {}
                # Registrar filename (no path)
                calculo_data['resultados']['diagramas'][clave] = nombre_png
        except Exception as e:
            print(f"⚠️ No se pudo reconstruir diagramas desde PNGs: {e}")
        
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoAEE.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✅ Cache AEE guardado: {archivo.name}")
        return hash_params
    
    @staticmethod
    def cargar_calculo_aee(nombre_estructura):
        """Carga resultados de Análisis Estático de Esfuerzos (AEE)"""
        nombre_estructura = nombre_estructura.replace(' ', '_')
        archivo = CACHE_DIR / f"{nombre_estructura}.calculoAEE.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
