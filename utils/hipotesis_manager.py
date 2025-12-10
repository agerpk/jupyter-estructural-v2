"""Gestor de hipótesis maestro por estructura"""

import json
import hashlib
import os
from pathlib import Path
from config.app_config import DATA_DIR


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
    def cargar_o_crear_hipotesis(nombre_estructura, estructura_json_path, hipotesis_maestro_base, nombre_estructura_origen=None):
        """
        Carga las hipótesis si existen y el hash coincide, sino crea nuevas
        
        Args:
            nombre_estructura: Nombre de la estructura
            estructura_json_path: Ruta al archivo .estructura.json
            hipotesis_maestro_base: Diccionario base de hipótesis desde HipotesisMaestro_Especial
            nombre_estructura_origen: Nombre de la estructura origen (para Guardar Como)
            
        Returns:
            dict: Hipótesis maestro a usar
        """
        from pathlib import Path
        
        # Verificar que el archivo .estructura.json existe
        if not Path(estructura_json_path).exists():
            print(f"⚠️ Archivo estructura no existe: {estructura_json_path}")
            print(f"📝 Usando hipótesis base para: {nombre_estructura}")
            return hipotesis_maestro_base
        
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
        
        # Si hay estructura origen, intentar copiar sus hipótesis
        if nombre_estructura_origen:
            ruta_hipotesis_origen = HipotesisManager.obtener_ruta_hipotesis(nombre_estructura_origen)
            if ruta_hipotesis_origen.exists():
                try:
                    with open(ruta_hipotesis_origen, 'r', encoding='utf-8') as f:
                        datos_origen = json.load(f)
                    hipotesis_a_usar = datos_origen['hipotesis_maestro']
                    print(f"📋 Copiando hipótesis desde: {nombre_estructura_origen}")
                    HipotesisManager.guardar_hipotesis(nombre_estructura, hash_actual, hipotesis_a_usar)
                    return hipotesis_a_usar
                except Exception as e:
                    print(f"⚠️ Error al copiar hipótesis origen: {e}, usando base...")
        
        # Crear nuevas hipótesis desde base
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
    
    @staticmethod
    def copiar_hipotesis_guardar_como(nombre_origen, nombre_destino, estructura_json_path_destino):
        """
        Copia hipótesis de estructura origen a nueva estructura (Guardar Como)
        
        Args:
            nombre_origen: Nombre de la estructura origen
            nombre_destino: Nombre de la nueva estructura
            estructura_json_path_destino: Ruta al nuevo archivo .estructura.json
        """
        ruta_origen = HipotesisManager.obtener_ruta_hipotesis(nombre_origen)
        
        if ruta_origen.exists():
            try:
                # Cargar hipótesis origen
                with open(ruta_origen, 'r', encoding='utf-8') as f:
                    datos_origen = json.load(f)
                
                # Calcular nuevo hash
                hash_destino = HipotesisManager.calcular_hash_estructura(estructura_json_path_destino)
                
                # Guardar con nuevo hash
                HipotesisManager.guardar_hipotesis(
                    nombre_destino,
                    hash_destino,
                    datos_origen['hipotesis_maestro']
                )
                print(f"✅ Hipótesis copiadas: {nombre_origen} → {nombre_destino}")
                return True
            except Exception as e:
                print(f"❌ Error al copiar hipótesis: {e}")
                return False
        return False
    
    @staticmethod
    def actualizar_hash_hipotesis(nombre_estructura, estructura_json_path):
        """
        Actualiza el hash en el archivo de hipótesis cuando se modifica .estructura.json
        
        Args:
            nombre_estructura: Nombre de la estructura
            estructura_json_path: Ruta al archivo .estructura.json modificado
        """
        ruta_hipotesis = HipotesisManager.obtener_ruta_hipotesis(nombre_estructura)
        
        if ruta_hipotesis.exists():
            try:
                # Cargar hipótesis existentes
                with open(ruta_hipotesis, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                
                # Calcular nuevo hash
                hash_nuevo = HipotesisManager.calcular_hash_estructura(estructura_json_path)
                
                # Actualizar hash
                datos['hash_estructura'] = hash_nuevo
                
                # Guardar
                with open(ruta_hipotesis, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=2, ensure_ascii=False)
                
                print(f"🔄 Hash actualizado en: {ruta_hipotesis.name}")
                return True
            except Exception as e:
                print(f"❌ Error al actualizar hash: {e}")
                return False
        return False
