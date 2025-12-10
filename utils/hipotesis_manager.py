"""Gestor de hipótesis maestro por estructura"""

import json
import hashlib
import os
from pathlib import Path


class HipotesisManager:
    """Gestiona las hipótesis maestro específicas de cada estructura"""
    
    @staticmethod
    def calcular_hash_estructura(estructura_json_path):
        """Calcula el hash MD5 del archivo .estructura.json"""
        with open(estructura_json_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    @staticmethod
    def obtener_ruta_hipotesis(nombre_estructura):
        """Obtiene la ruta del archivo de hipótesis para una estructura"""
        data_dir = Path(__file__).parent.parent / "data"
        nombre_limpio = nombre_estructura.replace(' ', '_').replace('/', '_')
        return data_dir / f"{nombre_limpio}.hipotesismaestro.json"
    
    @staticmethod
    def cargar_o_crear_hipotesis(nombre_estructura, estructura_json_path, hipotesis_maestro_base):
        """
        Carga las hipótesis si existen y el hash coincide, sino crea nuevas
        
        Args:
            nombre_estructura: Nombre de la estructura
            estructura_json_path: Ruta al archivo .estructura.json
            hipotesis_maestro_base: Diccionario base de hipótesis desde HipotesisMaestro_Especial
            
        Returns:
            dict: Hipótesis maestro a usar
        """
        ruta_hipotesis = HipotesisManager.obtener_ruta_hipotesis(nombre_estructura)
        hash_actual = HipotesisManager.calcular_hash_estructura(estructura_json_path)
        
        # Intentar cargar hipótesis existentes
        if ruta_hipotesis.exists():
            try:
                with open(ruta_hipotesis, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                
                # Verificar hash
                if datos.get('hash_estructura') == hash_actual:
                    print(f"✅ Hipótesis cargadas desde: {ruta_hipotesis.name}")
                    return datos['hipotesis_maestro']
                else:
                    print(f"⚠️ Hash no coincide, regenerando hipótesis...")
            except Exception as e:
                print(f"⚠️ Error al cargar hipótesis: {e}, regenerando...")
        
        # Crear nuevas hipótesis
        print(f"📝 Creando nuevas hipótesis para: {nombre_estructura}")
        HipotesisManager.guardar_hipotesis(nombre_estructura, hash_actual, hipotesis_maestro_base)
        return hipotesis_maestro_base
    
    @staticmethod
    def guardar_hipotesis(nombre_estructura, hash_estructura, hipotesis_maestro):
        """Guarda las hipótesis maestro con su hash"""
        ruta_hipotesis = HipotesisManager.obtener_ruta_hipotesis(nombre_estructura)
        
        datos = {
            'hash_estructura': hash_estructura,
            'hipotesis_maestro': hipotesis_maestro
        }
        
        # Crear directorio si no existe
        ruta_hipotesis.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ruta_hipotesis, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Hipótesis guardadas en: {ruta_hipotesis.name}")
