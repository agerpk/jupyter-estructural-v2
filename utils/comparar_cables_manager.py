"""
Manager para gestión de archivos de comparativa de cables
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from config.app_config import DATA_DIR

class ComparativaCablesManager:
    """Manager para archivos de comparativa de cables"""
    
    @staticmethod
    def crear_comparativa_nueva(titulo):
        """Crear nueva comparativa con valores por defecto"""
        return {
            "titulo": titulo,
            "fecha_creacion": datetime.now().isoformat(),
            "fecha_modificacion": datetime.now().isoformat(),
            "version": "1.0",
            "parametros_linea": {
                "L_vano": 150,
                "theta": 0,
                "Vmax": 38.9,
                "Vmed": 15.56,
                "t_hielo": 0
            },
            "configuracion_calculo": {
                "VANO_DESNIVELADO": True,
                "H_PIQANTERIOR": 0,
                "H_PIQPOSTERIOR": 0,
                "SALTO_PORCENTUAL": 0.05,
                "PASO_AFINADO": 0.01,
                "OBJ_CONDUCTOR": "FlechaMin",
                "RELFLECHA_SIN_VIENTO": True
            },
            "estados_climaticos": {
                "I": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "hielo_espesor": 0, "restriccion_conductor": 0.25, "restriccion_guardia": 0.7},
                "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "hielo_espesor": 0, "restriccion_conductor": 0.4, "restriccion_guardia": 0.7},
                "III": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": 38.9, "hielo_espesor": 0, "restriccion_conductor": 0.4, "restriccion_guardia": 0.7},
                "IV": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": 15.56, "hielo_espesor": 0.01, "restriccion_conductor": 0.4, "restriccion_guardia": 0.7},
                "V": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "hielo_espesor": 0, "restriccion_conductor": 0.25, "restriccion_guardia": 0.7}
            },
            "cables_seleccionados": []
        }
    
    @staticmethod
    def guardar_comparativa(comparativa_data):
        """Guardar comparativa en archivo JSON"""
        titulo = comparativa_data["titulo"]
        titulo_archivo = titulo.replace(' ', '_')
        ruta_archivo = DATA_DIR / f"{titulo_archivo}.compararCMC.json"
        
        # Actualizar fecha de modificación
        comparativa_data["fecha_modificacion"] = datetime.now().isoformat()
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(comparativa_data, f, indent=2, ensure_ascii=False)
        
        return str(ruta_archivo)
    
    @staticmethod
    def cargar_comparativa(titulo):
        """Cargar comparativa desde archivo JSON"""
        titulo_archivo = titulo.replace(' ', '_')
        ruta_archivo = DATA_DIR / f"{titulo_archivo}.compararCMC.json"
        
        if not ruta_archivo.exists():
            return None
        
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando comparativa {titulo}: {e}")
            return None
    
    @staticmethod
    def listar_comparativas():
        """Listar todas las comparativas disponibles"""
        comparativas = []
        for archivo in DATA_DIR.glob("*.compararCMC.json"):
            titulo = archivo.stem.replace('.compararCMC', '').replace('_', ' ')
            comparativas.append(titulo)
        return sorted(comparativas)
    
    @staticmethod
    def calcular_hash_parametros(comparativa_data):
        """Calcular hash MD5 de parámetros (excluyendo fechas y version)"""
        # Crear copia sin campos de metadata
        params_para_hash = {
            "parametros_linea": comparativa_data.get("parametros_linea", {}),
            "configuracion_calculo": comparativa_data.get("configuracion_calculo", {}),
            "estados_climaticos": comparativa_data.get("estados_climaticos", {}),
            "cables_seleccionados": comparativa_data.get("cables_seleccionados", [])
        }
        
        # Convertir a string JSON ordenado
        json_str = json.dumps(params_para_hash, sort_keys=True, ensure_ascii=False)
        
        # Calcular hash MD5
        return hashlib.md5(json_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def validar_titulo(titulo):
        """Validar que el título sea válido para nombre de archivo"""
        if not titulo or not titulo.strip():
            return False, "El título no puede estar vacío"
        
        # Caracteres no permitidos en nombres de archivo
        caracteres_invalidos = '<>:"/\\|?*'
        for char in caracteres_invalidos:
            if char in titulo:
                return False, f"El título no puede contener el carácter: {char}"
        
        if len(titulo) > 100:
            return False, "El título no puede exceder 100 caracteres"
        
        return True, ""
    
    @staticmethod
    def eliminar_comparativa(titulo):
        """Eliminar archivo de comparativa"""
        titulo_archivo = titulo.replace(' ', '_')
        ruta_archivo = DATA_DIR / f"{titulo_archivo}.compararCMC.json"
        
        if ruta_archivo.exists():
            ruta_archivo.unlink()
            return True
        return False