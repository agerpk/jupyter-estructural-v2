"""
AGP - Gestor de estructuras para carga y guardado de archivos JSON
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import copy
import datetime

class EstructuraManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.plantilla_path = data_dir / "plantilla.estructura.json"
        
    def cargar_estructura(self, ruta_archivo: Path) -> Dict[str, Any]:
        """Cargar estructura desde archivo JSON"""
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Si no existe, cargar plantilla
            return self.cargar_plantilla()
        except json.JSONDecodeError:
            raise ValueError("Archivo JSON corrupto")
    
    def cargar_plantilla(self) -> Dict[str, Any]:
        """Cargar estructura de plantilla"""
        try:
            with open(self.plantilla_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Crear estructura básica si no existe plantilla
            return {
                "TIPO_ESTRUCTURA": "Suspensión Recta",
                "TITULO": "Estructura Base",
                "fecha_creacion": datetime.datetime.now().isoformat(),
                "version": "1.0"
            }
    
    def guardar_estructura(self, estructura: Dict[str, Any], ruta_destino: Path):
        """Guardar estructura en archivo JSON"""
        # Añadir metadatos de modificación
        estructura_modificada = copy.deepcopy(estructura)
        estructura_modificada["fecha_modificacion"] = datetime.datetime.now().isoformat()
        estructura_modificada["version"] = "1.0"
        
        with open(ruta_destino, 'w', encoding='utf-8') as f:
            json.dump(estructura_modificada, f, indent=2, ensure_ascii=False)
        
        # Actualizar hash de hipótesis si existe
        try:
            from utils.hipotesis_manager import HipotesisManager
            nombre_estructura = estructura.get('TITULO', '')
            if nombre_estructura:
                HipotesisManager.actualizar_hash_hipotesis(nombre_estructura, str(ruta_destino))
        except Exception as e:
            print(f"⚠️ No se pudo actualizar hash de hipótesis: {e}")
    
    def listar_estructuras(self) -> List[str]:
        """Listar todas las estructuras en la base de datos"""
        estructuras = []
        for archivo in self.data_dir.glob("*.estructura.json"):
            # Excluir archivos especiales
            if archivo.name not in ["actual.estructura.json", "plantilla.estructura.json"]:
                estructuras.append(archivo.name)
        return sorted(estructuras)
    
    def eliminar_estructura(self, nombre_archivo: str) -> bool:
        """Eliminar estructura de la base de datos"""
        ruta_archivo = self.data_dir / nombre_archivo
        
        # No permitir eliminar archivos especiales
        if nombre_archivo in ["actual.estructura.json", "plantilla.estructura.json"]:
            return False
        
        if ruta_archivo.exists():
            ruta_archivo.unlink()
            return True
        return False
    
    def crear_nueva_estructura(self, titulo: str = None) -> Dict[str, Any]:
        """Crear nueva estructura basada en plantilla"""
        estructura = self.cargar_plantilla()
        
        if titulo:
            estructura["TITULO"] = titulo
        else:
            # Generar título automático
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            estructura["TITULO"] = f"Nueva_Estructura_{timestamp}"
        
        return estructura
    
    def actualizar_parametros(self, parametros: Dict[str, Any]):
        """Actualizar parámetros de estructura actual y guardar en ambos archivos"""
        ruta_actual = self.data_dir / "actual.estructura.json"
        estructura = self.cargar_estructura(ruta_actual)
        estructura.update(parametros)
        
        # Guardar en archivo con nombre de título
        titulo = estructura.get("TITULO", "estructura")
        nombre_archivo = f"{titulo}.estructura.json"
        ruta_titulo = self.data_dir / nombre_archivo
        
        self.guardar_estructura(estructura, ruta_titulo)
        self.guardar_estructura(estructura, ruta_actual)