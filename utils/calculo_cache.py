"""Utilidad para cache y persistencia de cálculos"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from config.app_config import DATA_DIR
import glob


class CalculoCache:
    """Gestiona cache y persistencia de cálculos"""
    
    @staticmethod
    def calcular_hash(estructura_data):
        """Calcula hash MD5 de los parámetros de estructura"""
        # Serializar datos y calcular hash
        data_str = json.dumps(estructura_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    @staticmethod
    def guardar_calculo_cmc(nombre_estructura, estructura_data, resultados_conductor, resultados_guardia, df_cargas_totales, fig_combinado=None, fig_conductor=None, fig_guardia=None):
        """Guarda resultados de Cálculo Mecánico de Cables"""
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        # Guardar imágenes (figuras Plotly)
        try:
            if fig_combinado:
                img_path = DATA_DIR / f"CMC_Combinado.{hash_params}.png"
                fig_combinado.write_image(str(img_path), width=1200, height=600)
            
            if fig_conductor:
                img_path = DATA_DIR / f"CMC_Conductor.{hash_params}.png"
                fig_conductor.write_image(str(img_path), width=1200, height=600)
            
            if fig_guardia:
                img_path = DATA_DIR / f"CMC_Guardia.{hash_params}.png"
                fig_guardia.write_image(str(img_path), width=1200, height=600)
        except Exception as e:
            print(f"Advertencia: No se pudieron guardar imágenes CMC: {e}")
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "resultados_conductor": resultados_conductor,
            "resultados_guardia": resultados_guardia,
            "df_cargas_totales": df_cargas_totales.to_dict() if df_cargas_totales is not None else None,
            "imagen_combinado": f"CMC_Combinado.{hash_params}.png" if fig_combinado else None,
            "imagen_conductor": f"CMC_Conductor.{hash_params}.png" if fig_conductor else None,
            "imagen_guardia": f"CMC_Guardia.{hash_params}.png" if fig_guardia else None
        }
        
        archivo = DATA_DIR / f"{nombre_estructura}.calculoCMC.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_cmc(nombre_estructura):
        """Carga resultados de Cálculo Mecánico de Cables"""
        archivo = DATA_DIR / f"{nombre_estructura}.calculoCMC.json"
        if not archivo.exists():
            return None
        
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_dge(nombre_estructura, estructura_data, dimensiones, nodes_key, fig_estructura, fig_cabezal):
        """Guarda resultados de Diseño Geométrico de Estructura"""
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        # Guardar imágenes (figuras matplotlib)
        try:
            if fig_estructura:
                img_path = DATA_DIR / f"Estructura.{hash_params}.png"
                fig_estructura.savefig(str(img_path), format='png', dpi=150, bbox_inches='tight')
            
            if fig_cabezal:
                img_path = DATA_DIR / f"Cabezal.{hash_params}.png"
                fig_cabezal.savefig(str(img_path), format='png', dpi=150, bbox_inches='tight')
        except Exception as e:
            print(f"Advertencia: No se pudieron guardar imágenes DGE: {e}")
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "dimensiones": dimensiones,
            "nodes_key": nodes_key,
            "imagen_estructura": f"Estructura.{hash_params}.png",
            "imagen_cabezal": f"Cabezal.{hash_params}.png"
        }
        
        archivo = DATA_DIR / f"{nombre_estructura}.calculoDGE.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_dge(nombre_estructura):
        """Carga resultados de Diseño Geométrico de Estructura"""
        archivo = DATA_DIR / f"{nombre_estructura}.calculoDGE.json"
        if not archivo.exists():
            return None
        
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_dme(nombre_estructura, estructura_data, df_reacciones, fig_polar, fig_barras):
        """Guarda resultados de Diseño Mecánico de Estructura"""
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        # Guardar imágenes (figuras matplotlib)
        try:
            if fig_polar:
                img_path = DATA_DIR / f"DME_Polar.{hash_params}.png"
                fig_polar.savefig(str(img_path), format='png', dpi=100)
            
            if fig_barras:
                img_path = DATA_DIR / f"DME_Barras.{hash_params}.png"
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
        
        archivo = DATA_DIR / f"{nombre_estructura}.calculoDME.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_dme(nombre_estructura):
        """Carga resultados de Diseño Mecánico de Estructura"""
        archivo = DATA_DIR / f"{nombre_estructura}.calculoDME.json"
        if not archivo.exists():
            return None
        
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_sph(nombre_estructura, calculo_data):
        """Guarda resultados de Selección de Postes de Hormigón"""
        archivo = DATA_DIR / f"{nombre_estructura}.calculoSPH.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return calculo_data.get('hash_parametros')
    
    @staticmethod
    def cargar_calculo_sph(nombre_estructura):
        """Carga resultados de Selección de Postes de Hormigón"""
        archivo = DATA_DIR / f"{nombre_estructura}.calculoSPH.json"
        if not archivo.exists():
            return None
        return json.loads(archivo.read_text(encoding="utf-8"))
    
    @staticmethod
    def guardar_calculo_arboles(nombre_estructura, estructura_data, imagenes_generadas):
        """Guarda resultados de Árboles de Carga"""
        hash_params = CalculoCache.calcular_hash(estructura_data)
        
        calculo_data = {
            "hash_parametros": hash_params,
            "fecha_calculo": datetime.now().isoformat(),
            "imagenes": [{
                "hipotesis": img['hipotesis'],
                "nombre": img['nombre']
            } for img in imagenes_generadas]
        }
        
        archivo = DATA_DIR / f"{nombre_estructura}.calculoARBOLES.json"
        archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return hash_params
    
    @staticmethod
    def cargar_calculo_arboles(nombre_estructura):
        """Carga resultados de Árboles de Carga"""
        archivo = DATA_DIR / f"{nombre_estructura}.calculoARBOLES.json"
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
