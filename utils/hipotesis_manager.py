"""Gestor de archivos de hipótesis"""

import json
import os
from pathlib import Path
from config.app_config import DATA_DIR


class HipotesisManager:
    """Gestiona el CRUD y la activación de archivos de hipótesis."""
    
    @staticmethod
    def obtener_ruta_hipotesis(nombre_hipotesis):
        """Obtiene la ruta del archivo de hipótesis (en data/hipotesis)."""
        hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
        hipotesis_dir.mkdir(parents=True, exist_ok=True)
        nombre_limpio = nombre_hipotesis.replace(' ', '_').replace('/', '_')
        if nombre_limpio.endswith('.hipotesis.json'):
            nombre_limpio = nombre_limpio.replace('.hipotesis.json', '')
            
        return hipotesis_dir / f"{nombre_limpio}.hipotesis.json"
    
    @staticmethod
    def guardar_hipotesis(nombre_hipotesis, datos_hipotesis):
        """Guarda un archivo de hipótesis."""
        ruta_hipotesis = HipotesisManager.obtener_ruta_hipotesis(nombre_hipotesis)
        
        # Crear directorio si no existe
        ruta_hipotesis.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ruta_hipotesis, 'w', encoding='utf-8') as f:
            json.dump(datos_hipotesis, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Hipótesis guardadas en: {ruta_hipotesis.name}")

    @staticmethod
    def eliminar_hipotesis(nombre_hipotesis):
        """Elimina el archivo de hipótesis correspondiente si existe."""
        ruta = HipotesisManager.obtener_ruta_hipotesis(nombre_hipotesis)
        if ruta.exists():
            try:
                ruta.unlink()
                print(f"🗑️ Hipótesis eliminada: {ruta.name}")
                return True
            except Exception as e:
                print(f"❌ Error eliminando hipótesis: {e}")
                return False
        print(f"⚠️ Hipótesis no encontrada: {ruta.name}")
        return False

    @staticmethod
    def listar_hipotesis():
        """Lista archivos de hipótesis disponibles en data/hipotesis."""
        hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
        hipotesis_dir.mkdir(parents=True, exist_ok=True)
        return [p.name for p in hipotesis_dir.glob("*.hipotesis.json")]

    @staticmethod
    def cargar_hipotesis_por_nombre(nombre_hipotesis):
        """Carga y retorna el contenido del archivo de hipótesis si existe."""
        ruta = HipotesisManager.obtener_ruta_hipotesis(nombre_hipotesis)
        if not ruta.exists():
            return None
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def establecer_hipotesis_activa(nombre_hipotesis):
        """Establece la hipótesis activa globalmente (escribe data/hipotesis/activo.json)."""
        hipotesis_dir = Path(__file__).parent.parent / "data" / "hipotesis"
        hipotesis_dir.mkdir(parents=True, exist_ok=True)
        activo_path = hipotesis_dir / "activo.json"
        
        nombre_archivo = f"{nombre_hipotesis}.hipotesis.json"
        if not nombre_hipotesis.endswith('.hipotesis.json'):
             nombre_archivo = f"{nombre_hipotesis}.hipotesis.json"
        else:
            nombre_archivo = nombre_hipotesis

        activo_path.write_text(json.dumps({"hipotesis_activa": nombre_archivo}, ensure_ascii=False), encoding='utf-8')
        print(f"✅ Hipótesis activa establecida: {nombre_archivo}")
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
            return destino
        except Exception as e:
            print(f"❌ Error importando hipótesis: {e}")
            return False
