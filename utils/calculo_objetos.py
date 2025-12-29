"""
Módulo para creación de objetos Cable, Cadena y Estructura según AEA-95301
"""

from CalculoCables import Cable_AEA, Elemento_AEA, LibCables
from DatosCables import datos_cables
import json
from config.app_config import DATA_DIR


class CalculoObjetosAEA:
    """Clase para gestionar la creación de objetos según configuración de estructura"""
    
    def __init__(self):
        self.lib_cables = None
        self.cable_conductor = None
        self.cable_guardia = None
        self.cable_guardia1 = None
        self.cable_guardia2 = None
        self.cadena = None
        self.estructura = None
        self.estructura_geometria = None
        self.estructura_mecanica = None
        self.estructura_graficos = None
        self.DATOS_CABLES = self._cargar_datos_cables()
    
    def _cargar_datos_cables(self):
        """Cargar datos de cables desde cables_2.json (incluye cables convertidos) o fallback a DatosCables.py"""
        try:
            cables_path = DATA_DIR / "cables_2.json"
            if cables_path.exists():
                with open(cables_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return datos_cables
        except Exception as e:
            print(f"Error cargando cables_2.json, usando DatosCables.py: {e}")
            return datos_cables
    
    def crear_objetos_cable(self, estructura_config):
        """Crear objetos Cable según configuración de estructura"""
        try:
            cable_conductor_id = estructura_config.get("cable_conductor_id")
            cable_guardia_id = estructura_config.get("cable_guardia_id")
            cable_guardia2_id = estructura_config.get("cable_guardia2_id")
            cant_hg = estructura_config.get("CANT_HG", 1)
            
            if cable_conductor_id not in self.DATOS_CABLES:
                raise ValueError(f"Cable conductor '{cable_conductor_id}' no encontrado")
            if cable_guardia_id not in self.DATOS_CABLES:
                raise ValueError(f"Cable guardia '{cable_guardia_id}' no encontrado")
            if cant_hg == 2 and cable_guardia2_id and cable_guardia2_id not in self.DATOS_CABLES:
                raise ValueError(f"Cable guardia 2 '{cable_guardia2_id}' no encontrado")
            
            viento_base_params_conductor = {
                'V': estructura_config.get("Vmax"),
                't_hielo': estructura_config.get("t_hielo"),
                'exp': estructura_config.get("exposicion"),
                'clase': estructura_config.get("clase"),
                'Zc': estructura_config.get("Zco"),
                'Cf': estructura_config.get("Cf_cable"),
                'L_vano': estructura_config.get("L_vano")
            }
            
            viento_base_params_guardia = {
                'V': estructura_config.get("Vmax"),
                't_hielo': estructura_config.get("t_hielo"),
                'exp': estructura_config.get("exposicion"),
                'clase': estructura_config.get("clase"),
                'Zc': estructura_config.get("Zcg"),
                'Cf': estructura_config.get("Cf_guardia"),
                'L_vano': estructura_config.get("L_vano")
            }
            
            self.lib_cables = LibCables()
            
            self.cable_conductor = Cable_AEA(
                id_cable=cable_conductor_id,
                nombre=cable_conductor_id,
                propiedades=self.DATOS_CABLES[cable_conductor_id],
                viento_base_params=viento_base_params_conductor
            )
            self.lib_cables.agregar_cable(self.cable_conductor)
            
            # Cable guardia 1 (derecha, HG1)
            self.cable_guardia1 = Cable_AEA(
                id_cable=cable_guardia_id,
                nombre=cable_guardia_id,
                propiedades=self.DATOS_CABLES[cable_guardia_id],
                viento_base_params=viento_base_params_guardia
            )
            self.lib_cables.agregar_cable(self.cable_guardia1)
            self.cable_guardia = self.cable_guardia1  # Compatibilidad
            
            # Si hay 2 cables de guardia y se especifica el segundo
            if cant_hg == 2 and cable_guardia2_id:
                self.cable_guardia2 = Cable_AEA(
                    id_cable=cable_guardia2_id,
                    nombre=cable_guardia2_id,
                    propiedades=self.DATOS_CABLES[cable_guardia2_id],
                    viento_base_params=viento_base_params_guardia
                )
                self.lib_cables.agregar_cable(self.cable_guardia2)
                
                return {
                    "exito": True,
                    "mensaje": "Cables creados exitosamente",
                    "conductor": self.cable_conductor.nombre,
                    "guardia1": self.cable_guardia1.nombre,
                    "guardia2": self.cable_guardia2.nombre
                }
            else:
                # Si solo hay 1 cable de guardia, usar el mismo para ambos
                self.cable_guardia2 = self.cable_guardia1
                return {
                    "exito": True,
                    "mensaje": "Cables creados exitosamente",
                    "conductor": self.cable_conductor.nombre,
                    "guardia1": self.cable_guardia1.nombre
                }
            
        except Exception as e:
            return {"exito": False, "mensaje": f"Error: {str(e)}"}
    
    def crear_objetos_cadena(self, estructura_config):
        """Crear objeto Cadena según configuración de estructura"""
        try:
            self.cadena = Elemento_AEA(
                id_elemento="cadena_aisladores",
                nombre="Cadena de Aisladores",
                area_transversal_m2=estructura_config.get("A_cadena"),
                area_longitudinal_m2=estructura_config.get("A_cadena"),
                Cf=estructura_config.get("Cf_cadena"),
                Z=estructura_config.get("Zca"),
                peso_daN=estructura_config.get("PCADENA")
            )
            
            return {
                "exito": True,
                "mensaje": "Objeto Cadena creado exitosamente",
                "cadena": str(self.cadena)
            }
            
        except Exception as e:
            return {"exito": False, "mensaje": f"Error: {str(e)}"}
    
    def crear_objetos_estructura(self, estructura_config):
        """Crear objeto Estructura según configuración de estructura"""
        try:
            self.estructura = Elemento_AEA(
                id_elemento="estructura",
                nombre="Estructura",
                area_transversal_m2=estructura_config.get("A_estr_trans"),
                area_longitudinal_m2=estructura_config.get("A_estr_long"),
                Cf=estructura_config.get("Cf_estructura"),
                Z=estructura_config.get("Zes"),
                peso_daN=estructura_config.get("PESTRUCTURA")
            )
            
            return {
                "exito": True,
                "mensaje": "Objeto Estructura creado exitosamente",
                "estructura": str(self.estructura)
            }
            
        except Exception as e:
            return {"exito": False, "mensaje": f"Error: {str(e)}"}
    
    def crear_cable_conductor(self, estructura_config):
        """Crear solo objeto Cable conductor"""
        try:
            cable_conductor_id = estructura_config.get("cable_conductor_id")
            
            if cable_conductor_id not in self.DATOS_CABLES:
                raise ValueError(f"Cable conductor '{cable_conductor_id}' no encontrado")
            
            viento_base_params_conductor = {
                'V': estructura_config.get("Vmax"),
                't_hielo': estructura_config.get("t_hielo"),
                'exp': estructura_config.get("exposicion"),
                'clase': estructura_config.get("clase"),
                'Zc': estructura_config.get("Zco"),
                'Cf': estructura_config.get("Cf_cable"),
                'L_vano': estructura_config.get("L_vano")
            }
            
            self.lib_cables = LibCables()
            
            self.cable_conductor = Cable_AEA(
                id_cable=cable_conductor_id,
                nombre=cable_conductor_id,
                propiedades=self.DATOS_CABLES[cable_conductor_id],
                viento_base_params=viento_base_params_conductor
            )
            self.lib_cables.agregar_cable(self.cable_conductor)
            
            return {
                "exito": True,
                "mensaje": "Cable conductor creado exitosamente",
                "conductor": self.cable_conductor.nombre
            }
            
        except Exception as e:
            return {"exito": False, "mensaje": f"Error: {str(e)}"}
        """Crear todos los objetos (Cable, Cadena, Estructura)"""
        resultados = []
        
        resultado_cables = self.crear_objetos_cable(estructura_config)
        resultados.append(resultado_cables)
        
        resultado_cadena = self.crear_objetos_cadena(estructura_config)
        resultados.append(resultado_cadena)
        
        resultado_estructura = self.crear_objetos_estructura(estructura_config)
        resultados.append(resultado_estructura)
        
        if all(r["exito"] for r in resultados):
            cables_msg = f"{resultado_cables['conductor']}, {resultado_cables['guardia1']}"
            if 'guardia2' in resultado_cables:
                cables_msg += f", {resultado_cables['guardia2']}"
            
            return {
                "exito": True,
                "mensaje": f"Todos los objetos creados exitosamente - Cables: {cables_msg} - Cadena de Aisladores - Estructura"
            }
        else:
            errores = [r["mensaje"] for r in resultados if not r["exito"]]
            return {"exito": False, "mensaje": "\n".join(errores)}
