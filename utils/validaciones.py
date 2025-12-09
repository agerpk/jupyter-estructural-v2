"""
Funciones de validación para estructuras
"""

import json
from typing import Dict, Any

def validar_estructura_json(data: Dict[str, Any]) -> bool:
    """Validar que el JSON tenga la estructura esperada"""
    
    campos_requeridos = [
        "TIPO_ESTRUCTURA", "TITULO", "cable_conductor_id", 
        "cable_guardia_id", "Vmax", "L_vano", "TENSION"
    ]
    
    # Verificar campos requeridos
    for campo in campos_requeridos:
        if campo not in data:
            return False
    
    # Verificar tipos básicos
    if not isinstance(data.get("TITULO"), str):
        return False
    if not isinstance(data.get("L_vano"), (int, float)):
        return False
    if not isinstance(data.get("TENSION"), int):
        return False
    
    return True

def validar_nombre_archivo(nombre: str) -> bool:
    """Validar que el nombre de archivo tenga el formato correcto"""
    return nombre.endswith('.estructura.json') and len(nombre) > len('.estructura.json')