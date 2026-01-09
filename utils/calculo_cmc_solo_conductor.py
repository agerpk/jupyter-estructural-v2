"""
Módulo para realizar cálculo mecánico solo de cables conductor (sin guardia)
"""

import pandas as pd
import io
import sys


class CalculoCMCSoloConductor:
    """Clase para gestionar el cálculo mecánico solo de conductor"""
    
    def __init__(self, calculo_objetos):
        self.calculo_objetos = calculo_objetos
        self.df_conductor = None
        self.resultados_conductor = None
        self.console_output = ""
    
    def calcular_solo_conductor(self, params, estados_climaticos, restricciones=None):
        """Realizar cálculo mecánico solo del conductor con captura de consola"""
        
        if not self.calculo_objetos.cable_conductor:
            return {"exito": False, "mensaje": "Debe crear el objeto Cable conductor primero"}
        
        # Capturar output de consola
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        try:
            # Extraer parámetros
            L_vano = params["L_vano"]
            exposicion = params["exposicion"]
            clase = params["clase"]
            Zco = params["Zco"]
            Cf_cable = params["Cf_cable"]
            SALTO_PORCENTUAL = params["SALTO_PORCENTUAL"]
            PASO_AFINADO = params["PASO_AFINADO"]
            OBJ_CONDUCTOR = params["OBJ_CONDUCTOR"]
            RELFLECHA_SIN_VIENTO = params["RELFLECHA_SIN_VIENTO"]
            
            # Parámetros de desnivel
            VANO_DESNIVELADO = params.get("VANO_DESNIVELADO", False)
            H_PIQANTERIOR = params.get("H_PIQANTERIOR", 0.0)
            H_PIQPOSTERIOR = params.get("H_PIQPOSTERIOR", 0.0)
            
            # Actualizar parámetros de desnivel en el cable conductor
            self.calculo_objetos.cable_conductor.VANO_DESNIVELADO = VANO_DESNIVELADO
            self.calculo_objetos.cable_conductor.H_PIQANTERIOR = H_PIQANTERIOR
            self.calculo_objetos.cable_conductor.H_PIQPOSTERIOR = H_PIQPOSTERIOR
            
            # Restricciones solo para conductor
            if restricciones is None:
                restricciones = {"tension_max_porcentaje": {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25}}
            else:
                restricciones = restricciones.get("conductor", restricciones)
            
            # Parámetros de viento solo para conductor
            parametros_viento = {"exposicion": exposicion, "clase": clase, "Zc": Zco, "Cf": Cf_cable, "L_vano": L_vano}
            
            # Calcular solo conductor
            self.df_conductor, self.resultados_conductor, estado_limitante_cond = \
                self.calculo_objetos.cable_conductor.calculo_mecanico(
                    vano=L_vano,
                    estados_climaticos=estados_climaticos,
                    parametros_viento=parametros_viento,
                    restricciones=restricciones,
                    objetivo=OBJ_CONDUCTOR,
                    es_guardia=False,
                    flecha_max_permitida=3.0,
                    salto_porcentual=SALTO_PORCENTUAL,
                    paso_afinado=PASO_AFINADO,
                    relflecha_sin_viento=RELFLECHA_SIN_VIENTO
                )
            
            # Capturar output de consola
            self.console_output = buffer.getvalue()
            sys.stdout = old_stdout
            
            # Redondear valores
            if self.df_conductor is not None:
                for col in self.df_conductor.columns:
                    if self.df_conductor[col].dtype == 'float64':
                        if 'Hielo' in col:
                            self.df_conductor[col] = self.df_conductor[col].round(3)
                        else:
                            self.df_conductor[col] = self.df_conductor[col].round(2)
            
            return {
                "exito": True,
                "mensaje": "Cálculo mecánico conductor completado exitosamente",
                "df_conductor": self.df_conductor,
                "resultados_conductor": self.resultados_conductor,
                "console_output": self.console_output
            }
            
        except Exception as e:
            sys.stdout = old_stdout
            return {"exito": False, "mensaje": f"Error en cálculo: {str(e)}"}