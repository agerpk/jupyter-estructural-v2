"""
Gestor de datos de cables
"""

import json
from pathlib import Path
from typing import Dict, Any, List

class CableManager:
    def __init__(self, cables_path: Path):
        self.cables_path = cables_path
        self.cables_data = self.cargar_cables()
    
    def cargar_cables(self) -> Dict[str, Any]:
        """Cargar datos de cables desde archivo JSON"""
        try:
            with open(self.cables_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    def obtener_cables(self) -> List[str]:
        """Obtener lista de IDs de cables disponibles"""
        return list(self.cables_data.keys())
    
    def obtener_cable(self, cable_id: str) -> Dict[str, Any]:
        """Obtener datos de un cable específico"""
        return self.cables_data.get(cable_id, {})
    
    def obtener_opciones_select(self) -> List[Dict[str, str]]:
        """Obtener opciones para dropdown de cables"""
        return [{"label": cable_id, "value": cable_id} for cable_id in self.obtener_cables()]
    
    def guardar_cables(self):
        """Guardar datos de cables en archivo JSON"""
        with open(self.cables_path, 'w', encoding='utf-8') as f:
            json.dump(self.cables_data, f, indent=2, ensure_ascii=False)
    
    def agregar_cable(self, cable_id: str, datos_cable: Dict[str, Any]):
        """Agregar un nuevo cable"""
        self.cables_data[cable_id] = datos_cable
        self.guardar_cables()
    
    def modificar_cable(self, cable_id: str, datos_cable: Dict[str, Any]):
        """Modificar un cable existente"""
        if cable_id in self.cables_data:
            self.cables_data[cable_id] = datos_cable
            self.guardar_cables()
        else:
            raise ValueError(f"Cable '{cable_id}' no existe")
    
    def eliminar_cable(self, cable_id: str):
        """Eliminar un cable"""
        if cable_id in self.cables_data:
            del self.cables_data[cable_id]
            self.guardar_cables()
        else:
            raise ValueError(f"Cable '{cable_id}' no existe")