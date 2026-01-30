"""
Módulo para realizar cálculo mecánico de cables
"""

import pandas as pd
from ListarCargas import ListadorCargas


class CalculoMecanicoCables:
    """Clase para gestionar el cálculo mecánico de cables"""
    
    def __init__(self, calculo_objetos):
        self.calculo_objetos = calculo_objetos
        self.df_conductor = None
        self.df_guardia1 = None
        self.df_guardia2 = None
        self.resultados_conductor = None
        self.resultados_guardia1 = None
        self.resultados_guardia2 = None
        self.df_cargas_totales = None
    
    def calcular(self, params, estados_climaticos, restricciones=None):
        """Realizar cálculo mecánico completo"""
        
        if not self.calculo_objetos.cable_conductor or not self.calculo_objetos.cable_guardia:
            return {"exito": False, "mensaje": "Debe crear los objetos Cable primero"}
        
        try:
            # Extraer parámetros
            L_vano = params["L_vano"]
            exposicion = params["exposicion"]
            clase = params["clase"]
            Zco = params["Zco"]
            Zcg = params["Zcg"]
            Cf_cable = params["Cf_cable"]
            Cf_guardia = params["Cf_guardia"]
            SALTO_PORCENTUAL = params["SALTO_PORCENTUAL"]
            PASO_AFINADO = params["PASO_AFINADO"]
            OBJ_CONDUCTOR = params["OBJ_CONDUCTOR"]
            OBJ_GUARDIA = params["OBJ_GUARDIA"]
            RELFLECHA_MAX_GUARDIA = params["RELFLECHA_MAX_GUARDIA"]
            RELFLECHA_SIN_VIENTO = params["RELFLECHA_SIN_VIENTO"]
            
            # Parámetros de desnivel
            VANO_DESNIVELADO = params.get("VANO_DESNIVELADO", False)
            H_PIQANTERIOR = params.get("H_PIQANTERIOR", 0.0)
            H_PIQPOSTERIOR = params.get("H_PIQPOSTERIOR", 0.0)
            
            # Actualizar parámetros de desnivel en los cables
            self.calculo_objetos.cable_conductor.VANO_DESNIVELADO = VANO_DESNIVELADO
            self.calculo_objetos.cable_conductor.H_PIQANTERIOR = H_PIQANTERIOR
            self.calculo_objetos.cable_conductor.H_PIQPOSTERIOR = H_PIQPOSTERIOR
            
            self.calculo_objetos.cable_guardia.VANO_DESNIVELADO = VANO_DESNIVELADO
            self.calculo_objetos.cable_guardia.H_PIQANTERIOR = H_PIQANTERIOR
            self.calculo_objetos.cable_guardia.H_PIQPOSTERIOR = H_PIQPOSTERIOR
            
            if self.calculo_objetos.cable_guardia2:
                self.calculo_objetos.cable_guardia2.VANO_DESNIVELADO = VANO_DESNIVELADO
                self.calculo_objetos.cable_guardia2.H_PIQANTERIOR = H_PIQANTERIOR
                self.calculo_objetos.cable_guardia2.H_PIQPOSTERIOR = H_PIQPOSTERIOR
            
            # Restricciones (usar las proporcionadas o valores por defecto)
            if restricciones is None:
                restricciones = {
                    "conductor": {"tension_max_porcentaje": {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25}},
                    "guardia": {"tension_max_porcentaje": {"I": 0.7, "II": 0.70, "III": 0.70, "IV": 0.7, "V": 0.7}, 
                               "relflecha_max": RELFLECHA_MAX_GUARDIA}
                }
            
            # Parámetros de viento
            parametros_viento = {"exposicion": exposicion, "clase": clase, "Zc": Zco, "Cf": Cf_cable, "L_vano": L_vano}
            parametros_viento_guardia = {**parametros_viento, "Zc": Zcg, "Cf": Cf_guardia}
            
            # Calcular conductor
            self.df_conductor, self.resultados_conductor, estado_limitante_cond, self.memoria_conductor = \
                self.calculo_objetos.cable_conductor.calculo_mecanico(
                    vano=L_vano,
                    estados_climaticos=estados_climaticos,
                    parametros_viento=parametros_viento,
                    restricciones=restricciones["conductor"],
                    objetivo=OBJ_CONDUCTOR,
                    es_guardia=False,
                    flecha_max_permitida=3.0,
                    salto_porcentual=SALTO_PORCENTUAL,
                    paso_afinado=PASO_AFINADO,
                    relflecha_sin_viento=RELFLECHA_SIN_VIENTO
                )
            
            # Redondear valores
            for col in self.df_conductor.columns:
                if self.df_conductor[col].dtype == 'float64':
                    if 'Hielo' in col:
                        self.df_conductor[col] = self.df_conductor[col].round(3)
                    else:
                        self.df_conductor[col] = self.df_conductor[col].round(2)

            # DEBUG: inspeccionar resultados del conductor
            try:
                print("💡 DEBUG resultados_conductor keys:", list(self.resultados_conductor.keys())[:5])
                sample_vals = {k: v.get('flecha_vertical_m') for k, v in list(self.resultados_conductor.items())[:5]}
                print("💡 DEBUG sample flecha_vertical_m:", sample_vals)
            except Exception:
                print("⚠️ DEBUG: no se pudo inspeccionar resultados_conductor")
            
            # Calcular guardia 1
            try:
                flecha_max_conductor = max([r["flecha_vertical_m"] for r in self.resultados_conductor.values() if r and r.get('flecha_vertical_m') is not None])
            except ValueError:
                return {"exito": False, "mensaje": "No se obtuvieron valores de flecha válidos del conductor"}
            except Exception as e:
                return {"exito": False, "mensaje": f"Error calculando flecha_max_conductor: {e}"}

            flecha_max_guardia = flecha_max_conductor * RELFLECHA_MAX_GUARDIA
            
            self.df_guardia1, self.resultados_guardia1, estado_limitante_guard1, self.memoria_guardia1 = \
                self.calculo_objetos.cable_guardia.calculo_mecanico(
                    vano=L_vano,
                    estados_climaticos=estados_climaticos,
                    parametros_viento=parametros_viento_guardia,
                    restricciones=restricciones["guardia"],
                    objetivo=OBJ_GUARDIA,
                    es_guardia=True,
                    flecha_max_permitida=flecha_max_guardia,
                    resultados_conductor=self.resultados_conductor,
                    salto_porcentual=SALTO_PORCENTUAL,
                    paso_afinado=PASO_AFINADO,
                    relflecha_sin_viento=RELFLECHA_SIN_VIENTO
                )
            
            # Redondear valores
            for col in self.df_guardia1.columns:
                if self.df_guardia1[col].dtype == 'float64':
                    if 'Hielo' in col:
                        self.df_guardia1[col] = self.df_guardia1[col].round(3)
                    else:
                        self.df_guardia1[col] = self.df_guardia1[col].round(2)
            
            # Calcular guardia 2 si existe
            if self.calculo_objetos.cable_guardia2:
                self.df_guardia2, self.resultados_guardia2, estado_limitante_guard2, self.memoria_guardia2 = \
                    self.calculo_objetos.cable_guardia2.calculo_mecanico(
                        vano=L_vano,
                        estados_climaticos=estados_climaticos,
                        parametros_viento=parametros_viento_guardia,
                        restricciones=restricciones["guardia"],
                        objetivo=OBJ_GUARDIA,
                        es_guardia=True,
                        flecha_max_permitida=flecha_max_guardia,
                        resultados_conductor=self.resultados_conductor,
                        salto_porcentual=SALTO_PORCENTUAL,
                        paso_afinado=PASO_AFINADO,
                        relflecha_sin_viento=RELFLECHA_SIN_VIENTO
                    )
                
                # Redondear valores
                for col in self.df_guardia2.columns:
                    if self.df_guardia2[col].dtype == 'float64':
                        if 'Hielo' in col:
                            self.df_guardia2[col] = self.df_guardia2[col].round(3)
                        else:
                            self.df_guardia2[col] = self.df_guardia2[col].round(2)
            else:
                self.df_guardia2 = None
                self.resultados_guardia2 = None
                self.memoria_guardia2 = None
            
            # Generar lista de cargas
            if self.calculo_objetos.cadena and self.calculo_objetos.estructura:
                listador_cargas = ListadorCargas(
                    cable_conductor=self.calculo_objetos.cable_conductor,
                    cable_guardia1=self.calculo_objetos.cable_guardia,
                    cable_guardia2=self.calculo_objetos.cable_guardia2,
                    cadena=self.calculo_objetos.cadena,
                    estructura=self.calculo_objetos.estructura,
                    estados_climaticos=estados_climaticos,
                    L_vano=L_vano,
                    alpha=params["alpha"],
                    theta=params["theta"],
                    t_hielo=params["t_hielo"],
                    exposicion=exposicion,
                    clase=clase,
                    Zco=Zco,
                    Zcg=Zcg,
                    Zca=params["Zca"],
                    Zes=params["Zes"],
                    Cf_cable=Cf_cable,
                    Cf_guardia=Cf_guardia,
                    Cf_cadena=params["Cf_cadena"],
                    Cf_estructura=params["Cf_estructura"],
                    PCADENA=params["PCADENA"],
                    CS=220.0
                )
                
                # Primero generar cargas de viento
                listador_cargas.generar_cargas_viento()
                
                # Luego generar lista total de cargas
                self.df_cargas_totales = listador_cargas.generar_lista_cargas(
                    self.resultados_conductor, 
                    self.resultados_guardia1,
                    self.resultados_guardia2
                )
            
            return {
                "exito": True,
                "mensaje": "Cálculo mecánico completado exitosamente",
                "df_conductor": self.df_conductor,
                "df_guardia1": self.df_guardia1,
                "df_guardia2": self.df_guardia2,
                "df_cargas_totales": self.df_cargas_totales
            }
            
        except Exception as e:
            return {"exito": False, "mensaje": f"Error en cálculo: {str(e)}"}
