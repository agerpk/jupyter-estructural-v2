"""
Manager para operaciones con Familias de Estructuras
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import hashlib

class FamiliaManager:
    """Manager para operaciones con familias de estructuras"""
    
    DATA_DIR = Path("data")
    
    @classmethod
    def cargar_familia_actual(cls) -> Dict:
        """Cargar familia actual o crear nueva"""
        try:
            # Intentar cargar última familia usada
            estado_file = cls.DATA_DIR / "familia_actual.json"
            if estado_file.exists():
                with open(estado_file, "r", encoding="utf-8") as f:
                    estado = json.load(f)
                    nombre_familia = estado.get("nombre_familia")
                    if nombre_familia:
                        return cls.cargar_familia(nombre_familia)
        except:
            pass
        
        # Crear familia nueva con plantilla
        return cls._crear_familia_nueva()
    
    @classmethod
    def _crear_familia_nueva(cls) -> Dict:
        """Crear nueva familia con plantilla"""
        plantilla = cls._cargar_plantilla()
        
        # Agregar campo cantidad
        plantilla["cantidad"] = 1
        
        return {
            "nombre_familia": "",
            "fecha_creacion": datetime.now().isoformat(),
            "fecha_modificacion": datetime.now().isoformat(),
            "estructuras": {
                "Estr.1": plantilla
            }
        }
    
    @classmethod
    def _cargar_plantilla(cls) -> Dict:
        """Cargar plantilla de estructura"""
        try:
            with open(cls.DATA_DIR / "plantilla.estructura.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    @classmethod
    def guardar_familia(cls, familia_data: Dict) -> None:
        """Guardar familia en archivo"""
        nombre_familia = familia_data["nombre_familia"]
        if not nombre_familia:
            raise ValueError("Nombre de familia requerido")
        
        # Sanitizar nombre
        nombre_archivo = nombre_familia.replace(" ", "_").replace("/", "_")
        archivo_familia = cls.DATA_DIR / f"{nombre_archivo}.familia.json"
        
        # Actualizar fecha modificación
        familia_data["fecha_modificacion"] = datetime.now().isoformat()
        
        # Guardar archivo
        with open(archivo_familia, "w", encoding="utf-8") as f:
            json.dump(familia_data, f, indent=2, ensure_ascii=False)
        
        # Guardar como familia actual
        cls._guardar_familia_actual(nombre_familia)
    
    @classmethod
    def _guardar_familia_actual(cls, nombre_familia: str) -> None:
        """Guardar referencia a familia actual"""
        estado = {
            "nombre_familia": nombre_familia,
            "fecha_acceso": datetime.now().isoformat()
        }
        
        with open(cls.DATA_DIR / "familia_actual.json", "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def cargar_familia(cls, nombre_familia: str) -> Dict:
        """Cargar familia por nombre"""
        nombre_archivo = nombre_familia.replace(" ", "_").replace("/", "_")
        archivo_familia = cls.DATA_DIR / f"{nombre_archivo}.familia.json"
        
        if not archivo_familia.exists():
            raise FileNotFoundError(f"Familia '{nombre_familia}' no encontrada")
        
        with open(archivo_familia, "r", encoding="utf-8") as f:
            familia_data = json.load(f)
        
        # Actualizar familia actual
        cls._guardar_familia_actual(nombre_familia)
        
        return familia_data
    
    @classmethod
    def listar_familias_disponibles(cls) -> List[str]:
        """Listar familias disponibles"""
        familias = []
        
        for archivo in cls.DATA_DIR.glob("*.familia.json"):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    nombre = data.get("nombre_familia", archivo.stem)
                    familias.append(nombre)
            except:
                continue
        
        return sorted(familias)
    
    @classmethod
    def tabla_a_familia(cls, tabla_data: List[Dict], nombre_familia: str) -> Dict:
        """Convertir datos de tabla a formato familia"""
        
        # Obtener columnas de estructuras
        if not tabla_data:
            raise ValueError("Datos de tabla vacíos")
        
        primera_fila = tabla_data[0]
        columnas_estructura = [key for key in primera_fila.keys() 
                             if key.startswith("Estr.")]
        
        if not columnas_estructura:
            raise ValueError("No se encontraron columnas de estructura")
        
        # Construir estructuras
        estructuras = {}
        
        for nombre_estr in columnas_estructura:
            estructura = {}
            
            for fila in tabla_data:
                parametro = fila["parametro"]
                valor = fila.get(nombre_estr, "")
                
                # Convertir tipos
                if parametro in ["cantidad", "TENSION", "CANT_HG", "FORZAR_N_POSTES"]:
                    try:
                        valor = int(valor) if valor != "" else 0
                    except:
                        valor = 0
                elif parametro in ["L_vano", "alpha", "theta", "Vmax", "Vmed", "Vtormenta", 
                                 "ALTURA_MINIMA_CABLE", "HADD", "ZOOM_CABEZAL"]:
                    try:
                        valor = float(valor) if valor != "" else 0.0
                    except:
                        valor = 0.0
                elif parametro in ["VANO_DESNIVELADO", "AJUSTAR_POR_ALTURA_MSNM", 
                                 "HG_CENTRADO", "REEMPLAZAR_TITULO_GRAFICO", "ADC_3D"]:
                    valor = bool(valor) if valor != "" else False
                
                estructura[parametro] = valor
            
            estructuras[nombre_estr] = estructura
        
        # Construir familia
        familia_data = {
            "nombre_familia": nombre_familia,
            "fecha_creacion": datetime.now().isoformat(),
            "fecha_modificacion": datetime.now().isoformat(),
            "estructuras": estructuras
        }
        
        return familia_data
    
    @classmethod
    def calcular_hash_familia(cls, familia_data: Dict) -> str:
        """Calcular hash MD5 de familia para cache"""
        # Excluir campos de fecha para hash
        familia_hash = familia_data.copy()
        familia_hash.pop("fecha_creacion", None)
        familia_hash.pop("fecha_modificacion", None)
        
        # Serializar y calcular hash
        familia_str = json.dumps(familia_hash, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(familia_str.encode('utf-8')).hexdigest()
    
    @classmethod
    def cargar_estructura_individual(cls, nombre_estructura: str) -> Dict:
        """Cargar estructura individual desde DB"""
        archivo_estructura = cls.DATA_DIR / f"{nombre_estructura}.estructura.json"
        
        if not archivo_estructura.exists():
            raise FileNotFoundError(f"Estructura '{nombre_estructura}' no encontrada")
        
        with open(archivo_estructura, "r", encoding="utf-8") as f:
            return json.load(f)
    
    @classmethod
    def listar_estructuras_disponibles(cls) -> List[str]:
        """Listar estructuras individuales disponibles"""
        estructuras = []
        
        for archivo in cls.DATA_DIR.glob("*.estructura.json"):
            if archivo.name != "plantilla.estructura.json":
                try:
                    with open(archivo, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        titulo = data.get("TITULO", archivo.stem)
                        estructuras.append(titulo)
                except:
                    continue
        
        return sorted(estructuras)