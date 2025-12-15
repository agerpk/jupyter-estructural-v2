# EstructuraAEA_Geometria.py
import pandas as pd
import math

class NodoEstructural:
    """
    Clase que representa un nodo estructural con sus propiedades y cargas
    """
    
    def __init__(self, nombre, coordenadas, tipo_nodo, cable_asociado=None, 
                angulo_quiebre=0, tipo_fijacion=None):
        """
        Inicializa un nodo estructural
        
        Args:
            nombre (str): Identificador único del nodo
            coordenadas (tuple): (x, y, z) en metros
            tipo_nodo (str): "conductor", "guardia", "base", "cruce", "general", "viento"
            cable_asociado (CABLE_AEA, optional): Objeto cable asociado
            angulo_quiebre (float): Ángulo de quiebre en grados
            tipo_fijacion (str): "suspensión" o "retención" (se determina automáticamente)
        """
        self.nombre = nombre
        self.coordenadas = coordenadas  # (x, y, z)
        self.tipo_nodo = tipo_nodo
        self.cable_asociado = cable_asociado
        self.angulo_quiebre = angulo_quiebre
        
        # Determinar tipo de fijación basado en el tipo de estructura
        if tipo_fijacion is None:
            if "suspens" in tipo_nodo.lower():
                self.tipo_fijacion = "suspensión"
            else:
                self.tipo_fijacion = "retención"
        else:
            self.tipo_fijacion = tipo_fijacion
            
        self.cargas = {}  # Diccionario: {codigo_hipotesis: [Fx, Fy, Fz]}
        
    def __str__(self):
        return f"Nodo({self.nombre}, {self.tipo_nodo}, {self.coordenadas})"
    
    def __repr__(self):
        return f"NodoEstructural('{self.nombre}', {self.coordenadas}, '{self.tipo_nodo}')"
    
    def agregar_carga(self, codigo_hipotesis, fuerza_x, fuerza_y, fuerza_z):
        """Agrega una carga al nodo para una hipótesis específica"""
        self.cargas[codigo_hipotesis] = [round(fuerza_x, 2), round(fuerza_y, 2), round(fuerza_z, 2)]
    
    def obtener_carga(self, codigo_hipotesis):
        """Obtiene la carga para una hipótesis específica"""
        return self.cargas.get(codigo_hipotesis, [0.0, 0.0, 0.0])
    
    def obtener_coordenadas_dict(self):
        """Devuelve coordenadas en formato de diccionario para compatibilidad"""
        return {self.nombre: list(self.coordenadas)}
    
    def info_completa(self):
        """Devuelve información completa del nodo"""
        info = {
            "Nombre": self.nombre,
            "Coordenadas": f"({self.coordenadas[0]:.2f}, {self.coordenadas[1]:.2f}, {self.coordenadas[2]:.2f})",
            "Tipo": self.tipo_nodo,
            "Cable asociado": self.cable_asociado.nombre if self.cable_asociado else "Ninguno",
            "Ángulo quiebre": f"{self.angulo_quiebre}°",
            "Tipo fijación": self.tipo_fijacion,
            "Hipótesis cargadas": len(self.cargas)
        }
        return info


class EstructuraAEA_Geometria:
    """
    Clase especializada en cálculos geométricos de la estructura según norma AEA
    Incluye dimensionamiento, creación de nodos y cálculos de distancias
    Sigue el proceso de 15 pasos indicado
    """
    
    # Variables globales (pueden ser configuradas desde el notebook)
    HG_CENTRADO = True  # Por defecto el cable guardia está centrado
    ANG_APANTALLAMIENTO = 30.0  # Ángulo de apantallamiento en grados por defecto
    AJUSTAR_POR_ALTURA_MSNM = False  # Por defecto no ajustar
    METODO_ALTURA_MSNM = "AEA 3%/300m"  # Método por defecto
    ALTURA_MSNM = 1000.0  # Altura sobre el nivel del mar en metros por defecto (no genera variación de distancias)
    
    # Tabla de tensiones máximas del sistema
    TABLA_TENSION_MAXIMA = {
        13.2: 13.8, 33: 36, 66: 72.5, 132: 145, 220: 245, 500: 550
    }
    
    # Coeficientes k según disposición y ángulo
    COEFICIENTES_K = {
        "vertical": {"<45°": 0.70, "45° a 55°": 0.75, "55° a 65°": 0.85, ">65°": 0.95},
        "triangular": {"<45°": 0.62, "45° a 55°": 0.65, "55° a 65°": 0.70, ">65°": 0.75},
        "horizontal": {"<45°": 0.60, "45° a 55°": 0.62, "55° a 65°": 0.70, ">65°": 0.75}
    }
    
    # Alturas mínimas sobre terreno (a)
    ALTURAS_MINIMAS_TERRENO = {
        "Peatonal": 4.70, "Rural": 5.90, "Urbana": 8.38, 
        "Autopista": 7.00, "Ferrocarril": 8.50, "Línea Eléctrica": 1.20
    }
    
    # Mapeo de estados climáticos
    ESTADOS_MAPEO = {
        "Vmax": "III", "Vmed": "IV", "TMA": "V", "Tmin": "II", "Tmax": "I"
    }
    
    def __init__(self, tipo_estructura, tension_nominal, zona_estructura, 
                disposicion, terna, cant_hg, alpha_quiebre,
                altura_minima_cable, long_mensula_min_conductor, long_mensula_min_guardia,
                hadd, hadd_entre_amarres, lk, ancho_cruceta,
                cable_conductor, cable_guardia, peso_estructura=0, peso_cadena=None,
                hg_centrado=None, ang_apantallamiento=None, hadd_hg=0.0, hadd_lmen=0.0,
                dist_reposicionar_hg=0.1, ajustar_por_altura_msnm=None,
                metodo_altura_msnm=None, altura_msnm=None):  # ← NUEVOS PARÁMETROS
        """
        Inicializa una estructura completa
        
        Args:
            tipo_estructura (str): Tipo de estructura (Suspensión Recta, Retención, etc.)
            tension_nominal (float): Tensión nominal en kV
            zona_estructura (str): Zona (Rural, Urbana, etc.)
            disposicion (str): Disposición (horizontal, triangular, vertical)
            terna (str): Terna (Simple, Doble)
            cant_hg (int): Cantidad de cables guardia (0, 1, 2)
            alpha_quiebre (float): Ángulo de quiebre en grados
            altura_minima_cable (float): Altura mínima del cable sobre terreno
            long_mensula_min_conductor (float): Longitud mínima de ménsula para conductor
            long_mensula_min_guardia (float): Longitud mínima de ménsula para guardia
            hadd (float): Altura adicional (HADD libre)
            hadd_entre_amarres (float): HADD entre fases (HADD_fase)
            lk (float): Longitud de cadena
            ancho_cruceta (float): Ancho de cruceta
            cable_conductor (CABLE_AEA): Objeto cable conductor
            cable_guardia (CABLE_AEA): Objeto cable guardia
            peso_estructura (float): Peso de la estructura en daN
            peso_cadena (float): Peso de la cadena en daN
            hg_centrado (bool): Indica si el cable guardia está centrado
            ang_apantallamiento (float): Ángulo de apantallamiento en grados
            hadd_hg (float): Altura adicional para cable guardia
            hadd_lmen (float): Altura adicional para longitud de ménsula
            ajustar_por_altura_msnm (bool): Si True, ajusta distancias por altura MSNM
            metodo_altura_msnm (str): Método de ajuste (actualmente solo "AEA 3%/300m")
            altura_msnm (float): Altura sobre el nivel del mar en metros
        """
        # Parámetros básicos
        self.tipo_estructura = tipo_estructura
        self.tension_nominal = tension_nominal
        self.zona_estructura = zona_estructura
        self.disposicion = disposicion.lower()
        self.terna = terna
        self.cant_hg = cant_hg
        self.alpha_quiebre = alpha_quiebre
        self.altura_minima_cable = altura_minima_cable
        self.long_mensula_min_conductor = long_mensula_min_conductor
        self.long_mensula_min_guardia = long_mensula_min_guardia
        self.hadd = hadd
        self.hadd_entre_amarres = hadd_entre_amarres
        self.lk = lk
        self.ancho_cruceta = ancho_cruceta
        self.peso_estructura = peso_estructura
        self.peso_cadena = peso_cadena
        self.dist_reposicionar_hg = dist_reposicionar_hg
        self.ajustar_por_altura_msnm = ajustar_por_altura_msnm if ajustar_por_altura_msnm is not None else self.AJUSTAR_POR_ALTURA_MSNM
        self.metodo_altura_msnm = metodo_altura_msnm if metodo_altura_msnm is not None else self.METODO_ALTURA_MSNM
        self.altura_msnm = altura_msnm if altura_msnm is not None else self.ALTURA_MSNM
        
        # Nuevos parámetros
        self.hg_centrado = hg_centrado if hg_centrado is not None else self.HG_CENTRADO
        self.ang_apantallamiento = ang_apantallamiento if ang_apantallamiento is not None else self.ANG_APANTALLAMIENTO
        self.hadd_hg = hadd_hg
        self.hadd_lmen = hadd_lmen
        
        # Validar parámetros requeridos
        if self.peso_estructura == 0:
            raise ValueError("El parámetro 'peso_estructura' es requerido y debe ser mayor a 0")
        
        if self.peso_cadena is None:
            raise ValueError("El parámetro 'peso_cadena' es requerido para el cálculo de theta_max")
        
        # Cables asociados
        self.cable_conductor = cable_conductor
        self.cable_guardia1 = cable_guardia  # Guardia 1 (derecha, x+)
        self.cable_guardia2 = None  # Guardia 2 (izquierda, x-) - se asigna después
        self.cable_guardia = cable_guardia  # Mantener para compatibilidad
        
        # Colección de nodos
        self.nodos = {}
        
        # Resultados de dimensionamiento
        self.dimensiones = {}
        self.nodes_key = {}  # Para compatibilidad
        
        # Variables auxiliares para el nuevo proceso
        self.h_base_electrica = 0.0
        self.lmen = 0.0
        self.lmen2c = 0.0  # Longitud para segundo conductor en ménsula (terna doble triangular)
        self.pcma = (0.0, 0.0)  # Posición conductor más alto (x, y)
        self.hhg = 0.0
        self.lmenhg = 0.0
        self.phg1 = (0.0, 0.0)  # Posición cable guardia 1
        self.phg2 = (0.0, 0.0)  # Posición cable guardia 2 (si hay 2)
        
        # Para almacenar DataFrames de parámetros
        self.parametros_cabezal = None
        
        # Configuración por defecto
        self._configurar_parametros_default()
        
        print(f"✅ ESTRUCTURA_AEA GEOMETRÍA CREADA: {self.tipo_estructura} - {self.tension_nominal}kV - {self.zona_estructura}")
    
    def _configurar_parametros_default(self):
        """Configura parámetros por defecto y derivados"""
        self.tension_maxima = self.TABLA_TENSION_MAXIMA.get(
            self.tension_nominal, self.tension_nominal * 1.1
        )
        
        # Determinar tipo de fijación base
        tipo_lower = self.tipo_estructura.lower()
        if "retención" in tipo_lower or "terminal" in tipo_lower or "retencion" in tipo_lower:
            self.tipo_fijacion_base = "retención"
        elif "suspension" in tipo_lower or "suspensión" in tipo_lower:
            self.tipo_fijacion_base = "suspensión"
        else:
            self.tipo_fijacion_base = "suspensión"
    
    def _obtener_coeficiente_k(self, theta_max):
        """Obtiene el coeficiente k según disposición y ángulo de declinación theta_max"""
        if theta_max < 45:
            rango = "<45°"
        elif 45 <= theta_max < 55:
            rango = "45° a 55°"
        elif 55 <= theta_max < 65:
            rango = "55° a 65°"
        else:
            rango = ">65°"
        
        return self.COEFICIENTES_K.get(self.disposicion, {}).get(rango, 0.70)
    
    def _calcular_altura_base_electrica(self, b):
        """Calcula la altura base eléctrica: a + b >= altura_minima_cable"""
        # a = altura mínima según zona
        a = self.ALTURAS_MINIMAS_TERRENO.get(self.zona_estructura, 99)
        
        # Calcular a + b
        h_base = a + b
        
        # Verificar que sea mayor o igual a altura_minima_cable
        if h_base < self.altura_minima_cable:
            h_base = self.altura_minima_cable
        
        return h_base
    
    def calcular_theta_max(self, vano, elemento_cadena=None):
        """
        Calcula el ángulo máximo de declinación theta_max usando cache de viento
        
        Args:
            vano (float): Longitud del vano en metros
            elemento_cadena (Elemento_AEA, optional): Objeto cadena para calcular viento en cadena
            
        Returns:
            float: Ángulo theta_max en grados
        """
        print(f"📐 CALCULANDO THETA_MAX...")
        
        # Si no es estructura de suspensión O Lk = 0, entonces theta_max = 0
        if self.tipo_fijacion_base != "suspensión" or self.lk == 0:
            theta_max = 0.0
            print(f"   📐 theta_max = 0° (estructura no es suspensión o Lk=0)")
        else:
            try:
                # Usar cache de viento del cable conductor
                cable = self.cable_conductor
                
                # Verificar si tiene cache
                if not hasattr(cable, 'viento_cache') or not cable.viento_cache:
                    print("   ❌ ERROR: El objeto Cable no tiene datos de viento en cache.")
                    return 99.0
                
                # Intentar obtener del cache
                if 'V_90' in cable.viento_cache:
                    resultado_cache = cable.viento_cache['V_90']
                    if resultado_cache:
                        carga_viento_conductor = resultado_cache['fuerza_total_daN']
                        print(f"   📐 Usando cache de viento: V_90")
                    else:
                        print("   ❌ ERROR: No hay datos de viento en cache para V_90.")
                        return 99.0
                else:
                    print("   ❌ ERROR: No hay datos de viento en cache para V_90.")
                    return 99.0
                
                # Calcular viento en cadena si se proporciona el elemento
                carga_viento_cadena = 0.0
                if elemento_cadena is not None and hasattr(elemento_cadena, 'viento_cache'):
                    if 'V_90' in elemento_cadena.viento_cache:
                        resultado_cache_cadena = elemento_cadena.viento_cache['V_90']
                        if resultado_cache_cadena:
                            carga_viento_cadena = resultado_cache_cadena['fuerza_total_daN']
                            print(f"   📐 Viento en cadena incluido: {carga_viento_cadena:.2f} daN")
                
                # Peso del conductor en el vano
                peso_conductor = cable.peso_unitario_dan_m * vano
                peso_cadena = self.peso_cadena
                
                # Calcular theta_max usando arctan((Fv + Fca) / (Pc + Pcadena))
                fuerza_viento_total = carga_viento_conductor + carga_viento_cadena
                if (peso_conductor + peso_cadena) > 0:
                    theta_max_rad = math.atan(fuerza_viento_total / (peso_conductor + peso_cadena))
                    theta_max = math.degrees(theta_max_rad)
                else:
                    theta_max = 99.0

                print(f"   📐 Cálculo theta_max (suspensión con Lk>0):")
                print(f"      - Carga viento conductor (Fv): {carga_viento_conductor:.2f} daN")
                print(f"      - Carga viento cadena (Fca): {carga_viento_cadena:.2f} daN")
                print(f"      - Fuerza viento total (Fv + Fca): {fuerza_viento_total:.2f} daN")
                print(f"      - Peso conductor: {peso_conductor:.2f} daN")
                print(f"      - Peso cadena: {peso_cadena:.2f} daN")
                print(f"      - theta_max calculado: {theta_max:.2f}°")
                
            except Exception as e:
                print(f"   ⚠️ Error calculando theta_max: {e}")
                theta_max = 99.0
        
        return theta_max
    
    def calcular_distancias_minimas(self, flecha_max_conductor, theta_max):
        """
        Calcula las distancias mínimas según norma AEA según el proceso indicado
        
        Args:
            flecha_max_conductor (float): Flecha máxima del conductor en metros
            theta_max (float): Ángulo máximo de declinación en grados
            
        Returns:
            dict: Diccionario con distancias calculadas
        """
        print(f"📐 CALCULANDO DISTANCIAS MÍNIMAS...")
        
        # 1. Obtener coeficiente k basado en theta_max
        k = self._obtener_coeficiente_k(theta_max)
        
        # 2. Calcular coeficiente de ajuste por altura MSNM (Ka)
        Ka = self._calcular_coeficiente_altura()
        
        # 3. Término común: flecha + longitud de cadena
        termino_flecha = flecha_max_conductor + self.lk
        
        # 4. Distancia mínima entre fases (D) - AJUSTADO POR ALTURA
        D_fases = k * math.sqrt(termino_flecha) + Ka * self.tension_nominal / 150
        
        # 5. Distancia mínima fase-estructura (s) - AJUSTADO POR ALTURA
        s_base = 0.280 + 0.005 * (self.tension_maxima - 50)
        s_base = s_base * Ka
        s_estructura = max(s_base, Ka * self.tension_nominal / 150)
        
        # 6. Distancia mínima guardia-conductor (Dhg) - AJUSTADO POR ALTURA
        Dhg = k * math.sqrt(termino_flecha) + Ka * (self.tension_nominal / math.sqrt(3)) / 150
        
        # 7. Componente eléctrico adicional (b) - AJUSTADO POR ALTURA
        b = 0.01 * (self.tension_nominal / math.sqrt(3) - 22) if self.tension_nominal > 33 else 0.0
        b = b * Ka
        
        # 8. Calcular altura base eléctrica (a + b >= altura_minima_cable)
        h_base_electrica = self._calcular_altura_base_electrica(b)
        
        # Guardar en diccionario de resultados
        distancias = {
            'theta_max': theta_max,
            'k': k,
            'Ka': Ka,  # ← NUEVO: Guardar coeficiente de altura
            'D_fases': D_fases,
            's_estructura': s_estructura,
            'Dhg': Dhg,
            'b': b,
            'h_base_electrica': h_base_electrica,
            'termino_flecha': termino_flecha
        }
        
        print(f"   📊 Distancias calculadas:")
        print(f"      - k: {k:.3f}")
        print(f"      - Ka (coef. altura): {Ka:.3f}")  # ← NUEVO
        print(f"      - D_fases: {D_fases:.3f} m")
        print(f"      - s_estructura: {s_estructura:.3f} m")
        print(f"      - Dhg: {Dhg:.3f} m")
        print(f"      - b: {b:.3f} m")
        print(f"      - Altura base eléctrica: {h_base_electrica:.3f} m")
        
        return distancias
    
    def _calcular_alturas_fases(self, D_fases, s_estructura, flecha_max_conductor):
        """Calcula las alturas h1a, h2a, h3a según el proceso indicado"""
        # 1. h1a = HADD + h_base_electrica + fmax + lk
        h1a = self.hadd + self.h_base_electrica + flecha_max_conductor + self.lk
        
        # Inicializar h2a y h3a
        h2a = h1a
        h3a = h1a
        
        # 2. Calcular h2a si: (disposición=triangular) o (disposición=vertical)
        if self.disposicion in ["triangular", "vertical"]:
            termino1 = self.hadd_entre_amarres + s_estructura + self.lk + self.ancho_cruceta
            termino2 = self.hadd_entre_amarres - self.lk + D_fases
            h2a = h1a + max(termino1, termino2)
        
        # 3. Calcular h3a si: (disposición=vertical)
        if self.disposicion == "vertical":
            termino1 = self.hadd_entre_amarres + s_estructura + self.lk
            termino2 = self.hadd_entre_amarres - self.lk + self.hadd_entre_amarres
            h3a = h2a + max(termino1, termino2)
        
        return h1a, h2a, h3a
    
    def _calcular_longitud_mensula(self, s_estructura, theta_max):
        """Calcula la longitud de ménsula según el proceso indicado"""
        # lmen = max(s_estructura + lk*sin(theta_max) + hadd_lmen, lmen_minimo)
        lmen_base = s_estructura + self.lk * math.sin(math.radians(theta_max)) + self.hadd_lmen
        lmen = max(lmen_base, self.long_mensula_min_conductor)
        
        return lmen
    
    def _calcular_posicion_conductor_mas_alto(self, h1a, h2a, h3a, lmen, s_estructura=None, D_fases=None, theta_max=None):
        """Calcula la posición del conductor más alto (pcma)"""
        # Determinar altura según disposición
        if self.disposicion == "vertical" and h3a > h2a:
            y = h3a - self.lk
            x = lmen
        elif self.disposicion == "triangular" and h2a > h1a:
            y = h2a - self.lk
            x = lmen
        elif self.disposicion == "horizontal":
            # Para horizontal, el conductor más alejado está en dist_conductor_final
            y = h1a - self.lk
            # Usar parámetros pasados o valores por defecto
            s_estructura = s_estructura if s_estructura is not None else 0.5
            D_fases = D_fases if D_fases is not None else 1.5
            theta_max = theta_max if theta_max is not None else 0.0
            dist_columna_x = max(self.lk * math.sin(math.radians(theta_max)) + s_estructura, D_fases / 2)
            dist_conductor_final = max(D_fases, dist_columna_x + self.lk * math.sin(math.radians(theta_max)) + s_estructura + self.ancho_cruceta/2)
            x = dist_conductor_final
        else:
            y = h1a - self.lk
            x = lmen
        
        return (x, y)
    
    def _calcular_cable_guardia(self, pcma, D_fases, Dhg, h1a, h2a, h3a, lmen, lmen2c, 
                            dist_reposicionar_hg=0.1, autoajustar_lmenhg=True, s_estructura=None, D_fases_param=None, theta_max=None):
        """Calcula las posiciones de los cables de guardia según configuración con ajustes iterativos"""
        x_pcma, y_pcma = pcma
        ang_rad = math.radians(self.ang_apantallamiento)
        
        # Si no hay cable guardia
        if self.cant_hg == 0:
            self.hhg = 0.0
            self.lmenhg = 0.0
            self.phg1 = (0.0, 0.0)
            self.phg2 = (0.0, 0.0)
            print(f"   🚫 No hay cable guardia (CANT_HG = 0)")
            return
        
        # Si hay 1 cable guardia centrado
        if self.cant_hg == 1 and self.hg_centrado:
            # hhg = pcma(x) / tan(ang_apantallamiento) + pcma(y)
            self.hhg = x_pcma / math.tan(ang_rad) + y_pcma
            self.lmenhg = 0.0
            self.phg1 = (0.0, self.hhg)
            print(f"   🛡️  Cable guardia centrado: hhg={self.hhg:.2f}m, phg1=(0, {self.hhg:.2f})")
        
        # Si hay 1 cable guardia NO centrado
        elif self.cant_hg == 1 and not self.hg_centrado:
            # dvhg = Dhg * cos(ang_apantallamiento) + HADD_hg
            dvhg = Dhg * math.cos(ang_rad) + self.hadd_hg
            self.hhg = y_pcma + dvhg
            
            # lmenhg = max(lmenhg_minima, pcma(x) - (dvhg/cos(ang_apantallamiento)) * sin(ang_apantallamiento))
            term = (dvhg / math.cos(ang_rad)) * math.sin(ang_rad)
            lmenhg_base = x_pcma - term
            self.lmenhg = max(lmenhg_base, self.long_mensula_min_guardia)
            
            self.phg1 = (self.lmenhg, self.hhg)
            print(f"   🛡️  Cable guardia no centrado inicial: hhg={self.hhg:.2f}m, lmenhg={self.lmenhg:.2f}m")
            
            # APLICAR AJUSTES ITERATIVOS (solo si autoajustar_lmenhg es True)
            if autoajustar_lmenhg:
                pcma_conductor = (x_pcma, y_pcma - self.lk)
                # Llamar al ajuste con la posición del CONDUCTOR
                self._ajustar_lmenhg_iterativo(Dhg, h1a, h2a, h3a, lmen, lmen2c, dist_reposicionar_hg, s_estructura, D_fases_param, theta_max)
            else:
                print(f"   ⏭️  Ajuste iterativo de lmenhg DESACTIVADO (autoajustar_lmenhg=False)")
            
            print(f"   🛡️  Cable guardia no centrado final: lmenhg={self.lmenhg:.3f}m, phg1=({self.phg1[0]:.3f}, {self.phg1[1]:.3f})")
        
        # Si hay 2 cables guardia
        elif self.cant_hg == 2:
            # hhg = Dhg * cos(ang_apantallamiento) + HADD_hg + pcma(y)
            dvhg = Dhg * math.cos(ang_rad) + self.hadd_hg
            self.hhg = y_pcma + dvhg
            
            # lmenhg = max(lmenhg_minima, pcma(x) - Dhg * sin(ang_apantallamiento))
            lmenhg_base = x_pcma - Dhg * math.sin(ang_rad)
            self.lmenhg = max(lmenhg_base, self.long_mensula_min_guardia)
            
            self.phg1 = (self.lmenhg, self.hhg)
            self.phg2 = (-self.lmenhg, self.hhg)
            print(f"   🛡️  Dos cables guardia inicial: hhg={self.hhg:.2f}m, lmenhg={self.lmenhg:.2f}m")
            
            # APLICAR AJUSTES ITERATIVOS (solo si autoajustar_lmenhg es True)
            if autoajustar_lmenhg:
                pcma_conductor = (x_pcma, y_pcma - self.lk)
                # Llamar al ajuste con la posición del CONDUCTOR
                self._ajustar_lmenhg_iterativo(Dhg, h1a, h2a, h3a, lmen, lmen2c, dist_reposicionar_hg, s_estructura, D_fases_param, theta_max)
            else:
                print(f"   ⏭️  Ajuste iterativo de lmenhg DESACTIVADO (autoajustar_lmenhg=False)")
            
            print(f"   🛡️  Dos cables guardia final: lmenhg={self.lmenhg:.3f}m")
            print(f"      phg1=({self.phg1[0]:.3f}, {self.phg1[1]:.3f}), phg2=({self.phg2[0]:.3f}, {self.phg2[1]:.3f})")
        
        # Verificar distancia diagonal entre conductor y cable guardia
        if self.cant_hg > 0:
            self._verificar_distancias_diagonales(pcma, Dhg)
    
    def _verificar_distancias_diagonales(self, pcma, Dhg_min):
        """Verifica que las distancias mínimas diagonales se cumplan"""
        x_pcma, y_pcma = pcma
        # Ajustar por lk para obtener posición real del conductor
        y_pcma_conductor = y_pcma - self.lk
        
        if self.cant_hg == 1:
            x_hg, y_hg = self.phg1
            distancia = math.sqrt((x_hg - x_pcma)**2 + (y_hg - y_pcma_conductor)**2)
            cumple = distancia >= Dhg_min
            print(f"   📏 Distancia diagonal CONDUCTOR-guardia: {distancia:.3f} m (mínimo: {Dhg_min:.3f} m) - {'✅ CUMPLE' if cumple else '❌ NO CUMPLE'}")
        
        elif self.cant_hg == 2:
            x_hg1, y_hg1 = self.phg1
            x_hg2, y_hg2 = self.phg2
            
            dist1 = math.sqrt((x_hg1 - x_pcma)**2 + (y_hg1 - y_pcma_conductor)**2)
            dist2 = math.sqrt((x_hg2 - x_pcma)**2 + (y_hg2 - y_pcma_conductor)**2)
            
            cumple1 = dist1 >= Dhg_min
            cumple2 = dist2 >= Dhg_min
            
            print(f"   📏 Distancia diagonal CONDUCTOR-guardia1: {dist1:.3f} m (mínimo: {Dhg_min:.3f} m) - {'✅ CUMPLE' if cumple1 else '❌ NO CUMPLE'}")
            print(f"   📏 Distancia diagonal CONDUCTOR-guardia2: {dist2:.3f} m (mínimo: {Dhg_min:.3f} m) - {'✅ CUMPLE' if cumple2 else '❌ NO CUMPLE'}")
    
    def dimensionar_unifilar(self, vano, flecha_max_conductor, flecha_max_guardia, dist_reposicionar_hg=0.1, autoajustar_lmenhg=False, elemento_cadena=None):
        """
        Dimensiona la estructura según el proceso indicado paso a paso
        
        Args:
            vano (float): Longitud del vano en metros
            flecha_max_conductor (float): Flecha máxima del conductor
            flecha_max_guardia (float): Flecha máxima del guardia
            dist_reposicionar_hg (float): Distancia para reposicionar HG (m)
            autoajustar_lmenhg (bool): Si True, aplica ajuste iterativo de lmenhg
            elemento_cadena (Elemento_AEA, optional): Objeto cadena para calcular viento en cadena
        """
        print(f"📐 DIMENSIONANDO ESTRUCTURA UNIFILAR SEGÚN PROCESO INDICADO...")
        print(f"   Vano: {vano}m, Flechas: cond={flecha_max_conductor:.2f}m, guard={flecha_max_guardia:.2f}m")
        print(f"   Autoajustar lmenhg: {'✅ ACTIVADO' if autoajustar_lmenhg else '❌ DESACTIVADO'}")
        
        # 1. CALCULAR THETA_MAX
        theta_max = self.calcular_theta_max(vano, elemento_cadena)
        
        # 2-3. CALCULAR DISTANCIAS MÍNIMAS Y COMPONENTE b
        distancias = self.calcular_distancias_minimas(flecha_max_conductor, theta_max)
        
        # Extraer valores
        D_fases = distancias['D_fases']
        s_estructura = distancias['s_estructura']
        Dhg = distancias['Dhg']
        b = distancias['b']
        self.h_base_electrica = distancias['h_base_electrica']
        
        # 4. Altura base eléctrica ya calculada en _calcular_altura_base_electrica
        
        # 5. CALCULAR ALTURAS DE FASES
        h1a, h2a, h3a = self._calcular_alturas_fases(D_fases, s_estructura, flecha_max_conductor)
        
        # 8. CALCULAR LONGITUD DE MENSULA
        self.lmen = self._calcular_longitud_mensula(s_estructura, theta_max)
        
        # 9. CALCULAR lmen2c si es necesario (terna doble triangular)
        self.lmen2c = self.lmen + D_fases if (self.disposicion == "triangular" and self.terna == "Doble") else self.lmen
        
        # 10. CALCULAR POSICIÓN CONDUCTOR MÁS ALTO
        self.pcma = self._calcular_posicion_conductor_mas_alto(h1a, h2a, h3a, self.lmen, s_estructura, D_fases, theta_max)
        
        # 11-13. CALCULAR CABLE GUARDIA (pasando autoajustar_lmenhg y parámetros)
        self._calcular_cable_guardia(self.pcma, D_fases, Dhg, h1a, h2a, h3a, self.lmen, self.lmen2c, 
                                    dist_reposicionar_hg, autoajustar_lmenhg, s_estructura, D_fases, theta_max)
        
        # 14. Verificaciones ya hechas en _calcular_cable_guardia
        
        # 15. CREAR NODOS SEGÚN CONFIGURACIÓN
        self._crear_nodos_estructurales_nuevo(h1a, h2a, h3a, s_estructura, D_fases, theta_max)
        
        # GUARDAR DIMENSIONES
        self.dimensiones = {
            "h1a": h1a, "h2a": h2a, "h3a": h3a, "hhg": self.hhg,
            "lmen": self.lmen, "lmen2c": self.lmen2c, "lmenhg": self.lmenhg,
            "pcma_x": self.pcma[0], "pcma_y": self.pcma[1],
            "phg1_x": self.phg1[0], "phg1_y": self.phg1[1],
            "phg2_x": self.phg2[0], "phg2_y": self.phg2[1],
            "D_fases": D_fases, "s_estructura": s_estructura, "Dhg": Dhg,
            "theta_max": theta_max, "k": distancias['k'],
            "h_base_electrica": self.h_base_electrica,
            "hg_centrado": self.hg_centrado,
            "ang_apantallamiento": self.ang_apantallamiento,
            "b": b,
            "altura_total": max(h3a, h2a, h1a, self.hhg),
            "autoajustar_lmenhg": autoajustar_lmenhg  # Guardar el estado
        }
        
        # CREAR DATAFRAME CON PARÁMETROS DEL CABEZAL
        self.parametros_cabezal = pd.DataFrame([self.dimensiones])
        
        print(f"✅ DIMENSIONAMIENTO COMPLETADO")
        print(f"   - Alturas: h1a={h1a:.2f}m, h2a={h2a:.2f}m, h3a={h3a:.2f}m")
        print(f"   - Ménsulas: lmen={self.lmen:.2f}m, lmen2c={self.lmen2c:.2f}m, lmenhg={self.lmenhg:.2f}m")
        print(f"   - Cable guardia: hhg={self.hhg:.2f}m, centrado={self.hg_centrado}")
        print(f"   - Conductor más alto: ({self.pcma[0]:.2f}, {self.pcma[1]:.2f})")

    
    def _crear_nodos_estructurales_nuevo(self, h1a, h2a, h3a, s_estructura=None, D_fases=None, theta_max=None):
        """Crea todos los nodos según el proceso indicado CORREGIDO"""
        self.nodos = {}
        
        # NODO BASE
        self.nodos["BASE"] = NodoEstructural(
            "BASE", (0.0, 0.0, 0.0), "base", 
            tipo_fijacion=self.tipo_fijacion_base
        )
        
        # NODOS DE CRUCE (poste-ménsula) - SOLO crear los necesarios
        # Solo crear CROSS_H1 si hay conductores en h1a
        if self.disposicion != "vertical" or h1a > 0:
            self.nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
        
        # Crear CROSS_H2 si hay conductores en h2a y h2a > h1a
        if (self.disposicion in ["triangular", "vertical"]) and h2a > h1a:
            self.nodos["CROSS_H2"] = NodoEstructural("CROSS_H2", (0.0, 0.0, h2a), "cruce")
        
        # Crear CROSS_H3 si hay conductores en h3a y h3a > h2a
        if self.disposicion == "vertical" and h3a > h2a:
            self.nodos["CROSS_H3"] = NodoEstructural("CROSS_H3", (0.0, 0.0, h3a), "cruce")
        
        # NODOS DE CONDUCTORES según configuración
        print(f"   🔍 DEBUG: disposicion='{self.disposicion}', terna='{self.terna}'")
        if self.disposicion == "horizontal":
            print("📐 Configuración horizontal")
            self._crear_nodos_horizontal_default(h1a, s_estructura, D_fases, theta_max)
        elif self.terna == "Simple" and self.disposicion == "vertical":
            self._crear_nodos_simple_vertical(h1a, h2a, h3a)
        elif self.terna == "Simple" and self.disposicion == "triangular":
            self._crear_nodos_simple_triangular(h1a, h2a)
        elif self.terna == "Doble" and self.disposicion == "vertical":
            self._crear_nodos_doble_vertical(h1a, h2a, h3a)
        elif self.terna == "Doble" and self.disposicion == "triangular":
            self._crear_nodos_doble_triangular(h1a, h2a)
        else:
            print(f"⚠️  Configuración no reconocida: terna={self.terna}, disposicion={self.disposicion}")
            self._crear_nodos_horizontal_default(h1a, s_estructura, D_fases, theta_max)
        
        # NODOS DE GUARDIA (ahora se maneja en _crear_nodos_guardia_nuevo)
        self._crear_nodos_guardia_nuevo()
        
        # NODO DE VIENTO (a 2/3 de la altura total)
        altura_total = max(h3a, h2a, h1a, self.hhg) if self.hhg > 0 else max(h3a, h2a, h1a)
        altura_v = (2/3) * altura_total
        self.nodos["V"] = NodoEstructural("V", (0.0, 0.0, altura_v), "viento")
        
        # NODO MEDIO (auxiliar) - solo si hay alturas válidas
        if altura_total > 0:
            altura_media = (h1a + altura_total) / 2
            self.nodos["MEDIO"] = NodoEstructural(
                "MEDIO", (0.0, 0.0, altura_media), "general"
            )
        
        # Actualizar nodes_key para compatibilidad
        self._actualizar_nodes_key()
        
        print(f"   ✅ Nodos creados: {len(self.nodos)} nodos totales")
    
    def _crear_nodos_simple_vertical(self, h1a, h2a, h3a):
        """Crea nodos para terna simple disposición vertical"""
        # C1_L, C2_L, C3_L = (lmen, h1a), (lmen, h2a), (lmen, h3a)
        self.nodos["C1_L"] = NodoEstructural(
            "C1_L", (self.lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C2_L"] = NodoEstructural(
            "C2_L", (self.lmen, 0.0, h2a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C3_L"] = NodoEstructural(
            "C3_L", (self.lmen, 0.0, h3a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
    
    def _crear_nodos_simple_triangular(self, h1a, h2a):
        """Crea nodos para terna simple disposición triangular"""
        # C1_R, C1_L, C2_R = (lmen, h1a), (-lmen, h1a), (lmen, h2a)
        self.nodos["C1_R"] = NodoEstructural(
            "C1_R", (self.lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C1_L"] = NodoEstructural(
            "C1_L", (-self.lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C2_R"] = NodoEstructural(
            "C2_R", (self.lmen, 0.0, h2a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
    
    def _crear_nodos_doble_vertical(self, h1a, h2a, h3a):
        """Crea nodos para terna doble disposición vertical"""
        # Lado derecho: C1_R, C2_R, C3_R = (lmen, h1a), (lmen, h2a), (lmen, h3a)
        # Lado izquierdo: C1_L, C2_L, C3_L = (-lmen, h1a), (-lmen, h2a), (-lmen, h3a)
        self.nodos["C1_R"] = NodoEstructural("C1_R", (self.lmen, 0.0, h1a), "conductor",
                                      self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2_R"] = NodoEstructural("C2_R", (self.lmen, 0.0, h2a), "conductor",
                                      self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3_R"] = NodoEstructural("C3_R", (self.lmen, 0.0, h3a), "conductor",
                                      self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        
        self.nodos["C1_L"] = NodoEstructural("C1_L", (-self.lmen, 0.0, h1a), "conductor",
                                      self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2_L"] = NodoEstructural("C2_L", (-self.lmen, 0.0, h2a), "conductor",
                                      self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3_L"] = NodoEstructural("C3_L", (-self.lmen, 0.0, h3a), "conductor",
                                      self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
    
    def _crear_nodos_doble_triangular(self, h1a, h2a):
        """Crea nodos para terna doble disposición triangular CORREGIDO"""
        print(f"   📐 Creando nodos para terna doble triangular:")
        print(f"      - h1a: {h1a:.2f}m, h2a: {h2a:.2f}m")
        print(f"      - lmen: {self.lmen:.2f}m, lmen2c: {self.lmen2c:.2f}m")
        
        # Nivel inferior (h1a): 4 conductores
        # Lado derecho: dos conductores en h1a
        self.nodos["C1_R"] = NodoEstructural(
            "C1_R", (self.lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C2_R"] = NodoEstructural(
            "C2_R", (self.lmen2c, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        
        # Lado izquierdo: dos conductores en h1a
        self.nodos["C1_L"] = NodoEstructural(
            "C1_L", (-self.lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C2_L"] = NodoEstructural(
            "C2_L", (-self.lmen2c, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        
        # Nivel superior (h2a): 2 conductores (uno por cada lado)
        self.nodos["C3_R"] = NodoEstructural(
            "C3_R", (self.lmen, 0.0, h2a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C3_L"] = NodoEstructural(
            "C3_L", (-self.lmen, 0.0, h2a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        
        print(f"      - Nodos creados: 6 conductores (4 en h1a, 2 en h2a)")
    
    def _crear_nodos_horizontal_default(self, altura, s_estructura=None, D_fases=None, theta_max=None):
        """Crea nodos para configuración horizontal con nueva lógica"""
        # Obtener parámetros necesarios
        h1a = altura
        s_estructura = s_estructura if s_estructura is not None else self.dimensiones.get('s_estructura', 0.5)
        D_fases = D_fases if D_fases is not None else self.dimensiones.get('D_fases', 1.5)
        theta_max = theta_max if theta_max is not None else self.dimensiones.get('theta_max', 0.0)
        print(f"   🔍 DEBUG _crear_nodos_horizontal: s_estructura={s_estructura:.3f}, D_fases={D_fases:.3f}, theta_max={theta_max:.2f}, Lk={self.lk}")
        
        # Calcular distancias
        dist_columna_x = max(self.lk * math.sin(math.radians(theta_max)) + s_estructura, D_fases / 2)
        print(f"   🔍 DEBUG: Lk*sin(theta)={self.lk * math.sin(math.radians(theta_max)):.3f}, dist_columna_x={dist_columna_x:.3f}")
        dist_conductor_x = dist_columna_x + self.lk * math.sin(math.radians(theta_max)) + s_estructura + self.ancho_cruceta/2
        dist_conductor_final = max(D_fases, dist_conductor_x)
        
        # 1. Nodo Y1 a altura h1a - 2*Lk (estructural)
        altura_y1 = h1a - 2*self.lk
        self.nodos["Y1"] = NodoEstructural("Y1", (0.0, 0.0, altura_y1), "general")
        
        # 2. Nodos Y2 y Y3 a altura h1a - Lk, defasados en x (estructurales)
        self.nodos["Y2"] = NodoEstructural("Y2", (dist_columna_x, 0.0, h1a - self.lk), "general")
        self.nodos["Y3"] = NodoEstructural("Y3", (-dist_columna_x, 0.0, h1a - self.lk), "general")
        
        # 3. Nodos Y4 y Y5 en misma posición X que Y2 y Y3, pero a altura h1a (estructurales)
        self.nodos["Y4"] = NodoEstructural("Y4", (dist_columna_x, 0.0, h1a), "general")
        self.nodos["Y5"] = NodoEstructural("Y5", (-dist_columna_x, 0.0, h1a), "general")
        
        # 4. Nodos de conductores C1, C2, C3 (todos a altura h1a)
        self.nodos["C1"] = NodoEstructural("C1", (dist_conductor_final, 0.0, h1a), "conductor",
                                  self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2"] = NodoEstructural("C2", (0.0, 0.0, h1a), "conductor",
                                  self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3"] = NodoEstructural("C3", (-dist_conductor_final, 0.0, h1a), "conductor",
                                  self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        
        print(f"   📍 Horizontal: C1=({dist_conductor_final:.2f}, {h1a:.2f}), C2=(0, {h1a:.2f}), C3=({-dist_conductor_final:.2f}, {h1a:.2f})")
        print(f"   📍 Columnas: Y2=({dist_columna_x:.2f}, {h1a-self.lk:.2f}), Y3=({-dist_columna_x:.2f}, {h1a-self.lk:.2f})")
        print(f"   📍 Estructura: BASE→Y1→Y2→Y4, Y1→Y3→Y5")
    
    def _crear_nodos_guardia_nuevo(self):
        """Crea nodos para cables de guardia según nueva lógica CORREGIDO"""
        if self.cant_hg == 0:
            print(f"   🚫 No hay cable guardia (CANT_HG = 0)")
            return
        
        # Primero crear el nodo TOP en (0, 0, hhg) - SOLO si NO hay guardia centrado
        crear_top = True
        
        if self.cant_hg == 1 and self.hg_centrado:
            # Guardia centrado: HG1 en (0, 0, hhg), NO se crea TOP
            self.nodos["HG1"] = NodoEstructural(
                "HG1", (0.0, 0.0, self.hhg), "guardia",
                self.cable_guardia1, self.alpha_quiebre, self.tipo_fijacion_base
            )
            crear_top = False  # No crear TOP para guardia centrado
            print(f"   🛡️  Cable guardia centrado: HG1 en (0, {self.hhg:.2f}) - SIN TOP")
        
        elif self.cant_hg == 1 and not self.hg_centrado:
            # Guardia no centrado: crear TOP y HG1 en (lmenhg, 0, hhg)
            self.nodos["TOP"] = NodoEstructural(
                "TOP", (0.0, 0.0, self.hhg), "general"
            )
            self.nodos["HG1"] = NodoEstructural(
                "HG1", (self.phg1[0], 0.0, self.phg1[1]), "guardia",
                self.cable_guardia1, self.alpha_quiebre, self.tipo_fijacion_base
            )
            print(f"   🛡️  Cable guardia no centrado: TOP en (0, {self.hhg:.2f}), HG1 en ({self.phg1[0]:.2f}, {self.phg1[1]:.2f})")
        
        elif self.cant_hg == 2:
            # Dos cables guardia: crear TOP y HG1, HG2
            self.nodos["TOP"] = NodoEstructural(
                "TOP", (0.0, 0.0, self.hhg), "general"
            )
            # HG1 (derecha, x+) usa cable_guardia1
            self.nodos["HG1"] = NodoEstructural(
                "HG1", (self.phg1[0], 0.0, self.phg1[1]), "guardia",
                self.cable_guardia1, self.alpha_quiebre, self.tipo_fijacion_base
            )
            # HG2 (izquierda, x-) usa cable_guardia2 si existe, sino cable_guardia1
            cable_hg2 = self.cable_guardia2 if self.cable_guardia2 else self.cable_guardia1
            self.nodos["HG2"] = NodoEstructural(
                "HG2", (self.phg2[0], 0.0, self.phg2[1]), "guardia",
                cable_hg2, self.alpha_quiebre, self.tipo_fijacion_base
            )
            print(f"   🛡️  Dos cables guardia: TOP en (0, {self.hhg:.2f}), HG1 en ({self.phg1[0]:.2f}, {self.phg1[1]:.2f}), HG2 en ({self.phg2[0]:.2f}, {self.phg2[1]:.2f})")
            if self.cable_guardia2:
                print(f"      - HG1: {self.cable_guardia1.nombre}, HG2: {self.cable_guardia2.nombre}")
    
    def _actualizar_nodes_key(self):
        """Actualiza el diccionario nodes_key para compatibilidad"""
        self.nodes_key = {}
        for nombre, nodo in self.nodos.items():
            self.nodes_key[nombre] = list(nodo.coordenadas)
    
    # ================= MÉTODOS DE ACCESO =================
    
    def obtener_parametros_cabezal(self):
        """Devuelve el DataFrame con todos los parámetros del cabezal"""
        return self.parametros_cabezal
    
    def obtener_nodes_key(self):
        """Devuelve el diccionario de nodos en formato compatible"""
        return self.nodes_key
    
    def listar_nodos(self):
        """Lista todos los nodos de la estructura con nombres corregidos"""
        print(f"\n📋 NODOS DE LA ESTRUCTURA ({len(self.nodos)} nodos):")
        print("=" * 80)
        
        # Ordenar nodos por tipo y luego por nombre
        tipos_orden = ["base", "cruce", "conductor", "guardia", "general", "viento"]
        
        for tipo in tipos_orden:
            nodos_tipo = [(nombre, nodo) for nombre, nodo in self.nodos.items() 
                         if nodo.tipo_nodo == tipo]
            if nodos_tipo:
                print(f"\n{tipo.upper()}:")
                for nombre, nodo in sorted(nodos_tipo, key=lambda x: x[0]):
                    x, y, z = nodo.coordenadas
                    cable_info = f" - {nodo.cable_asociado.nombre}" if nodo.cable_asociado else ""
                    print(f"  {nombre}: ({x:.3f}, {y:.3f}, {z:.3f}){cable_info}")
    
    def obtener_nodo(self, nombre_nodo):
        """Obtiene un nodo por nombre"""
        return self.nodos.get(nombre_nodo)
    
    def obtener_nodos_por_tipo(self, tipo):
        """Obtiene todos los nodos de un tipo específico"""
        return [nodo for nodo in self.nodos.values() if nodo.tipo_nodo == tipo]
    
    def info_estructura(self):
        """Devuelve información completa de la estructura"""
        tipo_detallado = f"{self.tipo_estructura} - {self.disposicion} - {self.terna}"
        
        info = {
            "Tipo de estructura": tipo_detallado,
            "Tensión nominal": f"{self.tension_nominal} kV",
            "Zona": self.zona_estructura,
            "Disposición": self.disposicion,
            "Terna": self.terna,
            "Cables guardia": self.cant_hg,
            "Ángulo quiebre": f"{self.alpha_quiebre}°",
            "Tipo fijación": self.tipo_fijacion_base,
            "Longitud cadena (Lk)": f"{self.lk:.2f} m",
            "Total nodos": len(self.nodos),
            "Nodos conductor": len(self.obtener_nodos_por_tipo("conductor")),
            "Nodos guardia": len(self.obtener_nodos_por_tipo("guardia")),
            "Altura total": f"{self.dimensiones.get('altura_total', 0):.2f} m",
            "Cable guardia centrado": "Sí" if self.hg_centrado else "No",
            "Ángulo apantallamiento": f"{self.ang_apantallamiento}°"
        }
        
        # Agregar información de ajuste por altura si aplica
        if self.ajustar_por_altura_msnm:
            info["Ajuste por altura MSNM"] = f"Sí ({self.metodo_altura_msnm})"
            info["Altura MSNM"] = f"{self.altura_msnm} m"
            Ka = self.dimensiones.get('Ka', 1.0)
            if Ka != 1.0:
                info["Coef. ajuste altura (Ka)"] = f"{Ka:.3f}"
        
        return info
    
    def imprimir_datos_dimensionamiento(self, vano, flecha_max_conductor, flecha_max_guardia):
        """Imprime en consola los datos de dimensionamiento"""
        
        print(f"\n📐 DIMENSIONES MÍNIMAS - {self.zona_estructura.upper()} - {self.tension_nominal}kV - {self.tipo_estructura.upper()}")
        
        # Agregar información de ajuste por altura MSNM si aplica
        if self.ajustar_por_altura_msnm:
            print(f"   (AJUSTADO POR ALTURA MSNM: {self.altura_msnm}m - Método: {self.metodo_altura_msnm})")
        
        print(f"{'Parámetro':<50} {'Valor':<12} {'Unidad':<10}")
        print("-" * 80)
        
        # Obtener valores
        theta_max = self.dimensiones.get('theta_max', 0.0)
        D_fases = self.dimensiones.get('D_fases', 0.0)
        s_estructura = self.dimensiones.get('s_estructura', 0.0)
        Dhg = self.dimensiones.get('Dhg', 0.0)
        b = self.dimensiones.get('b', 0.0)
        h_base_electrica = self.dimensiones.get('h_base_electrica', 0.0)
        Ka = self.dimensiones.get('Ka', 1.0)  # ← NUEVO
        
        # Agregar Ka a los parámetros a mostrar
        params = [
            ("Tipo de estructura", self.tipo_estructura, ""),
            ("TERNA", self.terna, ""),
            ("Disposición", self.disposicion, ""),
            ("Tensión nominal (Vn)", f"{self.tension_nominal:.1f}", "kV"),
            ("Tensión máxima (Vm)", f"{self.tension_maxima:.1f}", "kV"),
        ]
        
        # Solo mostrar Ka si es diferente de 1.0
        if Ka != 1.0:
            params.append(("Coef. ajuste altura (Ka)", f"{Ka:.3f}", ""))
        
        # Continuar con el resto de parámetros...
        params.extend([
            ("Altura mínima sobre terreno (a)", f"{self.ALTURAS_MINIMAS_TERRENO.get(self.zona_estructura, 5.90):.2f}", "m"),
            ("Componente eléctrico (b)", f"{b:.2f}", "m"),
            ("Altura base eléctrica (a+b)", f"{h_base_electrica:.2f}", "m"),
            ("Altura mínima cable", f"{self.altura_minima_cable:.2f}", "m"),
            ("Ángulo declinación máximo", f"{theta_max:.1f}", "°"),
            ("Coeficiente k", f"{self.dimensiones.get('k', 0):.2f}", ""),
            ("Distancia mín. entre fases (D)", f"{D_fases:.2f}", "m"),
            ("Distancia mín. guardia-fase (Dhg)", f"{Dhg:.2f}", "m"),
            ("Distancia mín. fase-estructura (s)", f"{s_estructura:.2f}", "m"),
            ("Altura adicional libre (HADD)", f"{self.hadd:.2f}", "m"),
            ("Distancia adicional vertical entre fases", f"{self.hadd_entre_amarres:.2f}", "m"),
            ("Longitud cadena (Lk)", f"{self.lk:.2f}", "m"),
            ("", "", ""),
            ("Alturas de Sujeción", "", ""),
            ("Primer amarre (h1a)", f"{self.dimensiones.get('h1a', 0):.2f}", "m"),
            ("Segundo amarre (h2a)", f"{self.dimensiones.get('h2a', 0):.2f}", "m"),
            ("Tercer amarre (h3a)", f"{self.dimensiones.get('h3a', 0):.2f}", "m"),
            ("Cable guardia (hhg)", f"{self.dimensiones.get('hhg', 0):.2f}", "m"),
            ("Longitud ménsula conductor (lmen)", f"{self.dimensiones.get('lmen', 0):.2f}", "m"),
            ("Longitud ménsula conductor 2 (lmen2c)", f"{self.dimensiones.get('lmen2c', 0):.2f}", "m"),
            ("Longitud ménsula guardia (lmenhg)", f"{self.dimensiones.get('lmenhg', 0):.2f} {'(CENTRADO)' if self.dimensiones.get('lmenhg', 0) == 0 else ''}", "m"),
            ("Posición conductor más alto", f"({self.dimensiones.get('pcma_x', 0):.2f}, {self.dimensiones.get('pcma_y', 0):.2f})", "m"),
            ("Altura total", f"{self.dimensiones.get('altura_total', 0):.2f}", "m")
        ])
        
        for param, val, unit in params:
            if param == "":
                print("-" * 80)
            else:
                print(f"{param:<50} {val:<12} {unit:<10}")
        
        # CÁLCULO DE APANTALLAMIENTO
        print(f"\n🛡️  CÁLCULO DE APANTALLAMIENTO - TERNA {self.terna}")
        print(f"{'Parámetro':<40} {'Valor':<8} {'Unidad':<10}")
        print("-" * 60)
        
        x_pcma = self.dimensiones.get('pcma_x', 0)
        y_pcma = self.dimensiones.get('pcma_y', 0)
        hhg = self.dimensiones.get('hhg', 0)
        distancia_vertical = hhg - y_pcma
        
        if self.cant_hg == 0:
            print("   No hay cable guardia (CANT_HG = 0)")
        elif self.cant_hg == 1 and self.hg_centrado:
            distancia_horizontal = x_pcma
            angulo_apant = math.degrees(math.atan(distancia_horizontal / distancia_vertical))
            distancia_diagonal = math.sqrt(distancia_horizontal**2 + distancia_vertical**2)
            
            apant_params = [
                ("Tipo de terna", self.terna, ""), 
                ("Cant. cables guardia", f"{self.cant_hg}", ""),
                ("Cable guardia", "CENTRADO", ""),
                ("Altura conductor más alto", f"{y_pcma:.2f}", "m"),
                ("Altura cable guardia", f"{hhg:.2f}", "m"), 
                ("Distancia vertical", f"{distancia_vertical:.2f}", "m"),
                ("Distancia horizontal", f"{distancia_horizontal:.2f}", "m"),
                ("Ángulo apantallamiento real", f"{angulo_apant:.1f}", "°"),
                ("Distancia diagonal", f"{distancia_diagonal:.2f}", "m"),
                ("Distancia mínima requerida (Dhg)", f"{Dhg:.2f}", "m"),
                ("Cumple ángulo 30°", "✅ Sí" if angulo_apant <= 30 else "❌ No", ""),
                ("Cumple distancia mínima", "✅ Sí" if distancia_diagonal >= Dhg else "❌ No", "")
            ]
        elif self.cant_hg == 1 and not self.hg_centrado:
            x_hg = self.dimensiones.get('phg1_x', 0)
            distancia_horizontal = abs(x_hg - x_pcma)
            angulo_apant = math.degrees(math.atan(distancia_horizontal / distancia_vertical))
            distancia_diagonal = math.sqrt(distancia_horizontal**2 + distancia_vertical**2)
            
            apant_params = [
                ("Tipo de terna", self.terna, ""), 
                ("Cant. cables guardia", f"{self.cant_hg}", ""),
                ("Cable guardia", "NO CENTRADO", ""),
                ("Altura conductor más alto", f"{y_pcma:.2f}", "m"),
                ("Altura cable guardia", f"{hhg:.2f}", "m"), 
                ("Distancia vertical", f"{distancia_vertical:.2f}", "m"),
                ("Distancia horizontal", f"{distancia_horizontal:.2f}", "m"),
                ("Ángulo apantallamiento real", f"{angulo_apant:.1f}", "°"),
                ("Distancia diagonal", f"{distancia_diagonal:.2f}", "m"),
                ("Distancia mínima requerida (Dhg)", f"{Dhg:.2f}", "m"),
                ("Cumple ángulo 30°", "✅ Sí" if angulo_apant <= 30 else "❌ No", ""),
                ("Cumple distancia mínima", "✅ Sí" if distancia_diagonal >= Dhg else "❌ No", "")
            ]
        elif self.cant_hg == 2:
            x_hg1 = self.dimensiones.get('phg1_x', 0)
            x_hg2 = self.dimensiones.get('phg2_x', 0)
            
            # Usar la menor distancia horizontal (la más crítica)
            distancia_horizontal1 = abs(x_hg1 - x_pcma)
            distancia_horizontal2 = abs(x_hg2 - x_pcma)
            distancia_horizontal = min(distancia_horizontal1, distancia_horizontal2)
            
            angulo_apant = math.degrees(math.atan(distancia_horizontal / distancia_vertical))
            distancia_diagonal = math.sqrt(distancia_horizontal**2 + distancia_vertical**2)
            
            apant_params = [
                ("Tipo de terna", self.terna, ""), 
                ("Cant. cables guardia", f"{self.cant_hg}", ""),
                ("Altura conductor más alto", f"{y_pcma:.2f}", "m"),
                ("Altura cable guardia", f"{hhg:.2f}", "m"), 
                ("Distancia vertical", f"{distancia_vertical:.2f}", "m"),
                ("Distancia horizontal (mín)", f"{distancia_horizontal:.2f}", "m"),
                ("Ángulo apantallamiento real", f"{angulo_apant:.1f}", "°"),
                ("Distancia diagonal", f"{distancia_diagonal:.2f}", "m"),
                ("Distancia mínima requerida (Dhg)", f"{Dhg:.2f}", "m"),
                ("Cumple ángulo 30°", "✅ Sí" if angulo_apant <= 30 else "❌ No", ""),
                ("Cumple distancia mínima", "✅ Sí" if distancia_diagonal >= Dhg else "❌ No", "")
            ]
        else:
            apant_params = [("Configuración no soportada", "", "")]
        
        for param, val, unit in apant_params: 
            print(f"{param:<40} {val:<8} {unit:<10}")

        print(f"\nVariables guardadas: h1a, h2a, h3a, hhg, lmen, lmen2c, lmenhg, D_fases, s_estructura, Dhg, nodes_key")
    
    def guardar_resultados_geometria(self, folder):
        """Guarda los resultados geométricos en archivos CSV"""
        import os
        
        print(f"\n💾 GUARDANDO RESULTADOS GEOMÉTRICOS...")
        os.makedirs(folder, exist_ok=True)
        
        # 1. Guardar nodes_key
        df_nodos = pd.DataFrame(self.nodes_key)
        ruta_nodos = f"{folder}/6_{self.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_').lower()}_NODOS_POO.csv"
        df_nodos.to_csv(ruta_nodos, index=False, encoding='utf-8')
        print(f"✅ Nodos guardados: {ruta_nodos}")
        
        # 2. Guardar dimensiones
        df_dimensiones = pd.DataFrame([self.dimensiones])
        ruta_dimensiones = f"{folder}/7_{self.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_').lower()}_DIMENSIONES_POO.csv"
        df_dimensiones.to_csv(ruta_dimensiones, index=False, encoding='utf-8')
        print(f"✅ Dimensiones guardadas: {ruta_dimensiones}")
        
        # 3. Guardar información de estructura
        info_df = pd.DataFrame([self.info_estructura()])
        ruta_info = f"{folder}/9_{self.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_').lower()}_INFO_POO.csv"
        info_df.to_csv(ruta_info, index=False, encoding='utf-8')
        print(f"✅ Información guardada: {ruta_info}")
        
        print(f"✅ Resultados geométricos guardados en: {folder}")

    def _ajustar_lmenhg_iterativo(self, Dhg, h1a, h2a, h3a, lmen, lmen2c, dist_reposicionar_hg=0.1, s_estructura=None, D_fases=None, theta_max=None):
        """
        Ajusta lmenhg con la nueva lógica:
        1. Primero: ningún conductor descubierto (diff >= 0)
        2. Segundo: si todos cubiertos y el cable más alto tiene diff > dist_reposicionar_hg,
        reducir lmenhg hasta cumplir dist_reposicionar_hg o antes de descubrir otro cable.
        3. dist_reposicionar_hg solo aplica al cable más alto.
        """
        # 1. Solo ajustar para guardias no centrados
        if self.cant_hg == 0 or (self.cant_hg == 1 and self.hg_centrado):
            return
        
        # 2. Calcular posiciones de conductores de la derecha (x > 0)
        posiciones = []
        ajuste_lk = self.lk
        
        # Configuración triangular doble
        if self.disposicion == "triangular" and self.terna == "Doble":
            # Ordenar por altura (y) para identificar el más alto
            posiciones.append((lmen, h1a - ajuste_lk, "C1_R"))    # Más bajo
            posiciones.append((lmen2c, h1a - ajuste_lk, "C2_R"))  # Medio
            posiciones.append((lmen, h2a - ajuste_lk, "C3_R"))    # Más alto
        
        # Configuración horizontal simple
        elif self.disposicion == "horizontal" and self.terna == "Simple":
            # Usar parámetros pasados o valores por defecto
            s_estructura_val = s_estructura if s_estructura is not None else 0.5
            D_fases_val = D_fases if D_fases is not None else 1.5
            theta_max_val = theta_max if theta_max is not None else 0.0
            dist_columna_x = max(self.lk * math.sin(math.radians(theta_max_val)) + s_estructura_val, D_fases_val / 2)
            dist_conductor_final = max(D_fases_val, dist_columna_x + self.lk * math.sin(math.radians(theta_max_val)) + s_estructura_val + self.ancho_cruceta/2)
            
            print(f"   🔍 DEBUG ajuste: dist_conductor_final={dist_conductor_final:.3f}m")
            # Solo verificar conductor del lado derecho (C1) - HG1 lo cubre
            # HG2 cubre C3 por simetría
            posiciones.append((dist_conductor_final, h1a - ajuste_lk, "C1"))  # Conductor derecho
        
        # Si no hay posiciones (otra configuración), salir
        if not posiciones:
            print(f"   ⏭️  Ajuste iterativo no implementado para: {self.disposicion} {self.terna}")
            return
        
        # Identificar el conductor más alto (mayor y)
        posiciones_sorted = sorted(posiciones, key=lambda item: item[1])
        conductor_mas_alto = posiciones_sorted[-1]  # El último es el más alto
        otros_conductores = posiciones_sorted[:-1]  # Los demás
        
        print(f"   🔧 Verificando {len(posiciones)} conductores del lado derecho...")
        print(f"   - Conductor más alto: {conductor_mas_alto[2]} en ({conductor_mas_alto[0]:.3f}, {conductor_mas_alto[1]:.3f})")
        
        # 3. Parámetros iniciales
        x_hg = self.lmenhg
        y_hg = self.hhg
        pendiente = -1 * math.tan(math.radians(90 - self.ang_apantallamiento))
        
        # 4. Función para calcular diff de un conductor
        def calcular_diff(x_hg_val, x_c, y_c):
            # Para horizontal: el guardia debe estar más afuera (x_hg >= x_c)
            if self.disposicion == "horizontal":
                # Si x_hg < x_c, el conductor no está cubierto
                if x_hg_val < x_c:
                    return -1.0  # Negativo = descubierto
                # Si x_hg >= x_c, calcular distancia vertical de cobertura
                return y_hg + pendiente * (x_c - x_hg_val) - y_c
            else:
                # Lógica original para triangular
                return y_hg + pendiente * (x_c - x_hg_val) - y_c
        
        # 5. Verificar condición inicial
        todos_cubiertos = True
        diffs = {}
        
        for x_c, y_c, nombre in posiciones:
            diff = calcular_diff(x_hg, x_c, y_c)
            diffs[nombre] = diff
            if diff < 0:
                todos_cubiertos = False
        
        print(f"   - Condición inicial: {'✅ TODOS CUBIERTOS' if todos_cubiertos else '❌ ALGUNO DESCUBIERTO'}")
        for nombre, diff in diffs.items():
            print(f"     {nombre}: diff = {diff:.3f}m")
        
        # 6. Si hay algún descubierto, AUMENTAR lmenhg para cubrirlo
        if not todos_cubiertos:
            print(f"   🚫 Hay conductores descubiertos. Ajustando para cubrir...")
            
            # Encontrar el conductor con mayor diff negativa (más descubierto)
            conductor_critico = min(posiciones, key=lambda item: calcular_diff(x_hg, item[0], item[1]))
            x_c_critico, y_c_critico, nombre_critico = conductor_critico
            
            # Calcular lmenhg_necesario para que diff = 0 para este conductor
            # 0 = y_hg + pendiente*(x_c - x_hg) - y_c
            # x_hg = x_c - (y_c - y_hg)/pendiente
            lmenhg_necesario = x_c_critico - (y_c_critico - y_hg) / pendiente
            
            # Asegurar que no sea menor que el mínimo
            lmenhg_necesario = max(lmenhg_necesario, self.long_mensula_min_guardia)
            
            print(f"   - Conductor más crítico: {nombre_critico}")
            print(f"   - lmenhg necesario para cubrirlo: {lmenhg_necesario:.3f}m (actual: {self.lmenhg:.3f}m)")
            
            # Verificar que al aplicar este lmenhg, no se descubran otros
            # (en teoría, aumentar lmenhg mejora la cobertura para todos)
            self.lmenhg = lmenhg_necesario
            
            # Recalcular diffs
            print(f"   📊 Diffs después del ajuste:")
            for x_c, y_c, nombre in posiciones:
                diff = calcular_diff(self.lmenhg, x_c, y_c)
                print(f"     {nombre}: diff = {diff:.3f}m {'✅' if diff >= 0 else '❌'}")
        
        # 7. Si todos están cubiertos, verificar sobrecobertura del cable más alto
        else:
            diff_mas_alto = calcular_diff(x_hg, conductor_mas_alto[0], conductor_mas_alto[1])
            
            if diff_mas_alto > dist_reposicionar_hg:
                print(f"   ⚠️  El conductor más alto tiene sobrecobertura: {diff_mas_alto:.3f}m > {dist_reposicionar_hg}m")
                print(f"   🔧 Reduciendo lmenhg para cumplir la tolerancia...")
                
                # Calcular lmenhg_objetivo para que diff_mas_alto = dist_reposicionar_hg
                # diff = y_hg + pendiente*(x_c - x_hg) - y_c = dist_reposicionar_hg
                # x_hg = x_c - (y_c - y_hg + dist_reposicionar_hg)/pendiente
                x_c_alto, y_c_alto, _ = conductor_mas_alto
                lmenhg_objetivo = x_c_alto - (y_c_alto - y_hg + dist_reposicionar_hg) / pendiente
                
                # Asegurar que no sea menor que el mínimo
                lmenhg_objetivo = max(lmenhg_objetivo, self.long_mensula_min_guardia)
                
                print(f"   - lmenhg objetivo para diff={dist_reposicionar_hg}: {lmenhg_objetivo:.3f}m")
                
                # Verificar que al reducir lmenhg, no descubramos otros cables
                # Para cada otro conductor, calcular su diff con el nuevo lmenhg
                problema_encontrado = False
                lmenhg_final = lmenhg_objetivo
                
                for x_c, y_c, nombre in otros_conductores:
                    diff_nuevo = calcular_diff(lmenhg_objetivo, x_c, y_c)
                    if diff_nuevo < 0:
                        # Este conductor quedaría descubierto, no podemos reducir tanto
                        # Calcular lmenhg máximo para este conductor (diff = 0)
                        lmenhg_max_para_este = x_c - (y_c - y_hg) / pendiente
                        lmenhg_max_para_este = max(lmenhg_max_para_este, self.long_mensula_min_guardia)
                        
                        if lmenhg_max_para_este > lmenhg_objetivo:
                            lmenhg_final = lmenhg_max_para_este
                            print(f"   - {nombre} quedaría descubierto si usamos {lmenhg_objetivo:.3f}m")
                            print(f"   - Usaremos lmenhg = {lmenhg_final:.3f}m (límite para {nombre})")
                            problema_encontrado = True
                            break
                
                if not problema_encontrado:
                    print(f"   ✅ Todos siguen cubiertos con lmenhg = {lmenhg_objetivo:.3f}m")
                    lmenhg_final = lmenhg_objetivo
                
                self.lmenhg = lmenhg_final
                
                # Verificar resultado final
                print(f"   📊 Diffs finales:")
                for x_c, y_c, nombre in posiciones:
                    diff = calcular_diff(self.lmenhg, x_c, y_c)
                    estado = "✅ OK" if diff >= 0 else "❌ DESCUBIERTO"
                    if nombre == conductor_mas_alto[2]:
                        estado += f" (diff={diff:.3f}m, objetivo ≤{dist_reposicionar_hg}m)"
                    print(f"     {nombre}: diff = {diff:.3f}m {estado}")
            
            else:
                print(f"   ✅ El conductor más alto ya cumple: diff={diff_mas_alto:.3f}m ≤ {dist_reposicionar_hg}m")
                print(f"   ✅ No se requiere ajuste de lmenhg")
        
        # 8. Actualizar posiciones de guardia
        if self.cant_hg == 1 and not self.hg_centrado:
            self.phg1 = (self.lmenhg, self.hhg)
        elif self.cant_hg == 2:
            self.phg1 = (self.lmenhg, self.hhg)
            self.phg2 = (-self.lmenhg, self.hhg)
        
        print(f"   🔧 lmenhg final: {self.lmenhg:.3f}m")

    def _calcular_coeficiente_altura(self):
        """
        Calcula el coeficiente de ajuste por altura sobre el nivel del mar (Ka)
        
        Returns:
            float: Coeficiente Ka
        """
        if not self.ajustar_por_altura_msnm:
            return 1.0
        
        if self.metodo_altura_msnm == "AEA 3%/300m":
            # Fórmula: Ka = 1 + 0.03 * (H - 1000) / 300
            # donde H es la altura sobre el nivel del mar en metros
            H = self.altura_msnm
            if H <= 1000:
                return 1.0
            else:
                Ka = 1.0 + 0.03 * (H - 1000) / 300
                return Ka
        else:
            raise ValueError(f"ERROR: Método de ajuste por altura '{self.metodo_altura_msnm}' no reconocido")