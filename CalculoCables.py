### 001 CLASES CABLE_AEA, ELEMENTO_AEA
import pandas as pd
import numpy as np
import math

class Cable_AEA:
    """
    Clase para representar cables según norma AEA 95301-2007
    con capacidades de cálculo mecánico extendidos
    """
    
    # Parámetros por exposición según Tabla 10.2-h AEA (los mismos que para cables)
    EXPOSICIONES = {
        "B": {"alpha": 4.5, "k": 0.01,  "Ls": 52,  "Zs": 366},
        "C": {"alpha": 7.5, "k": 0.005, "Ls": 67,  "Zs": 274},
        "D": {"alpha": 10,  "k": 0.003, "Ls": 76,  "Zs": 213},
    }
    
    # Clases de línea según tensión (factor de carga Fc) - Tabla 10.2-b
    CLASES_LINEA = {
        "B":  {"Fc": 0.93, "Vmin": 1,   "Vmax": 66},
        "BB": {"Fc": 1.00, "Vmin": 1,   "Vmax": 38},
        "C":  {"Fc": 1.15, "Vmin": 66,  "Vmax": 220},
        "D":  {"Fc": 1.30, "Vmin": 220, "Vmax": 800},
        "E":  {"Fc": 1.40, "Vmin": 800, "Vmax": 9999},
    }
    
    def __init__(self, id_cable, nombre, propiedades, 
                 viento_base_params=None):
        """
        Inicializa un objeto cable con parámetros de viento base OBLIGATORIOS
        
        Args:
            id_cable (str): Identificador único del cable
            nombre (str): Nombre descriptivo del cable
            propiedades (dict): Diccionario con propiedades mecánicas y geométricas
            viento_base_params (dict): Parámetros base de viento para cache (OBLIGATORIO)
        """
        self.id = id_cable
        self.nombre = nombre
        self.propiedades = propiedades
        
        # Propiedades básicas
        self.diametro_m = propiedades["diametro_total_mm"] / 1000.0
        self.seccion_mm2 = propiedades["seccion_total_mm2"]
        self.peso_unitario_dan_m = propiedades["peso_unitario_dan_m"]
        self.carga_rotura_dan = propiedades["carga_rotura_minima_dan"]
        self.modulo_elasticidad_dan_mm2 = propiedades["modulo_elasticidad_dan_mm2"]
        self.coeficiente_dilatacion = propiedades["coeficiente_dilatacion_1_c"]
        
        # Cache de cálculos de viento base (OBLIGATORIO)
        if viento_base_params is None:
            raise ValueError("ERROR: No se pudo crear objeto cable, faltan parámetros iniciales de viento base.")
        
        self.viento_base_params = viento_base_params
        self.viento_cache = {}
        
        # Calcular cache de vientos
        self._calcular_cache_vientos(viento_base_params)
    
    def _calcular_cache_vientos(self, params):
        """
        Calcula y cachea las 6 combinaciones de viento base para este cable
        
        Args:
            params (dict): Parámetros base de viento que incluyen:
                - V (float): Velocidad base del viento
                - t_hielo (float): Espesor de hielo
                - exp (str): Exposición
                - clase (str): Clase de línea
                - Zc (float): Altura efectiva
                - Cf (float): Coeficiente de fuerza
                - L_vano (float): Longitud de vano
        """
        V = params.get('V')
        t_hielo = params.get('t_hielo', 0)
        exp = params.get('exp', 'C')
        clase = params.get('clase', 'B')
        Zc = params.get('Zc')
        Cf = params.get('Cf')
        L_vano = params.get('L_vano')
        
        # Validar parámetros requeridos
        if V is None or Zc is None or Cf is None or L_vano is None:
            raise ValueError(f"ERROR: Faltan parámetros de viento base requeridos en {self.nombre}")
        
        # Diámetros
        d_base = self.diametro_m
        d_hielo = self.diametro_equivalente(t_hielo)
        
        # Combinaciones a calcular
        combinaciones = [
            ('V_90', V, 90, d_base, 'Viento máximo a 90°'),
            ('V_45', V, 45, d_base, 'Viento máximo a 45°'),
            ('V_0', V, 0, d_base, 'Viento máximo a 0°'),
            ('Vmed_90', V * 0.4, 90, d_hielo, 'Viento medio a 90°'),
            ('Vmed_45', V * 0.4, 45, d_hielo, 'Viento medio a 45°'),
            ('Vmed_0', V * 0.4, 0, d_hielo, 'Viento medio a 0°')
        ]
        
        # Calcular y cachear cada combinación
        for clave, velocidad, angulo, diametro, descripcion in combinaciones:
            try:
                resultado = self.cargaViento(
                    V=velocidad,
                    phi_rel_deg=angulo,
                    exp=exp,
                    clase=clase,
                    Zc=Zc,
                    Cf=Cf,
                    L_vano=L_vano,
                    d_eff=diametro
                )
                
                # Guardar en cache
                self.viento_cache[clave] = {
                    'fuerza_daN_per_m': resultado['fuerza_daN_per_m'],
                    'fuerza_total_daN': resultado['fuerza_daN_per_m'] * L_vano,
                    'velocidad': velocidad,
                    'angulo': angulo,
                    'diametro': diametro,
                    'descripcion': descripcion
                }
                
            except Exception as e:
                print(f"⚠️ Error calculando viento base {clave}: {e}")
                self.viento_cache[clave] = None
        
    def __str__(self):
        """Representación en string del cable"""
        return f"Cable {self.id}: {self.nombre} - Ø{self.diametro_m*1000:.1f}mm"
    
    def __repr__(self):
        """Representación para debugging"""
        return f"CABLE_AEA('{self.id}', '{self.nombre}', propiedades)"
    
    def diametro_equivalente(self, espesor_hielo_m=0):
        """
        Calcula el diámetro efectivo con manguito de hielo
        
        Args:
            espesor_hielo_m (float): Espesor del manguito de hielo en metros
            
        Returns:
            float: Diámetro equivalente en metros
        """
        return self.diametro_m + 2.0 * espesor_hielo_m
    
    def cargaPeso(self, espesor_hielo_m=None, densidad_hielo_kg_m3=900):
        """
        Calcula la carga por peso del cable, opcionalmente con hielo
        
        Args:
            espesor_hielo_m (float, optional): Espesor de hielo en metros
            densidad_hielo_kg_m3 (float): Densidad del hielo en kg/m³ (default 900)
                
        Returns:
            float: Carga de peso total (cable + hielo) en daN/m
        """
        peso_hielo = self._calcular_peso_hielo(espesor_hielo_m, densidad_hielo_kg_m3)
        return self.peso_unitario_dan_m + peso_hielo
    
    def _calcular_peso_hielo(self, espesor_hielo_m, densidad_hielo_kg_m3=900):
        """Calcula el peso del manguito de hielo"""
        if espesor_hielo_m is None or espesor_hielo_m <= 0:
            return 0.0
        
        r_int = self.diametro_m / 2
        r_ext = r_int + espesor_hielo_m
        area_corona = math.pi * (r_ext**2 - r_int**2)
        
        peso_hielo_dan_m = (densidad_hielo_kg_m3 * 9.81 * area_corona) / 10.0
        
        return peso_hielo_dan_m
    
    def _factor_Zp(self, Z, Zs, alpha_expo):
        """Calcula Zp según AEA 95301 (método interno)"""
        return 1.61 * (Z / Zs)**(1/alpha_expo)
    
    def _factor_Gw(self, Z, alpha_expo, k, Ls, L_vano):
        """
        Gw para cables (método interno)
        Bw = 1 / (1 + 0.8 * (L_vano / Ls))  
        """
        E = 4.9 * math.sqrt(k) * (10 / Z)**(1/alpha_expo)
        Bw = 1 / (1 + 0.8 * (L_vano / Ls))
        kv = 1.425  
        Gw = (1 + 2.7 * E * math.sqrt(Bw)) / (kv**2)
        return Gw, E, Bw
    
    def _factor_Gt(self, Z, alpha_expo, k, Ls):
        """Gt para estructuras y cadenas (método interno)"""
        E = 4.9 * math.sqrt(k) * (10 / Z)**(1/alpha_expo)
        Bt = 1 / (1 + 0.375 * (Z / Ls))
        Gt = 1 + 2.7 * E * math.sqrt(Bt)
        kv = 1.425
        Gt = Gt / (kv**2)
        return Gt, E, Bt
    
    def cargaViento(self, V=None, phi_rel_deg=90, exp="C", clase="B", Q=0.613, 
                   Zc=10.0, Cf=1.0, L_vano=150.0, d_eff=None, tipo="cable"):
        """
        Calcula la carga de viento sobre el cable según AEA 95301
        
        Args:
            V (float): Velocidad del viento en m/s (OBLIGATORIO)
            phi_rel_deg (float): Ángulo entre viento y eje del conductor en grados
            exp (str): Tipo de exposición ("B", "C", "D")
            clase (str): Clase de línea ("B", "BB", "C", "D", "E")
            Q (float): Presión dinámica de referencia
            Zc (float): Altura efectiva del cable en metros
            Cf (float): Coeficiente de fuerza
            L_vano (float): Longitud del vano en metros
            d_eff (float, optional): Diámetro efectivo con hielo en metros
            tipo (str): Tipo de elemento ("cable" o "estructura")
            
        Returns:
            dict: Diccionario con resultados detallados
        """
        # Validación: V es obligatorio
        if V is None:
            raise ValueError("ERROR: Velocidad del viento (V) es requerida para calcular carga de viento.")
        
        # Resto del método (sin cambios)...
        # Validaciones
        if exp not in self.EXPOSICIONES:
            raise ValueError(f"Exposición '{exp}' no válida. Use: {list(self.EXPOSICIONES.keys())}")
        if clase not in self.CLASES_LINEA:
            raise ValueError(f"Clase '{clase}' no válida. Use: {list(self.CLASES_LINEA.keys())}")
        
        # Obtener parámetros de exposición y clase
        expo = self.EXPOSICIONES[exp]
        alpha_expo = expo["alpha"]
        k = expo["k"]
        Ls = expo["Ls"]
        Zs = expo["Zs"]
        Fc = self.CLASES_LINEA[clase]["Fc"]
        
        # Diámetro efectivo
        if d_eff is None:
            d_eff = self.diametro_m
        
        # Factor Zp
        Zp = self._factor_Zp(Zc, Zs, alpha_expo)
        
        # Factor G según tipo de elemento
        if tipo == "cable":
            G, E, B = self._factor_Gw(Zc, alpha_expo, k, Ls, L_vano)
            ang_factor = math.sin(math.radians(phi_rel_deg))
        else:
            G, E, B = self._factor_Gt(Zc, alpha_expo, k, Ls)
            ang_factor = math.cos(math.radians(phi_rel_deg))
        
        # Cálculo de la fuerza unitaria (N/m)
        Fu_N_per_m = Q * (Zp * V)**2 * Fc * G * Cf * d_eff * ang_factor
        
        # Convertir a daN/m
        Fu_daN_per_m = Fu_N_per_m * 0.1
        
        return {
            "cable_id": self.id,
            "cable_nombre": self.nombre,
            "fuerza_daN_per_m": Fu_daN_per_m,
            "fuerza_N_per_m": Fu_N_per_m,
            "Zp": Zp,
            "G": G,
            "E": E,
            "B": B,
            "Fc": Fc,
            "angulo_factor": ang_factor,
            "phi_rel_grados": phi_rel_deg,
            "diametro_efectivo_m": d_eff,
            "exposicion": exp,
            "clase_linea": clase
        }
    
    def info_completa(self):
        """Devuelve información completa del cable"""
        info = {
            "ID": self.id,
            "Nombre": self.nombre,
            "Diámetro (mm)": self.diametro_m * 1000,
            "Sección (mm²)": self.seccion_mm2,
            "Peso unitario (daN/m)": self.peso_unitario_dan_m,
            "Carga rotura (daN)": self.carga_rotura_dan,
            "Módulo elasticidad (daN/mm²)": self.modulo_elasticidad_dan_mm2,
            "Coef. dilatación (1/°C)": self.coeficiente_dilatacion,
            "Material": self.propiedades.get("material", "No especificado")
        }
        return info
    
    def _resolver_ecuacion_cubica(self, A, B, semilla=100, tol=1e-8, max_iter=1000):
        """Resuelve ecuación cúbica t³ + A·t² + B = 0 usando Newton-Raphson"""
        t = semilla if semilla > 0 else 1.0
        
        for i in range(max_iter):
            f = t**3 + A * t**2 + B
            f_prime = 3 * t**2 + 2 * A * t
            
            if abs(f_prime) < 1e-12:
                # Usar método de bisección si la derivada es muy pequeña
                if f > 0:
                    t = t * 0.9
                else:
                    t = t * 1.1
                continue
                
            t_new = t - f / f_prime
            
            # Evitar valores negativos o cero
            if t_new <= 0:
                t_new = t * 0.5
                
            if abs(t_new - t) < tol:
                return max(t_new, 0.1)
            
            t = t_new
        
        # Si no converge, devolver el último valor (pero positivo)
        return max(t, 0.1)
    
    def _calcular_estado(self, vano, estado_data, t0, q0, parametros_viento):
        """Calcula tensiones y flechas para un estado climático específico dado un estado básico"""
        # Obtener parámetros del estado
        q = estado_data["temperatura"]
        viento_velocidad = estado_data.get("viento_velocidad", 0)
        espesor_hielo = estado_data.get("espesor_hielo", 0)
        
        # Calcular cargas
        peso_total = self.cargaPeso(espesor_hielo_m=espesor_hielo, densidad_hielo_kg_m3=900)
        peso_hielo = self._calcular_peso_hielo(espesor_hielo, 900)
        
        # Calcular viento si hay velocidad
        if viento_velocidad > 0:
            resultado_viento = self.cargaViento(
                V=viento_velocidad,
                phi_rel_deg=90,
                exp=parametros_viento.get("exposicion", "C"),
                clase=parametros_viento.get("clase", "B"),
                Zc=parametros_viento.get("Zc", 10.0),
                Cf=parametros_viento.get("Cf", 1.0),
                L_vano=vano,
                d_eff=self.diametro_equivalente(espesor_hielo)
            )
            carga_viento = resultado_viento["fuerza_daN_per_m"]
        else:
            carga_viento = 0
        
        # Carga vectorial total
        G = math.sqrt(peso_total**2 + carga_viento**2)
        
        # Parámetros del cable
        E = self.modulo_elasticidad_dan_mm2  # daN/mm²
        S = self.seccion_mm2  # mm²
        alfa = self.coeficiente_dilatacion  # 1/°C
        
        # Coeficientes de la ecuación cúbica (t³ + A·t² + B = 0)
        # En daN/mm², usando unidades consistentes
        L = vano
        
        # Calcular Go (carga del estado básico)
        # Para el estado básico, usar las condiciones iniciales
        espesor_hielo_0 = 0  # Asumimos que el estado básico es sin hielo
        peso_total_0 = self.cargaPeso(espesor_hielo_m=espesor_hielo_0)
        viento_velocidad_0 = 0  # Asumimos que el estado básico es sin viento
        carga_viento_0 = 0
        Go = math.sqrt(peso_total_0**2 + carga_viento_0**2)
        
        # Coeficiente A (corregido con unidades consistentes)
        A = (L**2 * E * Go**2) / (24 * t0**2 * S**2) + alfa * E * (q - q0) - t0
        
        # Coeficiente B (corregido con unidades consistentes)
        B = -(L**2 * E * G**2) / (24 * S**2)
        
        # Resolver ecuación cúbica para obtener tensión en daN/mm²
        t_estado = self._resolver_ecuacion_cubica(A, B, semilla=t0)
        
        # Calcular tiro (T = t * S)
        T_estado = t_estado * S
        
        # Calcular flechas
        flecha_vertical = (peso_total * L**2) / (8 * T_estado) if T_estado > 0 else float('nan')
        flecha_resultante = (G * L**2) / (8 * T_estado) if T_estado > 0 else float('nan')
        
        # Calcular porcentaje de rotura
        porcentaje_rotura = (T_estado / self.carga_rotura_dan) * 100 if self.carga_rotura_dan > 0 else float('nan')
        
        return {
            "tension_daN_mm2": t_estado,
            "tiro_daN": T_estado,
            "flecha_vertical_m": flecha_vertical,
            "flecha_resultante_m": flecha_resultante,
            "temperatura_C": q,
            "carga_unitaria_daN_m": G,
            "descripcion": estado_data["descripcion"],
            "porcentaje_rotura": porcentaje_rotura,
            "espesor_hielo_cm": espesor_hielo * 100,
            "viento_velocidad": viento_velocidad,
            "carga_viento_daN_m": carga_viento,
            "peso_total_daN_m": peso_total,
            "peso_hielo_daN_m": peso_hielo
        }
    
    def _calcular_tensiones_estado_basico(self, vano, estados_climaticos, t0, q0, parametros_viento):
        """Calcula tensiones para todos los estados climáticos dado un estado básico"""
        resultados = {}
        
        for estado_id, estado_data in estados_climaticos.items():
            resultados[estado_id] = self._calcular_estado(vano, estado_data, t0, q0, parametros_viento)
        
        return resultados
    
    def _encontrar_estado_max_tension(self, resultados):
        """Encuentra el estado con máxima tensión"""
        estado_max = None
        t_max = 0
        
        for estado_id, datos in resultados.items():
            t_actual = datos["tension_daN_mm2"]
            if t_actual > t_max:
                t_max = t_actual
                estado_max = estado_id
        
        return estado_max, t_max
    
    def _verificar_restricciones(self, resultados, restricciones_cable, resultados_conductor=None, 
                               es_guardia=False, relflecha_sin_viento=True, flecha_max_permitida=None,
                               objetivo='FlechaMin', tolerancia_relflecha=0.01):
        """Verifica si se cumplen todas las restricciones"""
        carga_rotura = self.carga_rotura_dan
        estado_violador = None
        tipo_violacion = None
        factor_severidad = 0
        
        for estado_id, datos in resultados.items():
            # Para TiroMin: IGNORAR restricciones de tensión máxima
            if objetivo != 'TiroMin':
                # Verificar tensión máxima solo si no es TiroMin
                tension_max_porcentaje = restricciones_cable.get("tension_max_porcentaje", {}).get(
                    estado_id, 0.40
                )
                T_actual = datos["tiro_daN"]
                T_max_permitida = tension_max_porcentaje * carga_rotura
                
                if T_actual > T_max_permitida:
                    severidad = (T_actual - T_max_permitida) / T_max_permitida
                    if severidad > factor_severidad:
                        factor_severidad = severidad
                        estado_violador = estado_id
                        tipo_violacion = "tension"
            
            # Para FlechaMin: IGNORAR restricciones de flecha máxima
            # Para TiroMin: CONSIDERAR flecha máxima (a menos que sea 0)
            if objetivo == 'TiroMin' and flecha_max_permitida is not None and flecha_max_permitida > 0:
                flecha_actual = datos["flecha_vertical_m"]
                if flecha_actual > flecha_max_permitida:
                    severidad = (flecha_actual - flecha_max_permitida) / flecha_max_permitida
                    if severidad > factor_severidad:
                        factor_severidad = severidad
                        estado_violador = estado_id
                        tipo_violacion = "flecha"
            
            # Verificar relación de flecha (solo para guardia con TiroMin) - CON TOLERANCIA
            if (es_guardia and objetivo == 'TiroMin' and 
                "relflecha_max" in restricciones_cable and 
                resultados_conductor and estado_id in resultados_conductor):
                
                considerar_estado = True
                if relflecha_sin_viento:
                    considerar_estado = (datos.get("carga_viento_daN_m", 0) == 0)
                
                if considerar_estado:
                    flecha_guardia = datos["flecha_vertical_m"]
                    flecha_conductor = resultados_conductor[estado_id]["flecha_vertical_m"]
                    
                    if flecha_conductor > 0 and not math.isnan(flecha_guardia):
                        relacion_flecha = flecha_guardia / flecha_conductor
                        relflecha_max = restricciones_cable["relflecha_max"]
                        
                        # APLICAR TOLERANCIA: Se acepta si está dentro del rango [relflecha_max - tolerancia, relflecha_max]
                        if relacion_flecha > relflecha_max + tolerancia_relflecha:
                            severidad = (relacion_flecha - relflecha_max) / relflecha_max
                            if severidad > factor_severidad:
                                factor_severidad = severidad
                                estado_violador = estado_id
                                tipo_violacion = "relflecha"
        
        return estado_violador, tipo_violacion
    
    def _iterar_estado_basico(self, vano, estados_climaticos, t0_inicial, q0_inicial, parametros_viento, max_iter=10, tol=1e-3):
        """
        ITERA para encontrar el estado básico correcto (estado de máxima tensión)
        SIGUE EXACTAMENTE EL PROCESO DESCRITO: estado básico 1, recalcular, encontrar estado básico 2
        """
        # 1. Estado básico 1: usar el primer estado climático como estado básico inicial
        estado_basico_1_id = list(estados_climaticos.keys())[0]
        q0_basico_1 = estados_climaticos[estado_basico_1_id]["temperatura"]
        t0_basico_1 = t0_inicial
        
        # 2. Calcular todos los estados con estado básico 1
        resultados_1 = self._calcular_tensiones_estado_basico(
            vano, estados_climaticos, t0_basico_1, q0_basico_1, parametros_viento
        )
        
        # 3. Encontrar estado con máxima tensión (posible estado básico 2)
        estado_max_tension_id, t_max = self._encontrar_estado_max_tension(resultados_1)
        
        # 4. Si el estado de máxima tensión es diferente al estado básico 1, iterar
        iteracion = 0
        estado_basico_actual_id = estado_basico_1_id
        q0_actual = q0_basico_1
        t0_actual = t0_basico_1
        resultados_actuales = resultados_1
        
        while estado_basico_actual_id != estado_max_tension_id and iteracion < max_iter:
            # Actualizar estado básico al de máxima tensión
            estado_basico_actual_id = estado_max_tension_id
            q0_actual = estados_climaticos[estado_basico_actual_id]["temperatura"]
            t0_actual = t_max  # Usar la tensión máxima como nueva t0
            
            # Recalcular todos los estados con el nuevo estado básico
            resultados_actuales = self._calcular_tensiones_estado_basico(
                vano, estados_climaticos, t0_actual, q0_actual, parametros_viento
            )
            
            # Encontrar nuevo estado de máxima tensión
            estado_max_tension_id, t_max = self._encontrar_estado_max_tension(resultados_actuales)
            
            iteracion += 1
        
        return resultados_actuales, t0_actual, q0_actual, estado_basico_actual_id
    
    def _buscar_solucion_incremental(self, vano, estados_climaticos, parametros_viento, restricciones_cable,
                                   resultados_conductor, es_guardia, flecha_max_permitida, relflecha_sin_viento,
                                   objetivo, t_inicial, paso_porcentual, sentido):
        """
        Búsqueda incremental principal según el objetivo
        CONTINÚA HASTA ENCONTRAR UNA VIOLACIÓN O HASTA 10,000 ITERACIONES
        """
        # Convertir paso porcentual a tensión absoluta
        paso_tension = paso_porcentual * (self.carga_rotura_dan / self.seccion_mm2)
        
        # Variables de búsqueda
        t_actual = t_inicial
        t_ultima_valida = None
        resultados_ultimos_validos = None
        estado_limitante = None
        tipo_violacion = None
        
        # Búsqueda iterativa - HASTA 10,000 ITERACIONES
        max_iteraciones = 10000
        iteracion = 0
        
        print(f"  🔍 Iniciando búsqueda incremental: t_inicial={t_actual:.6f} daN/mm², "
              f"paso={paso_tension:.6f}, sentido={'↑' if sentido > 0 else '↓'}, máximo {max_iteraciones} iteraciones")
        
        while iteracion < max_iteraciones:
            # 1. Iterar para encontrar estado básico estable
            resultados, t0_actual, q0_actual, estado_basico = self._iterar_estado_basico(
                vano, estados_climaticos, t_actual, 
                estados_climaticos[list(estados_climaticos.keys())[0]]["temperatura"],
                parametros_viento
            )
            
            # 2. Verificar restricciones
            estado_violador, tipo_violacion = self._verificar_restricciones(
                resultados, restricciones_cable, resultados_conductor, es_guardia,
                relflecha_sin_viento, flecha_max_permitida, objetivo
            )
            
            if estado_violador is None:
                # Restricciones cumplidas - guardar como válido
                t_ultima_valida = t_actual
                resultados_ultimos_validos = resultados
                estado_limitante = None
                
                # Solo mostrar progreso cada 100 iteraciones para no saturar
                if iteracion % 100 == 0:
                    print(f"    ✓ Iteración {iteracion}: t={t_actual:.6f} VÁLIDA")
                
                # Continuar buscando en el sentido indicado
                t_actual += sentido * paso_tension
                
                # Verificar límites físicos
                if t_actual <= 0:
                    print(f"    ⚠️  Límite mínimo alcanzado: t={t_actual:.6f}")
                    estado_limitante = "Límite mínimo físico"
                    break
                    
                # Para FlechaMin, verificar límite máximo
                if sentido > 0 and t_actual * self.seccion_mm2 >= self.carga_rotura_dan * 0.95:
                    print(f"    ⚠️  Límite máximo alcanzado: t={t_actual:.6f} (95% de rotura)")
                    estado_limitante = "Límite máximo físico"
                    break
            else:
                # Restricción violada - DETENER BÚSQUEDA
                estado_limitante = estado_violador
                print(f"    ✗ Iteración {iteracion}: t={t_actual:.6f} VIOLADA por {tipo_violacion} en estado {estado_limitante}")
                break
            
            iteracion += 1
        
        if iteracion >= max_iteraciones:
            print(f"    ⚠️  Se alcanzó el máximo de {max_iteraciones} iteraciones sin encontrar violación")
        
        return t_ultima_valida, resultados_ultimos_validos, estado_limitante, tipo_violacion
    
    def _ajuste_fino_triple_corregido(self, t_valida, t_violadora, vano, estados_climaticos, parametros_viento,
                                    restricciones_cable, resultados_conductor, es_guardia, flecha_max_permitida,
                                    relflecha_sin_viento, objetivo):
        """
        AJUSTE FINO TRIPLE CORREGIDO según la descripción:
        1. Fase 1 (1%): Desde t_valida con saltos de 1% hasta encontrar violación → retrocede 1%
        2. Fase 2 (0.1%): Desde el punto anterior con saltos de 0.1% hasta encontrar violación → retrocede 0.1%
        3. Fase 3 (0.01%): Desde el punto anterior con saltos de 0.01% hasta encontrar violación
        4. La solución es la última válida de la fase 3 (0.01% antes de la violación)
        """
        print("  🎯 Iniciando ajuste fino triple CORREGIDO")
        
        # Determinar sentido del ajuste
        if t_violadora > t_valida:  # FlechaMin (aumentando tensión)
            sentido = 1
            t_inicio = t_valida
            t_fin = t_violadora
        else:  # TiroMin (disminuyendo tensión)
            sentido = -1
            t_inicio = t_violadora  # Para TiroMin, t_violadora < t_valida
            t_fin = t_valida
        
        print(f"     Rango ajuste: {t_inicio:.6f} a {t_fin:.6f}, sentido={'↑' if sentido > 0 else '↓'}")
        
        # Fase 1: Saltos del 1%
        paso_1porc = 0.01 * (self.carga_rotura_dan / self.seccion_mm2)
        print(f"     Fase 1: Saltos del 1% ({paso_1porc:.6f} daN/mm²)")
        
        t_fase1 = t_inicio
        t_ultima_valida_fase1 = t_inicio
        resultados_fase1 = None
        
        while (sentido > 0 and t_fase1 <= t_fin) or (sentido < 0 and t_fase1 >= t_fin):
            resultados, t0_actual, q0_actual, estado_basico = self._iterar_estado_basico(
                vano, estados_climaticos, t_fase1,
                estados_climaticos[list(estados_climaticos.keys())[0]]["temperatura"],
                parametros_viento
            )
            
            estado_violador, _ = self._verificar_restricciones(
                resultados, restricciones_cable, resultados_conductor, es_guardia,
                relflecha_sin_viento, flecha_max_permitida, objetivo
            )
            
            if estado_violador is None:
                t_ultima_valida_fase1 = t_fase1
                resultados_fase1 = resultados
                t_fase1 += sentido * paso_1porc
            else:
                print(f"       Fase 1: Violación en t={t_fase1:.6f}")
                break
        
        # Retroceder 1% desde la violación
        t_fase1_inicio = t_ultima_valida_fase1 - sentido * paso_1porc
        print(f"       Fase 1 completada: última válida t={t_ultima_valida_fase1:.6f}")
        print(f"       Inicio Fase 2 desde: t={t_fase1_inicio:.6f}")
        
        # Fase 2: Saltos del 0.1%
        paso_01porc = 0.001 * (self.carga_rotura_dan / self.seccion_mm2)
        print(f"     Fase 2: Saltos del 0.1% ({paso_01porc:.6f} daN/mm²)")
        
        t_fase2 = t_fase1_inicio
        t_ultima_valida_fase2 = t_fase1_inicio
        resultados_fase2 = None
        
        # Avanzar hasta encontrar violación
        contador_fase2 = 0
        while contador_fase2 < 100:  # Límite de seguridad
            resultados, t0_actual, q0_actual, estado_basico = self._iterar_estado_basico(
                vano, estados_climaticos, t_fase2,
                estados_climaticos[list(estados_climaticos.keys())[0]]["temperatura"],
                parametros_viento
            )
            
            estado_violador, _ = self._verificar_restricciones(
                resultados, restricciones_cable, resultados_conductor, es_guardia,
                relflecha_sin_viento, flecha_max_permitida, objetivo
            )
            
            if estado_violador is None:
                t_ultima_valida_fase2 = t_fase2
                resultados_fase2 = resultados
                t_fase2 += sentido * paso_01porc
                contador_fase2 += 1
            else:
                print(f"       Fase 2: Violación en t={t_fase2:.6f}")
                break
        
        # Retroceder 0.1% desde la violación
        t_fase2_inicio = t_ultima_valida_fase2 - sentido * paso_01porc
        print(f"       Fase 2 completada: última válida t={t_ultima_valida_fase2:.6f}")
        print(f"       Inicio Fase 3 desde: t={t_fase2_inicio:.6f}")
        
        # Fase 3: Saltos del 0.01%
        paso_001porc = 0.0001 * (self.carga_rotura_dan / self.seccion_mm2)
        print(f"     Fase 3: Saltos del 0.01% ({paso_001porc:.6f} daN/mm²)")
        
        t_fase3 = t_fase2_inicio
        t_ultima_valida_fase3 = t_fase2_inicio
        resultados_fase3 = None
        
        # Avanzar hasta encontrar violación
        contador_fase3 = 0
        while contador_fase3 < 100:  # Límite de seguridad
            resultados, t0_actual, q0_actual, estado_basico = self._iterar_estado_basico(
                vano, estados_climaticos, t_fase3,
                estados_climaticos[list(estados_climaticos.keys())[0]]["temperatura"],
                parametros_viento
            )
            
            estado_violador, _ = self._verificar_restricciones(
                resultados, restricciones_cable, resultados_conductor, es_guardia,
                relflecha_sin_viento, flecha_max_permitida, objetivo
            )
            
            if estado_violador is None:
                t_ultima_valida_fase3 = t_fase3
                resultados_fase3 = resultados
                t_fase3 += sentido * paso_001porc
                contador_fase3 += 1
            else:
                print(f"       Fase 3: Violación en t={t_fase3:.6f}")
                break
        
        print(f"       Fase 3 completada: solución t={t_ultima_valida_fase3:.6f}")
        
        if resultados_fase3 is None:
            print("       ⚠️  No se encontró solución en Fase 3, usando Fase 2")
            return resultados_fase2, t_ultima_valida_fase2
        
        return resultados_fase3, t_ultima_valida_fase3
    
    def _optimizar_flecha_min(self, vano, estados_climaticos, parametros_viento, restricciones_cable,
                            resultados_conductor, es_guardia, flecha_max_permitida, relflecha_sin_viento):
        """
        Optimización para objetivo FlechaMin - CORREGIDO
        """
        print("  🎯 Objetivo: FlechaMin (minimizar flecha, aumentar tensión)")
        
        # 1. Tensión inicial: 1% de la rotura
        t_inicial = 0.01 * self.carga_rotura_dan / self.seccion_mm2
        print(f"  📈 Tensión inicial: {t_inicial:.6f} daN/mm² (1% de rotura)")
        
        # 2. Paso inicial: 1% de la rotura
        paso_inicial = 0.01
        sentido = 1  # Aumentar tensión para minimizar flecha
        
        # 3. Búsqueda principal incremental (hasta encontrar violación o 10,000 iteraciones)
        t_valida, resultados_validos, estado_limitante, tipo_violacion = self._buscar_solucion_incremental(
            vano, estados_climaticos, parametros_viento, restricciones_cable,
            resultados_conductor, es_guardia, flecha_max_permitida, relflecha_sin_viento,
            'FlechaMin', t_inicial, paso_inicial, sentido
        )
        
        q0 = estados_climaticos[list(estados_climaticos.keys())[0]]["temperatura"]
        
        if t_valida is None:
            print("  ❌ No se encontró ninguna solución válida")
            return self._resultados_nan(estados_climaticos), float('nan'), q0, estado_limitante
        
        # 5. Si se encontró una violación, hacer ajuste fino
        if estado_limitante is not None and tipo_violacion is not None:
            print(f"  🔄 Restricción violada en la búsqueda principal")
            print(f"     Última válida: t={t_valida:.6f}, violación por {tipo_violacion} en {estado_limitante}")
            
            # t_valida es la última tensión válida, t_violadora es t_valida + paso_inicial
            t_violadora = t_valida + paso_inicial * (self.carga_rotura_dan / self.seccion_mm2)
            
            # 6. Ajuste fino triple CORREGIDO
            resultados_finales, t_optima = self._ajuste_fino_triple_corregido(
                t_valida, t_violadora, vano, estados_climaticos, parametros_viento,
                restricciones_cable, resultados_conductor, es_guardia, flecha_max_permitida,
                relflecha_sin_viento, 'FlechaMin'
            )
            
            if resultados_finales is None:
                print("  ⚠️  Ajuste fino no encontró solución, usando última válida de búsqueda principal")
                return resultados_validos, t_valida, q0, estado_limitante
            
            print(f"  ✅ Ajuste fino completado: t_optima={t_optima:.6f}")
            return resultados_finales, t_optima, q0, estado_limitante
        elif estado_limitante is not None and tipo_violacion is None:
            # Límite físico alcanzado
            print(f"  ⚠️  Límite físico alcanzado: {estado_limitante}")
            return resultados_validos, t_valida, q0, None
        else:
            # Si no se violó ninguna restricción después de 10,000 iteraciones
            print(f"  ✅ Solución encontrada sin violaciones después de búsqueda exhaustiva: t={t_valida:.6f}")
            return resultados_validos, t_valida, q0, None
    
    def _optimizar_tiro_min(self, vano, estados_climaticos, parametros_viento, restricciones_cable,
                          resultados_conductor, es_guardia, relflecha_sin_viento, flecha_max_permitida):
        """
        Optimización para objetivo TiroMin - CORREGIDO
        """
        print("  🎯 Objetivo: TiroMin (minimizar tiro, disminuir tensión)")
        
        # 1. Tensión inicial: 70% de la rotura
        t_inicial = 0.70 * self.carga_rotura_dan / self.seccion_mm2
        print(f"  📉 Tensión inicial: {t_inicial:.6f} daN/mm² (70% de rotura)")
        
        # 2. Paso inicial: 1% de la rotura
        paso_inicial = 0.01
        sentido = -1  # Disminuir tensión para minimizar tiro
        
        # 3. Búsqueda principal incremental (hasta encontrar violación o 10,000 iteraciones)
        t_valida, resultados_validos, estado_limitante, tipo_violacion = self._buscar_solucion_incremental(
            vano, estados_climaticos, parametros_viento, restricciones_cable,
            resultados_conductor, es_guardia, flecha_max_permitida, relflecha_sin_viento,
            'TiroMin', t_inicial, paso_inicial, sentido
        )
        
        q0 = estados_climaticos[list(estados_climaticos.keys())[0]]["temperatura"]
        
        if t_valida is None:
            print("  ❌ No se encontró ninguna solución válida")
            return self._resultados_nan(estados_climaticos), float('nan'), q0, estado_limitante
        
        # 5. Si se encontró una violación, hacer ajuste fino
        if estado_limitante is not None and tipo_violacion is not None:
            print(f"  🔄 Restricción violada en la búsqueda principal")
            print(f"     Última válida: t={t_valida:.6f}, violación por {tipo_violacion} en {estado_limitante}")
            
            # t_valida es la última tensión válida, t_violadora es t_valida - paso_inicial
            t_violadora = t_valida - paso_inicial * (self.carga_rotura_dan / self.seccion_mm2)
            
            # 6. Ajuste fino triple CORREGIDO
            resultados_finales, t_optima = self._ajuste_fino_triple_corregido(
                t_valida, t_violadora, vano, estados_climaticos, parametros_viento,
                restricciones_cable, resultados_conductor, es_guardia, flecha_max_permitida,
                relflecha_sin_viento, 'TiroMin'
            )
            
            if resultados_finales is None:
                print("  ⚠️  Ajuste fino no encontró solución, usando última válida de búsqueda principal")
                return resultados_validos, t_valida, q0, estado_limitante
            
            print(f"  ✅ Ajuste fino completado: t_optima={t_optima:.6f}")
            return resultados_finales, t_optima, q0, estado_limitante
        elif estado_limitante is not None and tipo_violacion is None:
            # Límite físico alcanzado
            print(f"  ⚠️  Límite físico alcanzado: {estado_limitante}")
            return resultados_validos, t_valida, q0, None
        else:
            # Si no se violó ninguna restricción después de 10,000 iteraciones
            print(f"  ✅ Solución encontrada sin violaciones después de búsqueda exhaustiva: t={t_valida:.6f}")
            return resultados_validos, t_valida, q0, None
    
    def _resultados_nan(self, estados_climaticos):
        """Crea un diccionario de resultados con NaN para todos los valores numéricos"""
        resultados_nan = {}
        for estado_id, estado_data in estados_climaticos.items():
            resultados_nan[estado_id] = {
                "tension_daN_mm2": float('nan'),
                "tiro_daN": float('nan'),
                "flecha_vertical_m": float('nan'),
                "flecha_resultante_m": float('nan'),
                "temperatura_C": estado_data["temperatura"],
                "carga_unitaria_daN_m": float('nan'),
                "descripcion": estado_data["descripcion"],
                "porcentaje_rotura": float('nan'),
                "espesor_hielo_cm": estado_data.get("espesor_hielo", 0) * 100,
                "viento_velocidad": estado_data.get("viento_velocidad", 0),
                "carga_viento_daN_m": float('nan'),
                "peso_total_daN_m": float('nan'),
                "peso_hielo_daN_m": float('nan')
            }
        return resultados_nan
    
    def calculo_mecanico(self, vano, estados_climaticos, parametros_viento, 
                        restricciones=None, objetivo='FlechaMin', es_guardia=False,
                        resultados_conductor=None, flecha_max_permitida=None,
                        relflecha_sin_viento=True, **kwargs):
        """
        Realiza el cálculo mecánico completo del cable
        
        Args:
            **kwargs: Parámetros adicionales para compatibilidad
                      (salto_porcentual, paso_afinado, etc.) - SE IGNORAN, se usan los valores fijos
        """
        print(f"\n🔧 Cálculo mecánico para {self.nombre} ({'Guardia' if es_guardia else 'Conductor'})")
        print(f"   Objetivo: {objetivo}, Vano: {vano} m")
        
        # Mostrar advertencia si hay parámetros no usados (se usan valores fijos)
        if kwargs:
            print(f"   ⚠️  Parámetros ignorados (se usan valores fijos del algoritmo): {list(kwargs.keys())}")
        
        # Restricciones por defecto
        if restricciones is None:
            restricciones = {"tension_max_porcentaje": {}}
            for estado_id in estados_climaticos.keys():
                restricciones["tension_max_porcentaje"][estado_id] = 0.40
        
        # Para guardia, agregar restricción de relación de flecha si no existe
        if es_guardia and "relflecha_max" not in restricciones:
            restricciones["relflecha_max"] = 0.9
        
        # Para guardia con TiroMin, calcular flecha máxima basada en relación con conductor
        if (es_guardia and objetivo == 'TiroMin' and resultados_conductor and 
            (flecha_max_permitida is None or flecha_max_permitida == 0)):
            max_flecha_conductor = 0
            for estado_id, res_cond in resultados_conductor.items():
                if relflecha_sin_viento:
                    if res_cond.get('carga_viento_daN_m', 0) == 0:
                        max_flecha_conductor = max(max_flecha_conductor, res_cond['flecha_vertical_m'])
                else:
                    max_flecha_conductor = max(max_flecha_conductor, res_cond['flecha_vertical_m'])
            
            flecha_max_permitida = max_flecha_conductor * restricciones.get("relflecha_max", 0.9)
            print(f"   📏 Flecha máxima permitida para guardia: {flecha_max_permitida:.2f} m (basada en relación {restricciones.get('relflecha_max', 0.9)}:1)")
        
        # Optimizar según el objetivo
        if objetivo == 'FlechaMin':
            resultados_final, t_final, q0_final, estado_limitante = self._optimizar_flecha_min(
                vano, estados_climaticos, parametros_viento, restricciones,
                resultados_conductor, es_guardia, flecha_max_permitida,
                relflecha_sin_viento
            )
        else:  # 'TiroMin'
            resultados_final, t_final, q0_final, estado_limitante = self._optimizar_tiro_min(
                vano, estados_climaticos, parametros_viento, restricciones,
                resultados_conductor, es_guardia, relflecha_sin_viento, flecha_max_permitida
            )
        
        # VERIFICACIÓN CRÍTICA: asegurar que resultados_final no sea None
        if resultados_final is None:
            print("  ❗ ERROR: resultados_final es None, usando resultados NaN")
            resultados_final = self._resultados_nan(estados_climaticos)
        
        # Construir DataFrame de resultados
        tabla_data = []

        for estado_id, res in resultados_final.items():
            estado_data = estados_climaticos[estado_id]
            
            # Marcar estado determinante
            estado_determinante = '🟡' if estado_id == estado_limitante else ''
            
            # Calcular relación de flecha si es guardia
            if es_guardia and resultados_conductor and estado_id in resultados_conductor:
                flecha_guardia = res['flecha_vertical_m']
                flecha_conductor = resultados_conductor[estado_id]['flecha_vertical_m']
                
                if flecha_conductor > 0 and not math.isnan(flecha_guardia):
                    rel_flecha = flecha_guardia / flecha_conductor
                else:
                    rel_flecha = float('nan')
            else:
                rel_flecha = '-'
            
            tabla_data.append({
                'Cable': 'Guardia' if es_guardia else 'Conductor',
                'Descrip.': estado_data["descripcion"],
                'Temperatura [°C]': res['temperatura_C'],
                'Esp. manguito hielo [cm]': res['espesor_hielo_cm'],
                'Vano Regulador [m]': vano,
                'Carga Peso [daN/m]': self.peso_unitario_dan_m,
                'Carga Hielo [daN/m]': res['peso_hielo_daN_m'],
                'Carga Viento [daN/m]': res['carga_viento_daN_m'],
                'Carga vectorial [daN/m]': res['carga_unitaria_daN_m'],
                'Tensión [daN/mm2]': res['tension_daN_mm2'],
                'Tiro [daN]': res['tiro_daN'],
                'Flecha [m]': res['flecha_resultante_m'],
                'Flecha Vertical [m]': res['flecha_vertical_m'],
                '% rotura': res['porcentaje_rotura'],
                'Estado determinante': estado_determinante,
                'Rel. flecha': rel_flecha
            })

        df_resultados = pd.DataFrame(tabla_data)

        # Reordenar columnas
        columnas_base = ['Cable', 'Descrip.', 'Temperatura [°C]', 'Esp. manguito hielo [cm]', 
                        'Vano Regulador [m]', 'Carga Peso [daN/m]', 'Carga Hielo [daN/m]', 
                        'Carga Viento [daN/m]', 'Carga vectorial [daN/m]', 'Tensión [daN/mm2]', 
                        'Tiro [daN]', 'Flecha [m]', 'Flecha Vertical [m]', '% rotura', 'Estado determinante']

        if es_guardia:
            columnas_base.append('Rel. flecha')

        print(f"  ✅ Cálculo completado: t_final={t_final:.6f} daN/mm²")
        if estado_limitante and estado_limitante not in ["Límite mínimo físico", "Límite máximo físico"]:
            print(f"  🟡 Estado limitante: {estado_limitante}")

        return df_resultados[columnas_base], resultados_final, estado_limitante



class LibCables:
    """lib para administrar múltiples cables"""
    
    def __init__(self):
        self.cables = {}
    
    def agregar_cable(self, cable):
        """Agrega un cable al lib"""
        self.cables[cable.id] = cable
    
    def obtener_cable(self, id_cable):
        """Obtiene un cable por ID"""
        return self.cables.get(id_cable)
    
    def listar_cables(self):
        """Lista todos los cables disponibles"""
        print("📋 CABLES DISPONIBLES:")
        print("=" * 80)
        for cable_id, cable in self.cables.items():
            props = cable.propiedades
            print(f"  - {cable_id}: {props['material']}, "
                  f"Ø{props['diametro_total_mm']}mm, "
                  f"Sección: {props['seccion_total_mm2']}mm², "
                  f"Peso: {props['peso_unitario_dan_m']} daN/m")
    
    def buscar_por_material(self, material):
        """Busca cables por material"""
        return [cable for cable in self.cables.values() 
                if cable.propiedades.get("material", "").lower() == material.lower()] 
    

########### ELEMENTO_AEA

class Elemento_AEA:
    """
    Clase para representar elementos estructurales (cadenas, estructuras) según norma AEA 95301-2007
    """
    
    # Parámetros por exposición según Tabla 10.2-h AEA (los mismos que para cables)
    EXPOSICIONES = {
        "B": {"alpha": 4.5, "k": 0.01,  "Ls": 52,  "Zs": 366},
        "C": {"alpha": 7.5, "k": 0.005, "Ls": 67,  "Zs": 274},
        "D": {"alpha": 10,  "k": 0.003, "Ls": 76,  "Zs": 213},
    }
    
    # Clases de línea según tensión (factor de carga Fc) - Tabla 10.2-b
    CLASES_LINEA = {
        "B":  {"Fc": 0.93, "Vmin": 1,   "Vmax": 66},
        "BB": {"Fc": 1.00, "Vmin": 1,   "Vmax": 38},
        "C":  {"Fc": 1.15, "Vmin": 66,  "Vmax": 220},
        "D":  {"Fc": 1.30, "Vmin": 220, "Vmax": 800},
        "E":  {"Fc": 1.40, "Vmin": 800, "Vmax": 9999},
    }
    
    def __init__(self, id_elemento, nombre, area_transversal_m2, area_longitudinal_m2, Cf, Z, peso_daN):
        """
        Inicializa un objeto elemento estructural

        Args:
            id_elemento (str): Identificador único del elemento
            nombre (str): Nombre descriptivo del elemento
            area_transversal_m2 (float): Área expuesta al viento transversal en m²
            area_longitudinal_m2 (float): Área expuesta al viento longitudinal en m²
            Cf (float): Coeficiente de fuerza
            Z (float): Altura efectiva del elemento en metros
            peso_daN (float): Peso del elemento en daN
        """
        self.id = id_elemento
        self.nombre = nombre
        self.area_transversal_m2 = area_transversal_m2
        self.area_longitudinal_m2 = area_longitudinal_m2
        self.Cf = Cf
        self.Z = Z
        self.peso_daN = peso_daN
        
    def __str__(self):
        """Representación en string del elemento"""
        return f"Elemento {self.id}: {self.nombre} - A_trans: {self.area_transversal_m2:.3f}m², A_long: {self.area_longitudinal_m2:.3f}m²"
    
    def __repr__(self):
        """Representación para debugging"""
        return f"ELEMENTO_AEA('{self.id}', '{self.nombre}', {self.area_transversal_m2}, {self.area_longitudinal_m2}, {self.Cf}, {self.Z})"
    
    def _factor_Zp(self, Z, Zs, alpha_expo):
        """Calcula Zp según AEA 95301 (método interno)"""
        return 1.61 * (Z / Zs)**(1/alpha_expo)
    
    def _factor_Gt(self, Z, alpha_expo, k, Ls):
        """Gt para estructuras y cadenas (método interno)"""
        E = 4.9 * math.sqrt(k) * (10 / Z)**(1/alpha_expo)
        Bt = 1 / (1 + 0.375 * (Z / Ls))
        Gt = 1 + 2.7 * E * math.sqrt(Bt)
        kv = 1.425
        Gt = Gt / (kv**2)
        return Gt, E, Bt
    
    def cargaViento(self, V, theta_deg=90, exp="C", clase="B", Q=0.613, L_vano=150.0):
        """
        Calcula la carga de viento sobre el elemento según AEA 95301 - CORREGIDO
        
        Args:
            V (float): Velocidad del viento en m/s
            theta_deg (float): Ángulo del viento respecto al eje transversal en grados
                            (0 = longitudinal puro, 90 = transversal puro)
            exp (str): Tipo de exposición ("B", "C", "D")
            clase (str): Clase de línea ("B", "BB", "C", "D", "E")
            Q (float): Presión dinámica de referencia (default 0.613)
            L_vano (float): Longitud del vano en metros (para consistencia)
            
        Returns:
            dict: Diccionario con resultados detallados, ahora incluye componentes separadas
        """
        # Validaciones (mantener igual)
        if exp not in self.EXPOSICIONES:
            raise ValueError(f"Exposición '{exp}' no válida. Use: {list(self.EXPOSICIONES.keys())}")
        if clase not in self.CLASES_LINEA:
            raise ValueError(f"Clase '{clase}' no válida. Use: {list(self.CLASES_LINEA.keys())}")
        
        # Obtener parámetros de exposición y clase (mantener igual)
        expo = self.EXPOSICIONES[exp]
        alpha_expo = expo["alpha"]
        k = expo["k"]
        Ls = expo["Ls"]
        Zs = expo["Zs"]
        Fc = self.CLASES_LINEA[clase]["Fc"]
        
        # Factor Zp (mantener igual)
        Zp = self._factor_Zp(self.Z, Zs, alpha_expo)
        
        # Factor Gt para elementos estructurales (mantener igual)
        G, E, B = self._factor_Gt(self.Z, alpha_expo, k, Ls)
        
        # Calcular fuerzas por separado para áreas transversal y longitudinal
        # CORRECCIÓN: INVERTIR ASIGNACIÓN DE ÁREAS
        theta_rad = math.radians(theta_deg)
        
        # FUERZA TRANSVERSAL (actúa sobre área transversal)
        # Componente del viento en dirección transversal: V * sin(theta)
        V_trans = V * abs(math.sin(theta_rad))
        F_trans_N = Q * (Zp * V_trans)**2 * Fc * G * self.Cf * self.area_transversal_m2
        F_trans_daN = F_trans_N * 0.1
        
        # FUERZA LONGITUDINAL (actúa sobre área longitudinal)  
        # Componente del viento en dirección longitudinal: V * cos(theta)
        V_long = V * abs(math.cos(theta_rad))
        F_long_N = Q * (Zp * V_long)**2 * Fc * G * self.Cf * self.area_longitudinal_m2
        F_long_daN = F_long_N * 0.1
        
        # Fuerza total (vectorial)
        F_total_daN = math.sqrt(F_trans_daN**2 + F_long_daN**2)
        
        return {
            "elemento_id": self.id,
            "elemento_nombre": self.nombre,
            "fuerza_transversal_daN": F_trans_daN,
            "fuerza_longitudinal_daN": F_long_daN,
            "fuerza_total_daN": F_total_daN,
            "fuerza_transversal_N": F_trans_N,
            "fuerza_longitudinal_N": F_long_N,
            "Zp": Zp,
            "G": G,
            "E": E,
            "B": B,
            "Fc": Fc,
            "theta_grados": theta_deg,
            "viento_transversal_m_s": V_trans,
            "viento_longitudinal_m_s": V_long,
            "exposicion": exp,
            "clase_linea": clase
        }
    
def cargaPeso(self, espesor_hielo_m=None, densidad_hielo_kg_m3=900):
    """
    Calcula la carga por peso del cable, opcionalmente con hielo
    (AHORA USA EL MÉTODO CENTRALIZADO)
    
    Args:
        espesor_hielo_m (float, optional): Espesor de hielo en metros
        densidad_hielo_kg_m3 (float): Densidad del hielo en kg/m³ (default 900)
            
    Returns:
        float: Carga de peso total (cable + hielo) en daN/m
    """
    peso_hielo = self._calcular_peso_hielo(espesor_hielo_m, densidad_hielo_kg_m3)
    return self.peso_unitario_dan_m + peso_hielo

    def info_completa(self):
        """Devuelve información completa del elemento"""
        info = {
            "ID": self.id,
            "Nombre": self.nombre,
            "Área transversal (m²)": self.area_transversal_m2,
            "Área longitudinal (m²)": self.area_longitudinal_m2,
            "Coeficiente de fuerza": self.Cf,
            "Altura efectiva (m)": self.Z
        }
        return info