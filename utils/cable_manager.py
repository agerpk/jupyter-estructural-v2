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