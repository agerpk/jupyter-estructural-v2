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
        """Obtiene la ruta del archivo de hipótesis para una estructura (en data/hipotesis)."""
        hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
        hipotesis_dir.mkdir(parents=True, exist_ok=True)
        nombre_limpio = nombre_estructura.replace(' ', '_').replace('/', '_')
        return hipotesis_dir / f"{nombre_limpio}.hipotesis.json"
    
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
                    print(f"USANDO HIPÓTESIS: {ruta_hipotesis.name}")
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
    def listar_hipotesis():
        """Lista archivos de hipótesis disponibles en data/hipotesis."""
        hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
        hipotesis_dir.mkdir(parents=True, exist_ok=True)
        return [p.name for p in hipotesis_dir.glob("*.hipotesis.json")]

    @staticmethod
    def cargar_hipotesis_por_nombre(nombre_estructura):
        """Carga y retorna el contenido del archivo de hipótesis si existe."""
        ruta = HipotesisManager.obtener_ruta_hipotesis(nombre_estructura)
        if not ruta.exists():
            return None
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def establecer_hipotesis_activa(nombre_estructura):
        """Establece la hipótesis activa globalmente (escribe data/hipotesis/activo.json)."""
        hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
        hipotesis_dir.mkdir(parents=True, exist_ok=True)
        activo_path = hipotesis_dir / "activo.json"
        activo_path.write_text(json.dumps({"hipotesis_activa": f"{nombre_estructura}.hipotesis.json"}, ensure_ascii=False), encoding='utf-8')
        print(f"✅ Hipótesis activa establecida: {nombre_estructura}.hipotesis.json")
        return activo_path

    @staticmethod
    def obtener_hipotesis_activa():
        """Devuelve el nombre de la hipótesis activa si existe (ej. 'proyecto.hipotesis.json'), o None."""
        hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
        activo_path = hipotesis_dir / "activo.json"
        if not activo_path.exists():
            return None
        try:
            datos = json.loads(activo_path.read_text(encoding='utf-8'))
            return datos.get('hipotesis_activa')
        except Exception as e:
            print(f"⚠️ Error leyendo activo.json: {e}")
            return None

    @staticmethod
    def cargar_hipotesis_activa():
        """Carga el contenido de la hipótesis activa (archivo en data/hipotesis) y retorna el dict o None."""
        nombre = HipotesisManager.obtener_hipotesis_activa()
        if not nombre:
            return None
        hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
        ruta = hipotesis_dir / nombre
        if not ruta.exists():
            print(f"⚠️ Archivo de hipótesis activa no encontrado: {ruta}")
            return None
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error al cargar hipótesis activa: {e}")
            return None

    @staticmethod
    def validar_hipotesis(hipotesis_maestro):
        """Valida la estructura básica de un diccionario de hipótesis maestro.
        Retorna (bool, mensaje).
        """
        if not isinstance(hipotesis_maestro, dict):
            return False, "Hipótesis maestro debe ser un diccionario"
        if not hipotesis_maestro:
            return False, "Hipótesis maestro está vacío"
        # Check that each hipotesis entry is a dict
        for k, v in hipotesis_maestro.items():
            if not isinstance(v, dict):
                return False, f"Entrada de hipótesis '{k}' no es un diccionario"
        return True, "OK"

    @staticmethod
    def importar_hipotesis_desde_archivo(ruta_externa):
        """Importa un archivo JSON de hipótesis y lo guarda en data/hipotesis con su nombre base."""
        ruta_externa = Path(ruta_externa)
        if not ruta_externa.exists():
            print(f"⚠️ Archivo externo no existe: {ruta_externa}")
            return False
        try:
            with open(ruta_externa, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            nombre_destino = ruta_externa.stem + '.hipotesis.json'
            hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
            hipotesis_dir.mkdir(parents=True, exist_ok=True)
            destino = hipotesis_dir / nombre_destino
            with open(destino, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            print(f"✅ Hipótesis importada: {destino.name}")
            return True
        except Exception as e:
            print(f"❌ Error importando hipótesis: {e}")
            return False
    
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
        
        # Solo actualizar si el archivo de hipótesis existe
        if ruta_hipotesis.exists():
            try:
                # Cargar hipótesis existentes
                with open(ruta_hipotesis, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                
                # Calcular nuevo hash
                hash_nuevo = HipotesisManager.calcular_hash_estructura(estructura_json_path)
                
                # Solo actualizar si el hash cambió
                if datos.get('hash_estructura') != hash_nuevo:
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
