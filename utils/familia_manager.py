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
    def crear_familia_nueva(cls) -> Dict:
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
    def guardar_familia(cls, familia_data: Dict) -> bool:
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
        try:
            with open(archivo_familia, "w", encoding="utf-8") as f:
                json.dump(familia_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando familia {nombre_familia}: {e}")
            return False
    
    @classmethod
    def cargar_familia(cls, nombre_familia: str) -> Dict:
        """Cargar familia por nombre"""
        nombre_archivo = nombre_familia.replace(" ", "_").replace("/", "_")
        archivo_familia = cls.DATA_DIR / f"{nombre_archivo}.familia.json"
        
        if not archivo_familia.exists():
            raise FileNotFoundError(f"Familia '{nombre_familia}' no encontrada")
        
        with open(archivo_familia, "r", encoding="utf-8") as f:
            familia_data = json.load(f)
        
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
    def tabla_a_familia(cls, tabla_data: List[Dict], columnas: List[Dict], nombre_familia: str) -> Dict:
        """Convierte datos de tabla a formato .familia.json"""
        from datetime import datetime
        
        # Extraer columnas de estructura (Estr.1, Estr.2, etc.)
        columnas_estructura = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
        
        estructuras = {}
        for col_id in columnas_estructura:
            estructura_data = {}
            
            # Convertir filas de tabla a estructura
            for fila in tabla_data:
                parametro = fila['parametro']
                valor = fila.get(col_id, fila.get('valor', ''))
                
                # Convertir tipos
                tipo = fila.get('tipo', 'str')
                if tipo == 'int':
                    try:
                        valor = int(valor)
                    except:
                        valor = 0
                elif tipo == 'float':
                    try:
                        valor = float(valor)
                    except:
                        valor = 0.0
                elif tipo == 'bool':
                    valor = bool(valor) if isinstance(valor, bool) else str(valor).lower() == 'true'
                
                estructura_data[parametro] = valor
            
            estructuras[col_id] = estructura_data
        
        return {
            "nombre_familia": nombre_familia,
            "fecha_creacion": datetime.now().isoformat(),
            "fecha_modificacion": datetime.now().isoformat(),
            "estructuras": estructuras
        }
    
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
    def cargar_estructura_individual(cls, titulo_estructura: str) -> Dict:
        """Cargar estructura individual desde DB por título"""
        # Buscar archivo por título
        for archivo in cls.DATA_DIR.glob("*.estructura.json"):
            if archivo.name != "plantilla.estructura.json":
                try:
                    with open(archivo, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("TITULO") == titulo_estructura:
                            return data
                except:
                    continue
        
        raise FileNotFoundError(f"Estructura con título '{titulo_estructura}' no encontrada")
    
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
    
    @classmethod
    def obtener_archivos_familia(cls) -> List[str]:
        """Obtiene lista de archivos .familia.json disponibles"""
        try:
            archivos = list(cls.DATA_DIR.glob("*.familia.json"))
            return [archivo.stem for archivo in archivos]
        except:
            return []
    
    @classmethod
    def familia_a_tabla(cls, datos_familia: Dict) -> tuple[List[Dict], List[Dict]]:
        """Convierte formato .familia.json a datos de tabla"""
        if not datos_familia or 'estructuras' not in datos_familia:
            return [], []
        
        # Cargar plantilla para obtener estructura base
        try:
            with open(cls.DATA_DIR / "plantilla.estructura.json", 'r', encoding='utf-8') as f:
                plantilla = json.load(f)
        except:
            return [], []
        
        # Generar tabla usando ParametrosManager
        from utils.parametros_manager import ParametrosManager
        tabla_base = ParametrosManager.estructura_a_tabla(plantilla)
        
        # Crear columnas base
        columnas = [
            {"name": "Parámetro", "id": "parametro", "editable": False},
            {"name": "Símbolo", "id": "simbolo", "editable": False},
            {"name": "Unidad", "id": "unidad", "editable": False},
            {"name": "Descripción", "id": "descripcion", "editable": False}
        ]
        
        # Agregar columnas de estructura
        estructuras = datos_familia['estructuras']
        for nombre_estructura in sorted(estructuras.keys()):
            columnas.append({
                "name": nombre_estructura,
                "id": nombre_estructura,
                "editable": True
            })
        
        # Llenar datos de tabla
        tabla_data = []
        for fila_base in tabla_base:
            fila = {
                "parametro": fila_base["parametro"],
                "simbolo": fila_base["simbolo"],
                "unidad": fila_base["unidad"],
                "descripcion": fila_base["descripcion"],
                "tipo": fila_base["tipo"],
                "categoria": fila_base["categoria"]
            }
            
            # Agregar valores de cada estructura
            for nombre_estructura, estructura_data in estructuras.items():
                valor = estructura_data.get(fila_base["parametro"], fila_base["valor"])
                fila[nombre_estructura] = valor
            
            tabla_data.append(fila)
        
        # Asegurar que TITULO esté primero y seguir orden de cálculo encadenado
        # CMC>DGE>DME>ADC>SPH>FUND>COSTEO
        def sort_key(x):
            if x["parametro"] == "TITULO":
                return ("0_TITULO", "0_TITULO")  # TITULO siempre primero
            
            # Mapeo de categorías al orden de cálculo encadenado
            orden_categorias = {
                "General": "1_General",
                "Cables": "2_CMC",
                "Cabezal": "3_DGE", 
                "Línea": "4_DGE",
                "Mecánica": "5_DME",
                "Gráficos": "6_ADC",
                "Postes": "7_SPH",
                "Fundación": "8_FUND",
                "Costeo": "9_COSTEO"
            }
            
            categoria_orden = orden_categorias.get(x["categoria"], "Z_" + x["categoria"])
            return (categoria_orden, x["parametro"])
        
        tabla_data.sort(key=sort_key)
        
        return tabla_data, columnas