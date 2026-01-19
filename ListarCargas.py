"""
ListarCargas.py
Módulo para generar listado completo de cargas a partir de objetos Cable_AEA y Elemento_AEA
"""

import pandas as pd
import math
import os


class ListadorCargas:
    """Clase para generar listado de cargas de forma ordenada y escalable"""
    
    def __init__(self, cable_conductor, cable_guardia1, cable_guardia2, cadena, estructura, 
                 estados_climaticos, L_vano, alpha, theta, t_hielo,
                 exposicion, clase, Zco, Zcg, Zca, Zes, 
                 Cf_cable, Cf_guardia, Cf_cadena, Cf_estructura,
                 PCADENA, CS=220.0):
        """
        Inicializa el listador de cargas
        
        Args:
            cable_conductor: Objeto Cable_AEA del conductor
            cable_guardia1: Objeto Cable_AEA del cable de guardia 1 (derecha)
            cable_guardia2: Objeto Cable_AEA del cable de guardia 2 (izquierda, opcional)
            cadena: Objeto Elemento_AEA de la cadena
            estructura: Objeto Elemento_AEA de la estructura
            estados_climaticos: Dict con estados climáticos
            L_vano: Longitud del vano (m)
            alpha: Ángulo de quiebre (grados)
            theta: Ángulo de viento oblicuo (grados)
            t_hielo: Espesor de hielo (m)
            exposicion, clase: Parámetros de viento
            Zco, Zcg, Zca, Zes: Alturas efectivas
            Cf_cable, Cf_guardia, Cf_cadena, Cf_estructura: Coeficientes de arrastre
            PCADENA: Peso de cadena (daN)
            CS: Carga de servicio (daN)
        """
        self.cable_conductor = cable_conductor
        self.cable_guardia1 = cable_guardia1
        self.cable_guardia2 = cable_guardia2
        self.cadena = cadena
        self.estructura = estructura
        self.estados_climaticos = estados_climaticos
        self.L_vano = L_vano
        self.alpha = alpha
        self.theta = theta
        self.t_hielo = t_hielo
        self.exposicion = exposicion
        self.clase = clase
        self.Zco = Zco
        self.Zcg = Zcg
        self.Zca = Zca
        self.Zes = Zes
        self.Cf_cable = Cf_cable
        self.Cf_guardia = Cf_guardia
        self.Cf_cadena = Cf_cadena
        self.Cf_estructura = Cf_estructura
        self.PCADENA = PCADENA
        self.CS = CS
        
        # Cache de cargas
        self.cache_viento = {}
        self.cargas_cache = {}
        
        # DataFrames de resultados
        self.df_cargas = None
        self.df_cargas_totales = None
    
    def calcular_angulo_relativo_cable(self, theta_grados, alpha_mitad_grados, lado, direccion_viento):
        """Calcula el ángulo relativo entre el viento y el cable"""
        if direccion_viento == "transversal":
            return 90.0 - alpha_mitad_grados
        elif direccion_viento == "longitudinal":
            return alpha_mitad_grados
        else:  # oblicuo
            if lado == 1:
                return 90.0 - theta_grados + alpha_mitad_grados
            else:
                return 90.0 - theta_grados - alpha_mitad_grados
    
    def calcular_carga_viento_cable(self, cable_obj, V, Z, Cf, d_eff, phi_rel, factor_vano):
        """Calcula carga de viento en cables con cache"""
        clave_cache = f"{cable_obj.id}_{V}_{phi_rel}"
        
        if clave_cache not in self.cache_viento:
            resultado = cable_obj.cargaViento(
                V=V, phi_rel_deg=phi_rel, exp=self.exposicion, clase=self.clase,
                Zc=Z, Cf=Cf, L_vano=factor_vano, d_eff=d_eff
            )
            self.cache_viento[clave_cache] = {
                'unitario': resultado["fuerza_daN_per_m"],
                'total': resultado["fuerza_daN_per_m"] * factor_vano
            }
        
        return self.cache_viento[clave_cache]
    
    def generar_cargas_viento(self):
        """Genera DataFrame con todas las cargas de viento"""
        Vmax = max([e.get("viento_velocidad", 0) for e in self.estados_climaticos.values()])
        Vmed = 0.4 * Vmax
        
        alpha_mitad = self.alpha / 2.0
        rows = []
        
        # Diámetros efectivos
        d_conductor = self.cable_conductor.diametro_m
        d_guardia1 = self.cable_guardia1.diametro_m
        d_conductor_eff = self.cable_conductor.diametro_equivalente(self.t_hielo)
        d_guardia1_eff = self.cable_guardia1.diametro_equivalente(self.t_hielo)
        
        if self.cable_guardia2:
            d_guardia2 = self.cable_guardia2.diametro_m
            d_guardia2_eff = self.cable_guardia2.diametro_equivalente(self.t_hielo)
        
        # Escenarios de viento
        escenarios_viento = [
            ("Vmax - Transversal", Vmax, "transversal", self.L_vano, False),
            ("Vmax - Longitudinal", Vmax, "longitudinal", self.L_vano, False),
            ("Vmax - Oblicua", Vmax, "oblicuo", self.L_vano/2, True),
            ("Vmed - Transversal", Vmed, "transversal", self.L_vano, False),
            ("Vmed - Longitudinal", Vmed, "longitudinal", self.L_vano, False),
            ("Vmed - Oblicua", Vmed, "oblicuo", self.L_vano/2, True)
        ]
        
        print(f"\n🔍 DEBUG generar_cargas_viento:")
        print(f"   Vmax={Vmax:.1f} m/s, Vmed={Vmed:.1f} m/s, L_vano={self.L_vano:.1f} m")
        print(f"   Escenarios a calcular: {len(escenarios_viento)}")
        
        cables_config = [
            ("Conductor", self.cable_conductor, self.Zco, self.Cf_cable, d_conductor, d_conductor_eff),
            ("Cable Guardia 1", self.cable_guardia1, self.Zcg, self.Cf_guardia, d_guardia1, d_guardia1_eff)
        ]
        
        if self.cable_guardia2:
            cables_config.append(
                ("Cable Guardia 2", self.cable_guardia2, self.Zcg, self.Cf_guardia, d_guardia2, d_guardia2_eff)
            )
        
        # Cargas en cables
        for vel_label, V, direccion, factor_vano, es_oblicuo in escenarios_viento:
            for elemento, cable_obj, Z, Cf, d_base, d_eff in cables_config:
                d_use = d_eff if "Vmed" in vel_label else d_base
                
                if es_oblicuo:
                    for lado in [1, 2]:
                        phi_rel = self.calcular_angulo_relativo_cable(self.theta, alpha_mitad, lado, direccion)
                        resultado = self.calcular_carga_viento_cable(cable_obj, V, Z, Cf, d_use, phi_rel, factor_vano)
                        fuerza_cable = resultado['total']
                        
                        alpha_mitad_rad = math.radians(alpha_mitad)
                        f_estructura_trans = fuerza_cable * math.cos(alpha_mitad_rad)
                        f_estructura_long = fuerza_cable * math.sin(alpha_mitad_rad)
                        
                        rows.append({
                            "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": "Oblicuo",
                            "Elemento": elemento, "Descripción": f"Sobre CABLE (Lado {lado})",
                            "Fu_daN_per_m": round(resultado['unitario'], 2),
                            "F_total_daN": round(fuerza_cable, 2),
                            "Angulo": f"{phi_rel:.1f}°"
                        })
                        
                        rows.append({
                            "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": "Transversal",
                            "Elemento": elemento, "Descripción": f"Sobre ESTRUCTURA (Lado {lado})",
                            "Fu_daN_per_m": None,
                            "F_total_daN": round(f_estructura_trans, 2),
                            "Angulo": "Estruct."
                        })
                        
                        rows.append({
                            "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": "Longitudinal",
                            "Elemento": elemento, "Descripción": f"Sobre ESTRUCTURA (Lado {lado})",
                            "Fu_daN_per_m": None,
                            "F_total_daN": round(f_estructura_long, 2),
                            "Angulo": "Estruct."
                        })
                else:
                    phi_rel = self.calcular_angulo_relativo_cable(self.theta, alpha_mitad, 1, direccion)
                    resultado = self.calcular_carga_viento_cable(cable_obj, V, Z, Cf, d_use, phi_rel, factor_vano)
                    
                    direccion_label = "Transversal" if direccion == "transversal" else "Longitudinal"
                    rows.append({
                        "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": direccion_label,
                        "Elemento": elemento, "Descripción": f"Sobre CABLE ({direccion_label})",
                        "Fu_daN_per_m": round(resultado['unitario'], 2), 
                        "F_total_daN": round(resultado['total'], 2), 
                        "Angulo": f"{phi_rel:.1f}°"
                    })
        
        # Elementos estructurales
        elementos_config = [
            (self.cadena, "Cadena de Aisladores"),
            (self.estructura, "Estructura")
        ]
        
        for vel_label, V in [("Vmax - Transversal", Vmax), ("Vmax - Longitudinal", Vmax),
                             ("Vmed - Transversal", Vmed), ("Vmed - Longitudinal", Vmed)]:
            direccion = "Transversal" if "Transversal" in vel_label else "Longitudinal"
            angulo_theta = 90 if direccion == "Transversal" else 0
            
            for elemento_obj, nombre in elementos_config:
                resultado = elemento_obj.cargaViento(
                    V=V, theta_deg=angulo_theta, exp=self.exposicion, clase=self.clase, Q=0.613, L_vano=self.L_vano
                )
                
                rows.append({
                    "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": direccion,
                    "Elemento": nombre, "Descripción": f"Sobre {nombre.split()[0]} ({direccion})",
                    "Fu_daN_per_m": None, "F_total_daN": round(resultado["fuerza_total_daN"], 2), 
                    "Angulo": f"{angulo_theta:.1f}°"
                })
        
        # Viento oblicuo en estructura y cadena
        for vel_label, V in [("Vmax - Oblicua", Vmax), ("Vmed - Oblicua", Vmed)]:
            resultado_estructura = self.estructura.cargaViento(
                V=V, theta_deg=self.theta, exp=self.exposicion, clase=self.clase, Q=0.613, L_vano=self.L_vano
            )
            resultado_cadena = self.cadena.cargaViento(
                V=V, theta_deg=self.theta, exp=self.exposicion, clase=self.clase, Q=0.613, L_vano=self.L_vano
            )
            
            f_total_trans_est = resultado_estructura["fuerza_transversal_daN"]
            f_total_long_est = resultado_estructura["fuerza_longitudinal_daN"]
            f_total_trans_cad = resultado_cadena["fuerza_transversal_daN"]
            f_total_long_cad = resultado_cadena["fuerza_longitudinal_daN"]
            
            rows.extend([
                {
                    "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": "Transversal",
                    "Elemento": "Estructura", "Descripción": "Sobre Estructura (Oblicuo)",
                    "Fu_daN_per_m": None, "F_total_daN": round(f_total_trans_est, 2), "Angulo": f"{self.theta}°"
                },
                {
                    "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": "Longitudinal", 
                    "Elemento": "Estructura", "Descripción": "Sobre Estructura (Oblicuo)",
                    "Fu_daN_per_m": None, "F_total_daN": round(f_total_long_est, 2), "Angulo": f"{self.theta}°"
                },
                {
                    "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": "Transversal",
                    "Elemento": "Cadena de Aisladores", "Descripción": "Sobre Cadena (Oblicuo)",
                    "Fu_daN_per_m": None, "F_total_daN": round(f_total_trans_cad, 2), "Angulo": f"{self.theta}°"
                },
                {
                    "Velocidad_label": vel_label, "Velocidad_m_s": V, "Dirección": "Longitudinal",
                    "Elemento": "Cadena de Aisladores", "Descripción": "Sobre Cadena (Oblicuo)",
                    "Fu_daN_per_m": None, "F_total_daN": round(f_total_long_cad, 2), "Angulo": f"{self.theta}°"
                }
            ])
        
        self.df_cargas = pd.DataFrame(rows)
        return self.df_cargas
    
    def obtener_carga_optimizada(self, elemento, direccion, velocidad_label, desc_adicional=""):
        """Obtiene cargas del DataFrame con cache"""
        clave_cache = f"{elemento}_{direccion}_{velocidad_label}_{desc_adicional}"
        
        if clave_cache not in self.cargas_cache:
            try:
                filtro = (self.df_cargas['Elemento'] == elemento) & \
                         (self.df_cargas['Dirección'] == direccion) & \
                         (self.df_cargas['Velocidad_label'] == velocidad_label)
                if desc_adicional:
                    filtro = filtro & (self.df_cargas['Descripción'].str.contains(desc_adicional))
                
                # DEBUG: Mostrar qué se encontró
                filas_encontradas = self.df_cargas[filtro]
                print(f"      🔍 Buscando: elemento='{elemento}', dirección='{direccion}', velocidad='{velocidad_label}'")
                print(f"         Filas encontradas: {len(filas_encontradas)}")
                if not filas_encontradas.empty:
                    for idx, row in filas_encontradas.iterrows():
                        print(f"         - {row['Descripción']}: {row['F_total_daN']:.2f} daN (V={row['Velocidad_m_s']:.1f} m/s)")
                
                resultado = self.df_cargas[filtro]['F_total_daN'].iloc[0] if not self.df_cargas[filtro].empty else 0.0
                self.cargas_cache[clave_cache] = round(resultado, 2) if resultado is not None else 0.0
            except:
                self.cargas_cache[clave_cache] = 0.0
        
        return self.cargas_cache[clave_cache]
    
    def generar_lista_cargas(self, resultados_conductor, resultados_guardia1, resultados_guardia2=None):
        """Genera lista completa de cargas"""
        if self.df_cargas is None:
            raise ValueError("Debe ejecutar generar_cargas_viento() primero")
        
        # Datos base
        peso_conductor_base = self.cable_conductor.peso_unitario_dan_m
        peso_guardia1_base = self.cable_guardia1.peso_unitario_dan_m
        peso_hielo_conductor = self.cable_conductor._calcular_peso_hielo(self.t_hielo, 900)
        peso_hielo_guardia1 = self.cable_guardia1._calcular_peso_hielo(self.t_hielo, 900)
        
        Pc = round(peso_conductor_base * self.L_vano, 2)
        Pcg1 = round(peso_guardia1_base * self.L_vano, 2)
        Pch = round(peso_hielo_conductor * self.L_vano, 2)
        Pcg1h = round(peso_hielo_guardia1 * self.L_vano, 2)
        
        if self.cable_guardia2:
            peso_guardia2_base = self.cable_guardia2.peso_unitario_dan_m
            peso_hielo_guardia2 = self.cable_guardia2._calcular_peso_hielo(self.t_hielo, 900)
            Pcg2 = round(peso_guardia2_base * self.L_vano, 2)
            Pcg2h = round(peso_hielo_guardia2 * self.L_vano, 2)
        
        estados_climaticos_map = {"I": "Tmax", "II": "Tmin", "III": "Vmax", "IV": "Vmed", "V": "Tma"}
        
        cargas_data = []
        id_counter = 1
        
        def agregar_carga(elemento, codigo, descripcion, estado_climatico, magnitud, direccion):
            nonlocal id_counter
            if isinstance(magnitud, float):
                magnitud = round(magnitud, 2)
            
            cargas_data.append({
                "ID": id_counter, "Elemento": elemento, "Código": codigo, 
                "Carga": descripcion, "Estado Climático": estado_climatico, 
                "Magnitud": magnitud, "Unidad": "daN", "Direccion": direccion
            })
            id_counter += 1
        
        # Cargas verticales
        cargas_verticales = [
            ("Conductor", "Pc", "Peso de Gravivano", "NA", Pc, "Vertical"),
            ("Cable Guardia 1", "Pcg1", "Peso de Gravivano", "NA", Pcg1, "Vertical"),
            ("Conductor", "Pch", "Peso adicional por hielo", "NA", Pch, "Vertical"),
            ("Cable Guardia 1", "Pcg1h", "Peso Adicional por hielo", "NA", Pcg1h, "Vertical"),
        ]
        
        if self.cable_guardia2:
            cargas_verticales.extend([
                ("Cable Guardia 2", "Pcg2", "Peso de Gravivano", "NA", Pcg2, "Vertical"),
                ("Cable Guardia 2", "Pcg2h", "Peso Adicional por hielo", "NA", Pcg2h, "Vertical"),
            ])
        
        cargas_verticales.extend([
            ("Cadena", "Pa", "Peso de Cadena de Aisladores y Herrajes", "NA", self.PCADENA, "Vertical"),
            ("Estructura", "CS", "Carga de Servicio", "NA", self.CS, "Vertical")
        ])
        
        for carga in cargas_verticales:
            agregar_carga(*carga)
        
        # Viento máximo - cables
        cargas_viento_max = [
            ("Conductor", "Transversal", "Vc", "Viento Máximo en Eolovano", "Vmax"),
            ("Conductor", "Longitudinal", "VcL", "Viento Máximo en Eolovano", "Vmax"),
            ("Cable Guardia 1", "Transversal", "Vcg1", "Viento Máximo en Eolovano", "Vmax"), 
            ("Cable Guardia 1", "Longitudinal", "Vcg1L", "Viento Máximo en Eolovano", "Vmax")
        ]
        
        if self.cable_guardia2:
            cargas_viento_max.extend([
                ("Cable Guardia 2", "Transversal", "Vcg2", "Viento Máximo en Eolovano", "Vmax"),
                ("Cable Guardia 2", "Longitudinal", "Vcg2L", "Viento Máximo en Eolovano", "Vmax")
            ])
        
        print(f"\n🔍 DEBUG ListarCargas: Generando cargas de viento máximo...")
        for elemento, direccion, codigo, descripcion, estado in cargas_viento_max:
            magnitud = self.obtener_carga_optimizada(elemento, direccion, f"{estado} - {direccion}")
            print(f"   {codigo}: elemento='{elemento}', dirección='{direccion}', filtro='{estado} - {direccion}' → {magnitud:.2f} daN")
            agregar_carga(elemento, codigo, descripcion, estado, magnitud, direccion)
        
        # Viento máximo oblicuo - cables
        elementos_oblicuo = ["Conductor", "Cable Guardia 1"]
        if self.cable_guardia2:
            elementos_oblicuo.append("Cable Guardia 2")
        
        for elemento in elementos_oblicuo:
            for lado in [1, 2]:
                if elemento == "Conductor":
                    codigo_base = "Vc_o"
                elif elemento == "Cable Guardia 1":
                    codigo_base = "Vcg1_o"
                else:
                    codigo_base = "Vcg2_o"
                
                desc_base = f"Viento Máximo en Eolovano - Oblícuo - Lado {lado}"
                
                magnitud_trans = self.obtener_carga_optimizada(elemento, "Transversal", "Vmax - Oblicua", f"Lado {lado}")
                agregar_carga(elemento, f"{codigo_base}_t_{lado}", desc_base, "Vmax", magnitud_trans, "Transversal")
                
                magnitud_long = self.obtener_carga_optimizada(elemento, "Longitudinal", "Vmax - Oblicua", f"Lado {lado}")
                agregar_carga(elemento, f"{codigo_base}_l_{lado}", desc_base, "Vmax", magnitud_long, "Longitudinal")
        
        # Viento medio - cables
        cargas_viento_med = [
            ("Conductor", "Transversal", "Vcmed", "Viento Medio en Eolovano", "Vmed"),
            ("Conductor", "Longitudinal", "VcmedL", "Viento Medio en Eolovano", "Vmed"),
            ("Cable Guardia 1", "Transversal", "Vcg1med", "Viento Medio en Eolovano", "Vmed"),
            ("Cable Guardia 1", "Longitudinal", "Vcg1medL", "Viento Medio en Eolovano", "Vmed")
        ]
        
        if self.cable_guardia2:
            cargas_viento_med.extend([
                ("Cable Guardia 2", "Transversal", "Vcg2med", "Viento Medio en Eolovano", "Vmed"),
                ("Cable Guardia 2", "Longitudinal", "Vcg2medL", "Viento Medio en Eolovano", "Vmed")
            ])
        
        for elemento, direccion, codigo, descripcion, estado in cargas_viento_med:
            magnitud = self.obtener_carga_optimizada(elemento, direccion, f"{estado} - {direccion}")
            agregar_carga(elemento, codigo, descripcion, estado, magnitud, direccion)
        
        # Viento medio oblicuo - cables
        for elemento in elementos_oblicuo:
            for lado in [1, 2]:
                if elemento == "Conductor":
                    codigo_base = "Vcmed_o"
                elif elemento == "Cable Guardia 1":
                    codigo_base = "Vcg1med_o"
                else:
                    codigo_base = "Vcg2med_o"
                
                desc_base = f"Viento Medio en Eolovano - Oblícuo - Lado {lado}"
                
                magnitud_trans = self.obtener_carga_optimizada(elemento, "Transversal", "Vmed - Oblicua", f"Lado {lado}")
                agregar_carga(elemento, f"{codigo_base}_t_{lado}", desc_base, "Vmed", magnitud_trans, "Transversal")
                
                magnitud_long = self.obtener_carga_optimizada(elemento, "Longitudinal", "Vmed - Oblicua", f"Lado {lado}")
                agregar_carga(elemento, f"{codigo_base}_l_{lado}", desc_base, "Vmed", magnitud_long, "Longitudinal")
        
        # Elementos estructurales - viento
        for elemento, codigo_t_max, codigo_l_max, codigo_t_med, codigo_l_med, nombre_completo in [
            ("Cadena", "VaT", "VaL", "VamedT", "VamedL", "Cadena de Aisladores"),
            ("Estructura", "VeT", "VeL", "Vemedt", "Vemedl", "Estructura")
        ]:
            magnitud_t_max = self.obtener_carga_optimizada(nombre_completo, "Transversal", "Vmax - Transversal")
            magnitud_l_max = self.obtener_carga_optimizada(nombre_completo, "Longitudinal", "Vmax - Longitudinal")
            
            agregar_carga(elemento, codigo_t_max, f"Viento Máximo en {nombre_completo}", "Vmax", magnitud_t_max, "Transversal")
            agregar_carga(elemento, codigo_l_max, f"Viento Máximo en {nombre_completo}", "Vmax", magnitud_l_max, "Longitudinal")
            
            magnitud_t_med = self.obtener_carga_optimizada(nombre_completo, "Transversal", "Vmed - Transversal")
            magnitud_l_med = self.obtener_carga_optimizada(nombre_completo, "Longitudinal", "Vmed - Longitudinal")
            
            agregar_carga(elemento, codigo_t_med, f"Viento Medio en {nombre_completo}", "Vmed", magnitud_t_med, "Transversal")
            agregar_carga(elemento, codigo_l_med, f"Viento Medio en {nombre_completo}", "Vmed", magnitud_l_med, "Longitudinal")
        
        # Viento oblicuo en estructura y cadena
        for vel_label, estado in [("Vmax - Oblicua", "Vmax"), ("Vmed - Oblicua", "Vmed")]:
            codigo_transv_est = "VeoT" if estado == "Vmax" else "VemedoT"
            codigo_long_est = "VeoL" if estado == "Vmax" else "VemedoL"
            codigo_transv_cad = "VaoT" if estado == "Vmax" else "VaoTmed"
            codigo_long_cad = "VaoL" if estado == "Vmax" else "VaoLmed"
            
            magnitud_trans_est = self.obtener_carga_optimizada("Estructura", "Transversal", vel_label, "Oblicuo")
            magnitud_long_est = self.obtener_carga_optimizada("Estructura", "Longitudinal", vel_label, "Oblicuo")
            magnitud_trans_cad = self.obtener_carga_optimizada("Cadena de Aisladores", "Transversal", vel_label, "Oblicuo")
            magnitud_long_cad = self.obtener_carga_optimizada("Cadena de Aisladores", "Longitudinal", vel_label, "Oblicuo")
            
            agregar_carga("Estructura", codigo_transv_est, f"Viento {estado} sobre Estructura - Oblicuo - Comp. Transv.", estado, magnitud_trans_est, "Transversal")
            agregar_carga("Estructura", codigo_long_est, f"Viento {estado} sobre Estructura - Oblicuo - Comp. Long.", estado, magnitud_long_est, "Longitudinal")
            agregar_carga("Cadena", codigo_transv_cad, f"Viento {estado} sobre Cadena - Oblicuo - Comp. Transv.", estado, magnitud_trans_cad, "Transversal")
            agregar_carga("Cadena", codigo_long_cad, f"Viento {estado} sobre Cadena - Oblicuo - Comp. Long.", estado, magnitud_long_cad, "Longitudinal")
        
        # Tiros de cables
        def obtener_tiro_estado(resultados_dict, estado, componente="longitudinal"):
            if estado in resultados_dict:
                tiro_total = resultados_dict[estado]["tiro_daN"]
                alpha_rad = math.radians(self.alpha / 2.0)
                if componente == "transversal":
                    return round(tiro_total * math.sin(alpha_rad), 2)
                else:
                    return round(tiro_total * math.cos(alpha_rad), 2)
            return 0.0
        
        tiros_config = [
            ("Conductor", resultados_conductor, "c", "conductor"),
            ("Cable Guardia 1", resultados_guardia1, "cg1", "cable de guardia 1")
        ]
        
        if resultados_guardia2:
            tiros_config.append(
                ("Cable Guardia 2", resultados_guardia2, "cg2", "cable de guardia 2")
            )
        
        for elemento, resultados_dict, prefijo, nombre_desc in tiros_config:
            for estado, nombre_estado in estados_climaticos_map.items():
                for componente, sufijo in [("transversal", "t"), ("longitudinal", "l")]:
                    codigo = f"T{nombre_estado.lower()}_{prefijo}_{sufijo}"
                    magnitud = obtener_tiro_estado(resultados_dict, estado, componente)
                    descripcion = f"Componente {componente.title()} - Tiro {nombre_estado.lower()} de {nombre_desc}"
                    
                    agregar_carga(elemento, codigo, descripcion, nombre_estado, magnitud, componente.title())
        
        self.df_cargas_totales = pd.DataFrame(cargas_data)
        return self.df_cargas_totales
    
    def guardar_resultados(self, folder, tipoestructura_nombre_archivo):
        """Guarda los DataFrames en archivos CSV"""
        os.makedirs(folder, exist_ok=True)
        
        if self.df_cargas is not None:
            ruta_cargas = f"{folder}/1_{tipoestructura_nombre_archivo}_Cargas_Viento.csv"
            self.df_cargas.to_csv(ruta_cargas, index=False, encoding='utf-8')
            print(f"💾 Cargas de viento guardadas en: {ruta_cargas}")
        
        if self.df_cargas_totales is not None:
            ruta_totales = f"{folder}/3_{tipoestructura_nombre_archivo}_LISTA_TOTAL_DE_CARGAS.csv"
            self.df_cargas_totales.to_csv(ruta_totales, index=False, encoding='utf-8')
            print(f"💾 Lista total de cargas guardada en: {ruta_totales}")
