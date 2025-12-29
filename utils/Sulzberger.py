import numpy as np
import pandas as pd
import math

class Sulzberger:
    """
    Clase para cálculo de fundaciones usando el método Sulzberger
    Basado en la lógica del Excel FUNDACIONES-AGPK-V2.xlsx
    """
    
    def __init__(self, parametros_estructura=None, parametros_suelo=None, parametros_calculo=None):
        # Parámetros por defecto basados en el Excel
        self.parametros_estructura = parametros_estructura or {}
        self.parametros_suelo = parametros_suelo or self._get_default_suelo()
        self.parametros_calculo = parametros_calculo or self._get_default_calculo()
        
        # Resultados del cálculo
        self.resultados = {}
        self.verificaciones = {}
        self.memoria_calculo = []
        
    def _get_default_suelo(self):
        """Parámetros por defecto del suelo basados en el Excel"""
        return {
            'C': 5.0e6,          # Índice de compresibilidad [kg/m3]
            'sigma_adm': 50000,   # Presión admisible [kg/m2]
            'beta': 8.0,         # Ángulo de tierra gravante [grados]
            'mu': 0.40,          # Coeficiente de fricción terreno-hormigón
            'gamma_tierra': 3800, # Densidad tierra [kg/m3]
            'gamma_hor': 2200    # Densidad hormigón [kg/m3]
        }
    
    def _get_default_calculo(self):
        """Parámetros por defecto de cálculo basados en el Excel"""
        return {
            'FS': 1.5,           # Factor de seguridad al volcamiento
            'tg_alfa_adm': 0.01, # Inclinación admisible por desplazamiento
            't_he_max': 1.25,    # Relación máx. sin armadura
            'sigma_max_adm': 1.33, # Superación presión admisible
            'incremento': 0.01,  # Incremento para iteraciones [m]
            'cacb': 1.20,       # Coeficiente aumento Cb respecto Ct
            'max_iteraciones': 10000, # Máximo número de iteraciones
            't_max': 3.0,       # Profundidad máxima [m]
            'coef_dmed': 0.015, # Coeficiente para diámetro medio
            'factor_rombica': 0.5 # Factor de forma para base rómbica
        }
    
    def configurar_estructura(self, Gp, Tiro_x, Tiro_y, Tiro_z, h, hl, he, dc, n_postes=1):
        """Configurar parámetros de la estructura desde SPH y DME"""
        # Calcular diámetro medio empotrado
        coef_conicidad = self.parametros_calculo.get('coef_dmed', 0.015)
        dmed = dc * (1 + coef_conicidad * (hl + he/2))
        
        # Calcular Gp efectivo según método Sulzberger
        if Tiro_z < 0:  # Compresión
            peso_adicional = (-1) * Tiro_z / 0.981  # Inversión de signo
        else:  # Tracción
            peso_adicional = Tiro_z / 0.981  # Sin inversión
        Gp_efectivo = Gp + peso_adicional
        
        self.parametros_estructura.update({
            'Gp': Gp_efectivo,    # Masa efectiva total [kg]
            'Tiro_x': Tiro_x,     # Fuerza transversal [kgf]
            'Tiro_y': Tiro_y,     # Fuerza longitudinal [kgf]
            'h': h,               # Altura total [m]
            'hl': hl,             # Altura libre [m]
            'he': he,             # Altura empotrada [m]
            'dc': dc,             # Diámetro en cima [m]
            'dmed': dmed,         # Diámetro medio empotrado [m]
            'n_postes': n_postes  # Número de postes
        })
    
    def calcular_fundacion(self, tin=1.7, ain=1.3, bin=1.3, tipo_base='Rombica'):
        """
        Calcular fundación usando método Sulzberger verdadero
        """
        self.memoria_calculo = []
        self._log(f"=== CÁLCULO FUNDACIÓN SULZBERGER ===")
        self._log(f"Tipo de base: {tipo_base}")
        self._log(f"Dimensiones iniciales: t={tin}m, a={ain}m, b={bin}m")
        
        # Dimensiones actuales
        t, a, b = tin, ain, bin
        
        # Parámetros de estructura - verificar que existan
        if not self.parametros_estructura:
            raise ValueError("Debe configurar parámetros de estructura antes de calcular")
        
        Gp = self.parametros_estructura.get('Gp')
        Tiro_x = self.parametros_estructura.get('Tiro_x')
        Tiro_y = self.parametros_estructura.get('Tiro_y')
        he = self.parametros_estructura.get('he')
        hl = self.parametros_estructura.get('hl')
        dmed = self.parametros_estructura.get('dmed')
        n_postes = self.parametros_estructura.get('n_postes', 1)
        
        if any(param is None for param in [Gp, Tiro_x, Tiro_y, he, hl, dmed]):
            raise ValueError("Faltan parámetros de estructura: Gp, Tiro_x, Tiro_y, he, hl, dmed")
        
        # Parámetros de suelo y cálculo
        gamma_hor = self.parametros_suelo['gamma_hor']
        gamma_tierra = self.parametros_suelo['gamma_tierra']
        C = self.parametros_suelo['C']
        beta = math.radians(self.parametros_suelo['beta'])
        cacb = self.parametros_calculo['cacb']
        FS_req = self.parametros_calculo['FS']
        tg_alfa_adm = self.parametros_calculo['tg_alfa_adm']
        mu = self.parametros_suelo['mu']
        
        max_iteraciones = self.parametros_calculo.get('max_iteraciones', 10000)
        iteracion = 0
        
        while iteracion < max_iteraciones:
            iteracion += 1
            
            if iteracion == 1 or iteracion % 50 == 0:
                self._log(f"\n--- Iteración {iteracion} ---")
                self._log(f"Dimensiones: t={t:.3f}m, a={a:.3f}m, b={b:.3f}m")
            
            # 1. VOLUMEN Y MASA TOTAL (método Sulzberger)
            # Volumen hormigón = volumen base - volumen hueco postes
            if tipo_base == 'Rombica':
                V_base = a * b * t
            else:  # Cuadrada
                V_base = a * b * t
            
            # Restar volumen hueco de postes empotrados
            V_hueco_postes = (0.25 * math.pi * dmed**2) * he * n_postes
            V_hormigon = V_base - V_hueco_postes
            G_hormigon = V_hormigon * gamma_hor
            
            # Volumen tierra gravante (fórmula Sulzberger)
            tan_beta = math.tan(beta)
            term_2t_tan_beta = 2 * t * tan_beta
            V_tierra_gravante = (t/3) * ((a*b + (a+term_2t_tan_beta)*(b+term_2t_tan_beta)) + 
                                        math.sqrt(a*b*(a+term_2t_tan_beta)*(b+term_2t_tan_beta))) - a*b*t
            G_tierra_gravante = V_tierra_gravante * gamma_tierra
            
            # Masa total
            G_total = Gp + G_hormigon + G_tierra_gravante
            
            if iteracion == 1 or iteracion % 50 == 0:
                self._log(f"Volumen hormigón: {V_hormigon:.3f} m³ (base: {V_base:.3f} - huecos: {V_hueco_postes:.3f})")
                self._log(f"Masa total: {G_total:.0f} kg (poste: {Gp:.0f} + hormigón: {G_hormigon:.0f} + tierra: {G_tierra_gravante:.0f})")
            
            # 2. INCLINACIONES (método Sulzberger)
            C_t = C * t  # Índice de compresibilidad ajustado
            
            # Inclinaciones tipo 1 (por fricción)
            if tipo_base == 'Rombica':
                tg_alfa1t = 4.5 * mu * G_total / (b * t**2 * C_t)
                tg_alfa1l = 4.5 * mu * G_total / (a * t**2 * C_t)
            else:  # Cuadrada
                tg_alfa1t = 6 * mu * G_total / (b * t**2 * C_t)
                tg_alfa1l = 6 * mu * G_total / (a * t**2 * C_t)
            
            # Inclinaciones tipo 2 (por compresibilidad)
            if tipo_base == 'Rombica':
                tg_alfa2t = math.sqrt(2) * G_total / (a**2 * b * C_t * cacb)
                tg_alfa2l = math.sqrt(2) * G_total / (b**2 * a * C_t * cacb)
            else:  # Cuadrada
                tg_alfa2t = 2 * G_total / (a**2 * b * C_t * cacb)
                tg_alfa2l = 2 * G_total / (b**2 * a * C_t * cacb)
            
            # 3. MOMENTOS OPOSITORES (método Sulzberger)
            # Determinar caso según inclinaciones
            caso_t = 2 if min(tg_alfa1t, tg_alfa2t) <= tg_alfa_adm else 1
            caso_l = 2 if min(tg_alfa1l, tg_alfa2l) <= tg_alfa_adm else 1
            
            # Momentos según caso
            if caso_t == 1:  # Eje en 2/3 t
                if tipo_base == 'Rombica':
                    mst = math.sqrt(2) * b * t**3 * C_t * tg_alfa1t / 12
                    mbt = math.sqrt(2) * b * a**3 * C_t * cacb * tg_alfa2t / 12
                else:
                    mst = b * t**3 * C_t * tg_alfa1t / 12
                    mbt = b * a**3 * C_t * cacb * tg_alfa2t / 12
                mot = mst + mbt
                rel_mt = mst / mbt if mbt > 0 else float('inf')
                st = 1.48 - 0.842*rel_mt + 0.364*rel_mt**2 if 0 < rel_mt < 1 else 1.0
                mvt = st * Tiro_x * (hl + 2/3 * t)
            else:  # Caso 2: Eje en base
                if tipo_base == 'Rombica':
                    mst = math.sqrt(2) * b * t**3 * C_t * tg_alfa1t / 36
                    mbt = G_total * (math.sqrt(2) * 0.5 * a - 0.5 * (G_total * tg_alfa2t / (C_t * cacb))**(1/3))
                else:
                    mst = b * t**3 * C_t * tg_alfa1t / 36
                    mbt = G_total * (a * 0.5 - 0.47 * math.sqrt(G_total / (b * C_t * cacb * tg_alfa2t)))
                mot = mst + mbt
                rel_mt = mst / mbt if mbt > 0 else float('inf')
                st = 1.48 - 0.842*rel_mt + 0.364*rel_mt**2 if 0 < rel_mt < 1 else 1.0
                mvt = st * Tiro_x * (hl + t)
            
            # Mismo cálculo para longitudinal
            if caso_l == 1:
                if tipo_base == 'Rombica':
                    msl = math.sqrt(2) * a * t**3 * C_t * tg_alfa1l / 12
                    mbl = math.sqrt(2) * a * b**3 * C_t * cacb * tg_alfa2l / 12
                else:
                    msl = a * t**3 * C_t * tg_alfa1l / 12
                    mbl = a * b**3 * C_t * cacb * tg_alfa2l / 12
                mol = msl + mbl
                rel_ml = msl / mbl if mbl > 0 else float('inf')
                sl = 1.48 - 0.842*rel_ml + 0.364*rel_ml**2 if 0 < rel_ml < 1 else 1.0
                mvl = sl * Tiro_y * (hl + 2/3 * t)
            else:
                if tipo_base == 'Rombica':
                    msl = math.sqrt(2) * a * t**3 * C_t * tg_alfa1l / 36
                    mbl = G_total * (math.sqrt(2) * 0.5 * b - 0.5 * (G_total * tg_alfa2l / (C_t * cacb))**(1/3))
                else:
                    msl = a * t**3 * C_t * tg_alfa1l / 36
                    mbl = G_total * (b * 0.5 - 0.47 * math.sqrt(G_total / (a * C_t * cacb * tg_alfa2l)))
                mol = msl + mbl
                rel_ml = msl / mbl if mbl > 0 else float('inf')
                sl = 1.48 - 0.842*rel_ml + 0.364*rel_ml**2 if 0 < rel_ml < 1 else 1.0
                mvl = sl * Tiro_y * (hl + t)
            
            # 4. FACTORES DE SEGURIDAD
            FSt = mot / mvt if mvt > 0 and Tiro_x > 0 else float('inf')
            FSl = mol / mvl if mvl > 0 and Tiro_y > 0 else float('inf')
            
            # 5. VERIFICACIONES
            verif_FSt = FSt >= FS_req
            verif_FSl = FSl >= FS_req
            verif_incl_t = caso_t >= 2  # Caso 2 significa inclinaciones aceptables
            verif_incl_l = caso_l >= 2
            
            # Presión en fondo
            sigma = G_total / (a * b)
            verif_presion = sigma <= self.parametros_suelo['sigma_adm'] * self.parametros_calculo['sigma_max_adm']
            
            # Relación t/he
            rel_t_he = t / he
            verif_t_he = rel_t_he <= self.parametros_calculo['t_he_max']
            
            if iteracion == 1 or iteracion % 50 == 0:
                self._log(f"FS transversal: {FSt:.3f} (caso {caso_t}), FS longitudinal: {FSl:.3f} (caso {caso_l})")
                self._log(f"Verificaciones: FSt={verif_FSt}, FSl={verif_FSl}, incl_t={verif_incl_t}, incl_l={verif_incl_l}, presión={verif_presion}, t/he={verif_t_he}")
            
            # Si todas las verificaciones pasan, terminar
            if all([verif_FSt, verif_FSl, verif_incl_t, verif_incl_l, verif_presion, verif_t_he]):
                if iteracion > 1:
                    self._log(f"\nTODAS LAS VERIFICACIONES CUMPLEN EN ITERACIÓN {iteracion}")
                break
            
            # 6. AJUSTE DE DIMENSIONES (método Sulzberger)
            t_max = self.parametros_calculo.get('t_max', 3.0)
            prueba_arm = rel_t_he > 0.99 * self.parametros_calculo['t_he_max']
            
            if not all([verif_FSt, verif_FSl, verif_incl_t, verif_incl_l]):
                if not prueba_arm and t < t_max:  # Incrementar profundidad
                    t += self.parametros_calculo['incremento']
                else:  # Incrementar dimensiones base
                    a += self.parametros_calculo['incremento']
                    b += self.parametros_calculo['incremento']
            elif not verif_presion:
                a += self.parametros_calculo['incremento']
                b += self.parametros_calculo['incremento']
            else:
                break
        
        # Guardar resultados finales
        self.resultados = {
            'a': a,
            'b': b,
            't': t,
            'volumen': V_hormigon,
            'FSt': FSt,
            'FSl': FSl,
            'caso_t': caso_t,
            'caso_l': caso_l,
            'sigma': sigma,
            'rel_t_he': rel_t_he,
            'iteraciones': iteracion,
            'convergencia': iteracion < max_iteraciones
        }
        
        return self.resultados
    
    def _volumen_rombica(self, a, b, t):
        """Calcular volumen de base rómbica"""
        # Fórmula correcta para base rómbica: V = (a * b * t) / 2
        # Para base rómbica real, usar factor de forma
        factor_rombica = self.parametros_calculo.get('factor_rombica', 0.5)
        return a * b * t * factor_rombica
    
    def _calcular_presion_maxima(self, G_total, Tiro_x, Tiro_y, a, b, t):
        """Calcular presión máxima en el suelo"""
        if G_total <= 0:
            return 0
        
        area = a * b
        sigma_media = G_total / area
        
        # Momentos por fuerzas horizontales
        M_t = Tiro_x * (self.parametros_estructura.get('he', 0) + t)
        M_l = Tiro_y * (self.parametros_estructura.get('he', 0) + t)
        
        # Excentricidades
        e_t = M_t / G_total if G_total > 0 else 0
        e_l = M_l / G_total if G_total > 0 else 0
        
        # Verificar que no exceda el núcleo central
        if abs(e_t) > a/6 or abs(e_l) > b/6:
            # Fuera del núcleo central - usar distribución triangular
            if abs(e_t) > a/6:
                sigma_max = 2 * G_total / (3 * b * (a/2 - abs(e_t)))
            else:
                sigma_max = 2 * G_total / (3 * a * (b/2 - abs(e_l)))
        else:
            # Dentro del núcleo central - distribución trapezoidal
            sigma_max = sigma_media * (1 + 6*abs(e_t)/a + 6*abs(e_l)/b)
        
        return max(sigma_max, sigma_media)
    
    def _log(self, mensaje):
        """Agregar mensaje a la memoria de cálculo"""
        self.memoria_calculo.append(mensaje)
        print(mensaje)
    
    def calcular_fundacion_multiples_hipotesis(self, tin=1.7, ain=1.3, bin=1.3, tipo_base='Rombica'):
        """
        Calcular fundación para todas las hipótesis y retornar la de mayor volumen
        """
        self.memoria_calculo = []
        self._log(f"=== CÁLCULO FUNDACIÓN SULZBERGER - MÚTIPLES HIPÓTESIS ===")
        
        hipotesis_fuerzas = self.parametros_estructura.get('hipotesis_fuerzas', [])
        if not hipotesis_fuerzas:
            raise ValueError("No hay hipótesis de fuerzas disponibles")
        
        # Guardar Gp base (sin fuerzas verticales)
        Gp_base = self.parametros_estructura.get('Gp', 0)
        self.parametros_estructura['Gp_base'] = Gp_base
        self._log(f"Peso base del poste: {Gp_base:.0f} kg")
        
        resultados_todas = []
        max_volumen = 0
        resultado_final = None
        
        for hip_data in hipotesis_fuerzas:
            hipotesis = hip_data['hipotesis']
            Tiro_x = hip_data['Tiro_x']
            Tiro_y = hip_data['Tiro_y']
            Tiro_z = hip_data['Tiro_z']
            
            self._log(f"\n--- HIPÓTESIS {hipotesis} ---")
            self._log(f"Fuerzas: Tiro_x={Tiro_x:.1f} daN, Tiro_y={Tiro_y:.1f} daN, Fz={Tiro_z:.1f} daN")
            
            # Configurar fuerzas para esta hipótesis
            # Calcular Gp efectivo: usar método correcto de inversión de signo
            Gp_base = self.parametros_estructura.get('Gp_base', self.parametros_estructura.get('Gp', 0))
            if Tiro_z < 0:  # Fz negativo = compresión = peso adicional
                peso_adicional = (-1) * Tiro_z / 0.981  # Inversión de signo
                Gp_efectivo = Gp_base + peso_adicional
                self._log(f"Peso efectivo: Gp_base={Gp_base:.0f} kg + (-Fz)={peso_adicional:.0f} kg = {Gp_efectivo:.0f} kg")
            else:  # Fz positivo = tracción = resta peso
                peso_adicional = Tiro_z / 0.981  # Sin inversión
                Gp_efectivo = Gp_base + peso_adicional  # Suma algebraica (será negativo)
                self._log(f"Peso efectivo: Gp_base={Gp_base:.0f} kg + Fz={peso_adicional:.0f} kg = {Gp_efectivo:.0f} kg")
            
            # Configurar estructura con parámetros completos
            self.configurar_estructura(
                Gp=Gp_base,
                Tiro_x=Tiro_x,
                Tiro_y=Tiro_y,
                Tiro_z=Tiro_z,
                h=self.parametros_estructura.get('h', 15.0),
                hl=self.parametros_estructura.get('hl', 13.5),
                he=self.parametros_estructura.get('he', 1.5),
                dc=self.parametros_estructura.get('dc', 0.31),
                n_postes=self.parametros_estructura.get('n_postes', 1)
            )
            
            # Calcular fundación para esta hipótesis
            resultado_hip = self.calcular_fundacion(tin, ain, bin, tipo_base)
            resultado_hip['hipotesis'] = hipotesis
            resultado_hip['Tiro_x_input'] = Tiro_x
            resultado_hip['Tiro_y_input'] = Tiro_y
            resultado_hip['Tiro_z_input'] = Tiro_z
            resultado_hip['Gp_efectivo'] = Gp_efectivo
            
            resultados_todas.append(resultado_hip)
            
            # Verificar si es el mayor volumen
            if resultado_hip['volumen'] > max_volumen:
                max_volumen = resultado_hip['volumen']
                resultado_final = resultado_hip
            
            self._log(f"Volumen hipótesis {hipotesis}: {resultado_hip['volumen']:.3f} m³")
        
        self._log(f"\n=== RESULTADO FINAL ===")
        self._log(f"Hipótesis dimensionante: {resultado_final['hipotesis']}")
        self._log(f"Volumen máximo: {max_volumen:.3f} m³")
        
        # Guardar todos los resultados
        self.resultados_todas_hipotesis = resultados_todas
        self.resultado_dimensionante = resultado_final
        
        return {
            'resultado_final': resultado_final,
            'todas_hipotesis': resultados_todas,
            'hipotesis_dimensionante': resultado_final['hipotesis'],
            'volumen_maximo': max_volumen
        }
    
    def obtener_dataframe_todas_hipotesis(self):
        """Generar DataFrame con resultados de todas las hipótesis"""
        if not hasattr(self, 'resultados_todas_hipotesis'):
            return pd.DataFrame()
        
        data = []
        for resultado in self.resultados_todas_hipotesis:
            convergencia = resultado.get('convergencia', True)
            data.append({
                'Hipótesis': resultado['hipotesis'],
                'Tiro_x [daN]': resultado['Tiro_x_input'],
                'Tiro_y [daN]': resultado['Tiro_y_input'],
                'Fz [daN]': resultado['Tiro_z_input'],
                'Gp efectivo [kg]': f"{resultado['Gp_efectivo']:.0f}",
                'a [m]': f"{resultado['a']:.3f}",
                'b [m]': f"{resultado['b']:.3f}",
                't [m]': f"{resultado['t']:.3f}",
                'Volumen [m³]': f"{resultado['volumen']:.3f}",
                'FS Transversal': f"{resultado['FSt']:.3f}",
                'FS Longitudinal': f"{resultado['FSl']:.3f}",
                'Iteraciones': resultado['iteraciones'],
                'Convergencia': '🟢' if convergencia else '🔴',
                'Dimensionante': '🟡' if resultado == self.resultado_dimensionante else ''
            })
        
        return pd.DataFrame(data)
    
    def obtener_memoria_calculo(self):
        """Obtener memoria de cálculo como string"""
        return "\n".join(self.memoria_calculo)