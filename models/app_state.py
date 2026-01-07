"""Modelo de estado de la aplicación"""

from pathlib import Path
from utils.estructura_manager import EstructuraManager
from utils.cable_manager import CableManager
from utils.calculo_objetos import CalculoObjetosAEA
from utils.calculo_mecanico_cables import CalculoMecanicoCables
from config.app_config import DATA_DIR, CABLES_PATH, FAMILIA_STATE_FILE
import json


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
        self.cargado_desde_cache = False
        self._estructura_actual_titulo = self._cargar_estructura_activa_persistente()
        self._familia_activa_nombre = self._cargar_familia_activa_persistente()
        
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
            self._guardar_estructura_activa_persistente(titulo)
            
            ruta_actual = self.get_estructura_actual_path()
            self.estructura_manager.guardar_estructura(estructura_data, ruta_actual)
            
            print(f"✅ Estructura activa: {titulo}")
    
    def set_familia_activa(self, nombre_familia):
        """Establecer la familia activa y persistir"""
        self._familia_activa_nombre = nombre_familia
        self._guardar_familia_activa_persistente(nombre_familia)
        print(f"✅ Familia activa: {nombre_familia}")
    
    def get_familia_activa(self):
        """Obtener el nombre de la familia activa"""
        return self._familia_activa_nombre
    
    def cargar_familia_activa(self):
        """Cargar datos de la familia activa"""
        if not self._familia_activa_nombre:
            return None
        
        try:
            from pathlib import Path
            import json
            archivo_familia = DATA_DIR / f"{self._familia_activa_nombre}.familia.json"
            if archivo_familia.exists():
                with open(archivo_familia, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error cargando familia activa: {str(e)}")
        return None
    
    def _cargar_familia_activa_persistente(self):
        """Cargar familia activa desde archivo de persistencia"""
        try:
            if FAMILIA_STATE_FILE.exists():
                with open(FAMILIA_STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    nombre_familia = state.get('familia_activa')
                    if nombre_familia:
                        print(f"📂 Familia activa cargada desde persistencia: {nombre_familia}")
                        return nombre_familia
        except Exception as e:
            print(f"⚠️ Error cargando familia activa persistente: {e}")
        return None
    
    def _cargar_estructura_activa_persistente(self):
        """Cargar estructura activa desde archivo de persistencia"""
        try:
            if FAMILIA_STATE_FILE.exists():
                with open(FAMILIA_STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    titulo_estructura = state.get('estructura_activa')
                    if titulo_estructura:
                        print(f"📂 Estructura activa cargada desde persistencia: {titulo_estructura}")
                        return titulo_estructura
        except Exception as e:
            print(f"⚠️ Error cargando estructura activa persistente: {e}")
        return None
    
    def _guardar_estructura_activa_persistente(self, titulo_estructura):
        """Guardar estructura activa en archivo de persistencia"""
        try:
            state_data = {}
            if FAMILIA_STATE_FILE.exists():
                with open(FAMILIA_STATE_FILE, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
            
            state_data['estructura_activa'] = titulo_estructura
            
            with open(FAMILIA_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Estructura activa guardada en persistencia: {titulo_estructura}")
        except Exception as e:
            print(f"⚠️ Error guardando estructura activa persistente: {e}")
    
    def _guardar_familia_activa_persistente(self, nombre_familia):
        """Guardar familia activa en archivo de persistencia"""
        try:
            state = {'familia_activa': nombre_familia}
            with open(FAMILIA_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            print(f"💾 Familia activa guardada en persistencia: {nombre_familia}")
        except Exception as e:
            print(f"⚠️ Error guardando familia activa persistente: {e}")
    
    def set_vano_economico_ajustes(self, ajustes):
        """Guardar ajustes de vano económico"""
        try:
            state_data = {}
            if FAMILIA_STATE_FILE.exists():
                with open(FAMILIA_STATE_FILE, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
            
            state_data['vano_economico_ajustes'] = ajustes
            
            with open(FAMILIA_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error guardando ajustes vano económico: {e}")
    
    def get_vano_economico_ajustes(self):
        """Obtener ajustes de vano económico"""
        try:
            if FAMILIA_STATE_FILE.exists():
                with open(FAMILIA_STATE_FILE, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    return state_data.get('vano_economico_ajustes')
        except Exception as e:
            print(f"⚠️ Error cargando ajustes vano económico: {e}")
        return None
    
    def set_calculos_activos(self, calculos_activos):
        """Guardar checkboxes de cálculos activos"""
        try:
            state_data = {}
            if FAMILIA_STATE_FILE.exists():
                with open(FAMILIA_STATE_FILE, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
            
            state_data['calculos_activos'] = calculos_activos
            
            with open(FAMILIA_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error guardando cálculos activos: {e}")
    
    def get_calculos_activos(self):
        """Obtener checkboxes de cálculos activos"""
        try:
            if FAMILIA_STATE_FILE.exists():
                with open(FAMILIA_STATE_FILE, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    return state_data.get('calculos_activos', ["cmc", "dge", "dme", "arboles", "sph", "fundacion", "costeo"])
        except Exception as e:
            print(f"⚠️ Error cargando cálculos activos: {e}")
        return ["cmc", "dge", "dme", "arboles", "sph", "fundacion", "costeo"]
