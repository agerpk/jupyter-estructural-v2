"""Utilidad para cache y persistencia de cálculos"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from config.app_config import CACHE_DIR
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
    def eliminar_cache(nombre_estructura):
        """Elimina todos los archivos de cache de una estructura"""
        tipos = ['CMC', 'DGE', 'DME', 'ARBOLES', 'SPH', 'TODO']
        eliminados = []
        
        for tipo in tipos:
            archivo = CACHE_DIR / f"{nombre_estructura}.calculo{tipo}.json"
            if archivo.exists():
                archivo.unlink()
                eliminados.append(tipo)
        
        # Eliminar imágenes asociadas
        patrones = [
            f"CMC_*.*.png",
            f"Estructura.*.png",
            f"Cabezal.*.png",
            f"DME_*.*.png",
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
