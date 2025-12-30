"""Modelo de estado de la aplicación"""

from pathlib import Path
from utils.estructura_manager import EstructuraManager
from utils.cable_manager import CableManager
from utils.calculo_objetos import CalculoObjetosAEA
from utils.calculo_mecanico_cables import CalculoMecanicoCables
from config.app_config import DATA_DIR, CABLES_PATH


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
        self.cargado_desde_cache = False  # Flag para controlar mensajes de cache
        self._estructura_actual_titulo = None  # Título de la estructura actual
        
        self._initialized = True
    
    def cargar_estructura_actual(self):
        """Cargar la estructura actual o la plantilla por defecto"""
        try:
            # Intentar cargar estructura actual desde el sistema unificado
            if self._estructura_actual_titulo:
                ruta_actual = self.get_estructura_actual_path()
                estructura = self.estructura_manager.cargar_estructura(ruta_actual)
                return estructura
        except Exception as e:
            print(f"Error cargando estructura actual: {e}")
        
        # Cargar plantilla por defecto
        estructura = self.estructura_manager.cargar_plantilla()
        self._estructura_actual_titulo = estructura.get('TITULO', 'estructura')
        # Guardar en archivo unificado
        ruta_actual = self.get_estructura_actual_path()
        self.estructura_manager.guardar_estructura(estructura, ruta_actual)
        return estructura
    
    def get_estructura_actual_path(self):
        """Obtener la ruta del archivo de la estructura actual"""
        if self._estructura_actual_titulo:
            return DATA_DIR / f"{self._estructura_actual_titulo}.estructura.json"
        
        # Fallback: buscar primera estructura disponible
        estructuras = self.estructura_manager.listar_estructuras()
        if estructuras:
            return DATA_DIR / estructuras[0]
        
        # Si no hay estructuras, usar plantilla
        return DATA_DIR / "plantilla.estructura.json"
    
    def set_estructura_actual(self, estructura_data):
        """Establecer la estructura actual y actualizar el título"""
        if estructura_data:
            titulo = estructura_data.get('TITULO', 'estructura')
            self._estructura_actual_titulo = titulo
            
            # Guardar en archivo unificado
            ruta_actual = self.get_estructura_actual_path()
            self.estructura_manager.guardar_estructura(estructura_data, ruta_actual)
            
            print(f"✅ Estructura activa: {titulo}")
    
    def get_estructura_actual_titulo(self):
        """Obtener el título de la estructura actual"""
        return self._estructura_actual_titulo or 'estructura'
