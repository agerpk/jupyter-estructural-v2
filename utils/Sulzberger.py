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
            'max_iteraciones': 100, # Máximo número de iteraciones
            't_max': 3.0,       # Profundidad máxima [m]
            'coef_dmed': 0.015, # Coeficiente para diámetro medio
            'factor_rombica': 0.5 # Factor de forma para base rómbica
        }
    
    def configurar_estructura(self, Gp, Ft, Fl, h, hl, he, dc):
        """Configurar parámetros de la estructura desde SPH y DME"""
        self.parametros_estructura.update({
            'Gp': Gp,    # Masa total poste [kg]
            'Ft': Ft,    # Fuerza transversal [kgf]
            'Fl': Fl,    # Fuerza longitudinal [kgf]
            'h': h,      # Altura total [m]
            'hl': hl,    # Altura libre [m]
            'he': he,    # Altura empotrada [m]
            'dc': dc,    # Diámetro en cima [m]
            'dmed': dc * (1 + self.parametros_calculo.get('coef_dmed', 0.015) * (hl + he/2))  # Diámetro medio empotrado
        })
    
    def calcular_fundacion(self, tin=1.7, ain=1.3, bin=1.3, tipo_base='Rombica'):
        """
        Calcular fundación usando método Sulzberger
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
        Ft = self.parametros_estructura.get('Ft')
        Fl = self.parametros_estructura.get('Fl')
        he = self.parametros_estructura.get('he')
        
        if any(param is None for param in [Gp, Ft, Fl, he]):
            raise ValueError("Faltan parámetros de estructura: Gp, Ft, Fl, he")
        
        # Parámetros de suelo
        gamma_hor = self.parametros_suelo['gamma_hor']
        gamma_tierra = self.parametros_suelo['gamma_tierra']
        sigma_adm = self.parametros_suelo['sigma_adm']
        mu = self.parametros_suelo['mu']
        
        # Parámetros de cálculo
        FS_req = self.parametros_calculo['FS']
        tg_alfa_adm = self.parametros_calculo['tg_alfa_adm']
        
        max_iteraciones = self.parametros_calculo.get('max_iteraciones', 100)
        iteracion = 0
        
        while iteracion < max_iteraciones:
            iteracion += 1
            self._log(f"\n--- Iteración {iteracion} ---")
            self._log(f"Dimensiones: t={t:.3f}m, a={a:.3f}m, b={b:.3f}m")
            
            # Calcular volumen y peso de fundación
            if tipo_base == 'Rombica':
                V_fund = self._volumen_rombica(a, b, t)
            else:  # Cuadrada
                V_fund = a * b * t
            
            G_fund = V_fund * gamma_hor
            self._log(f"Volumen fundación: {V_fund:.3f} m³")
            self._log(f"Peso fundación: {G_fund:.0f} kg")
            
            # Peso total
            G_total = Gp + G_fund
            
            # Calcular momentos estabilizantes y volcantes
            Ms = G_total * (a/2)  # Momento estabilizante
            Mb = Ft * (he + t)    # Momento volcante transversal
            Ml = Fl * (he + t)    # Momento volcante longitudinal
            
            # Factores de seguridad
            FSt = Ms / Mb if Mb > 0 else float('inf')  # Transversal
            FSl = Ms / Ml if Ml > 0 else float('inf')  # Longitudinal
            
            self._log(f"Factor seguridad transversal: {FSt:.3f}")
            self._log(f"Factor seguridad longitudinal: {FSl:.3f}")
            
            # Verificar inclinaciones (corregir fórmula)
            # La inclinación se calcula como desplazamiento horizontal / profundidad
            if G_total > 0:
                # Fuerza de fricción disponible
                F_friccion = G_total * mu
                # Desplazamiento por deslizamiento
                x_t = max(0, (Ft - F_friccion) / (gamma_tierra * a * b)) if Ft > F_friccion else 0
                x_l = max(0, (Fl - F_friccion) / (gamma_tierra * a * b)) if Fl > F_friccion else 0
            else:
                x_t = x_l = 0
            
            tg_alfa_t = x_t / t if t > 0 else 0
            tg_alfa_l = x_l / t if t > 0 else 0
            
            # Verificar presiones
            sigma_max = self._calcular_presion_maxima(G_total, Ft, Fl, a, b, t)
            rel_presion = sigma_max / sigma_adm
            
            # Verificar relación t/he
            rel_t_he = t / he
            
            # Verificaciones
            verif_FSt = FSt >= FS_req
            verif_FSl = FSl >= FS_req
            verif_incl_t = tg_alfa_t <= tg_alfa_adm
            verif_incl_l = tg_alfa_l <= tg_alfa_adm
            verif_presion = rel_presion <= self.parametros_calculo['sigma_max_adm']
            verif_t_he = rel_t_he <= self.parametros_calculo['t_he_max']
            
            self._log(f"Verificaciones:")
            self._log(f"  FS transversal: {verif_FSt}")
            self._log(f"  FS longitudinal: {verif_FSl}")
            self._log(f"  Inclinación transversal: {verif_incl_t}")
            self._log(f"  Inclinación longitudinal: {verif_incl_l}")
            self._log(f"  Presión: {verif_presion}")
            self._log(f"  Relación t/he: {verif_t_he}")
            
            # Si todas las verificaciones pasan, terminar
            if all([verif_FSt, verif_FSl, verif_incl_t, verif_incl_l, verif_presion, verif_t_he]):
                self._log(f"\nTODAS LAS VERIFICACIONES CUMPLEN")
                break
            
            # Ajustar dimensiones según criterio del Excel
            if not verif_FSt or not verif_FSl:
                t_max = self.parametros_calculo.get('t_max', 3.0)
                if t < t_max:
                    t += self.parametros_calculo['incremento']
                    self._log(f"Incrementando profundidad t")
                else:
                    a += self.parametros_calculo['incremento']
                    b += self.parametros_calculo['incremento']
                    self._log(f"Incrementando dimensiones a y b")
            elif not verif_presion:
                a += self.parametros_calculo['incremento']
                b += self.parametros_calculo['incremento']
                self._log(f"Incrementando dimensiones por presión")
            elif not verif_incl_t or not verif_incl_l:
                # Si solo fallan las inclinaciones, incrementar dimensiones base
                a += self.parametros_calculo['incremento']
                b += self.parametros_calculo['incremento']
                self._log(f"Incrementando dimensiones por inclinación")
            else:
                # Si no se puede mejorar más, salir
                self._log(f"No se puede mejorar más, terminando")
                break
        
        # Guardar resultados finales
        self.resultados = {
            'a': a,
            'b': b,
            't': t,
            'volumen': V_fund,
            'FSt': FSt,
            'FSl': FSl,
            'tg_alfa_t': tg_alfa_t,
            'tg_alfa_l': tg_alfa_l,
            'rel_presion': rel_presion,
            'rel_t_he': rel_t_he,
            'iteraciones': iteracion
        }
        
        self.verificaciones = {
            'FSt': verif_FSt,
            'FSl': verif_FSl,
            'inclinacion_t': verif_incl_t,
            'inclinacion_l': verif_incl_l,
            'presion': verif_presion,
            't_he': verif_t_he
        }
        
        return self.resultados
    
    def _volumen_rombica(self, a, b, t):
        """Calcular volumen de base rómbica"""
        # Fórmula correcta para base rómbica: V = (a * b * t) / 2
        # Para base rómbica real, usar factor de forma
        factor_rombica = self.parametros_calculo.get('factor_rombica', 0.5)
        return a * b * t * factor_rombica
    
    def _calcular_presion_maxima(self, G_total, Ft, Fl, a, b, t):
        """Calcular presión máxima en el suelo"""
        if G_total <= 0:
            return 0
        
        area = a * b
        sigma_media = G_total / area
        
        # Momentos por fuerzas horizontales
        M_t = Ft * (self.parametros_estructura.get('he', 0) + t)
        M_l = Fl * (self.parametros_estructura.get('he', 0) + t)
        
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
    
    def obtener_dataframe_resultados(self):
        """Generar DataFrame con resultados"""
        if not self.resultados:
            return pd.DataFrame()
        
        data = []
        for key, value in self.resultados.items():
            verificacion = ""
            if key in ['FSt', 'FSl']:
                key_verif = 'FSt' if key == 'FSt' else 'FSl'
                verificacion = "Verifica" if self.verificaciones.get(key_verif, False) else "No Verifica"
            elif 'tg_alfa' in key:
                verificacion = "Verifica" if self.verificaciones.get('inclinacion_' + key[-1], False) else "No Verifica"
            elif key == 'rel_presion':
                verificacion = "Verifica" if self.verificaciones.get('presion', False) else "No Verifica"
            elif key == 'rel_t_he':
                verificacion = "Verifica" if self.verificaciones.get('t_he', False) else "No Verifica"
            
            data.append({
                'Parámetro': key,
                'Valor': f"{value:.4f}" if isinstance(value, float) else str(value),
                'Verificación': verificacion
            })
        
        return pd.DataFrame(data)
    
    def obtener_memoria_calculo(self):
        """Obtener memoria de cálculo como string"""
        return "\n".join(self.memoria_calculo)