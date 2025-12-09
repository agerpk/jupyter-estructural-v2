"""Modelo de estado de la aplicación"""

from pathlib import Path
from utils.estructura_manager import EstructuraManager
from utils.cable_manager import CableManager
from utils.calculo_objetos import CalculoObjetosAEA
from utils.calculo_mecanico_cables import CalculoMecanicoCables
from config.app_config import DATA_DIR, CABLES_PATH, ARCHIVO_ACTUAL


class AppState:
    """Singleton para gestionar el estado global de la aplicación"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.estructura_manager = EstructuraManager(DATA_DIR)
        self.cable_manager = CableManager(CABLES_PATH)
        self.calculo_objetos = CalculoObjetosAEA()
        self.calculo_mecanico = CalculoMecanicoCables(self.calculo_objetos)
        self.archivo_actual = ARCHIVO_ACTUAL
        
        self._initialized = True
    
    def cargar_estructura_actual(self):
        """Cargar la estructura actual o la plantilla por defecto"""
        try:
            if self.archivo_actual.exists():
                return self.estructura_manager.cargar_estructura(self.archivo_actual)
        except Exception as e:
            print(f"Error cargando estructura actual: {e}")
        
        estructura = self.estructura_manager.cargar_plantilla()
        self.estructura_manager.guardar_estructura(estructura, self.archivo_actual)
        return estructura
