import math
from DatosPostes import *

class PostesHormigon:
    def __init__(self, factores_lrfd=None, sep_externa=0.4):
        self.datos = cargar_datos_postes()
        self.sep_externa = sep_externa

        # Factores LRFD configurables
        self.factores_lrfd = factores_lrfd or {
            'φ_tc': 0.8,
            'φ_tor': 0.85, 
            'CoefServ': 0.4,
            'KE': 1.0,
            'divisor_biposte_transversal': (8, 2),
            'divisor_biposte_longitudinal': (2, 8),
            'AJUSTE_RO_POR_HT': False
        }
        
        self.KC_dict = {
            "Suspensión Recta": 1.0,
            "Suspensión angular": 1.0,
            "Retención / Ret. Angular": 1.2,
            "Terminal": 1.2,
            "Especial": 1.3
        }
        
        # Tabla IRAM 1605-2008 - Resistencia mínima por transporte
        self.resistencia_minima_transporte = {
            (0,8):300, (8,10):400, (10,12):500, (12,13):600, (13,14):900,
            (14,16):1200, (16,17):1500, (17,18):1800, (18,19):2100, (19,20):2400,
            (20,21):2700, (21,22):3000, (22,23):3300, (23,24):3600, (24,25):3900,
            (25,26):4200, (26,27):4500, (27,28):4800, (28,29):4900, (29,30):5000
        }
        
        cargar_datos_postes()
        self._resultados_cache = {}
    
    def _encontrar_categoria(self, longitud):
        for cat_nombre, cat_datos in self.datos.items():
            min_long, max_long = cat_datos['rango']
            if min_long <= longitud <= max_long:
                return cat_nombre, cat_datos
        return None, None

    def _interpolar_lineal(self, x, x1, x2, y1, y2):
        """Interpolación lineal entre dos puntos"""
        if x1 == x2:
            return y1
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

    def buscar_postes(self, longitud, rotura):
        """Busca el diámetro y peso para una longitud y rotura dadas, interpolando si es necesario"""
        
        # Encontrar categoría
        cat_nombre, cat_datos = self._encontrar_categoria(longitud)
        if not cat_nombre:
            return None, None, f"Longitud {longitud}m fuera de rango"
        
        longitudes = cat_datos['longitudes']
        datos = cat_datos['datos']
        
        # Encontrar longitudes adyacentes
        long_inf = None
        long_sup = None
        
        for long in longitudes:
            if long <= longitud:
                long_inf = long
            if long >= longitud:
                long_sup = long
                break
        
        if long_inf is None or long_sup is None:
            return None, None, f"No se encontraron datos para longitud {longitud}m"
        
        # Encontrar roturas adyacentes para cada longitud
        def encontrar_roturas_adyacentes(datos_rotura, rotura_obj):
            roturas = sorted(datos_rotura.keys())
            rot_inf = None
            rot_sup = None
            
            for rot in roturas:
                if rot <= rotura_obj:
                    rot_inf = rot
                if rot >= rotura_obj:
                    rot_sup = rot
                    break
            
            return rot_inf, rot_sup
        
        # Para longitud inferior
        rot_inf_inf, rot_inf_sup = encontrar_roturas_adyacentes(datos, long_inf)
        # Para longitud superior  
        rot_sup_inf, rot_sup_sup = encontrar_roturas_adyacentes(datos, long_sup)
        
        if None in [rot_inf_inf, rot_inf_sup, rot_sup_inf, rot_sup_sup]:
            return None, None, f"No se pueden interpolar los datos para rotura {rotura}kg"
        
        # Interpolar en longitud inferior
        diam_inf = self._interpolar_lineal(rotura, rot_inf_inf, rot_inf_sup, 
                                         datos[rot_inf_inf][long_inf][0], 
                                         datos[rot_inf_sup][long_inf][0])
        peso_inf = self._interpolar_lineal(rotura, rot_inf_inf, rot_inf_sup,
                                         datos[rot_inf_inf][long_inf][1],
                                         datos[rot_inf_sup][long_inf][1])
        
        # Interpolar en longitud superior
        diam_sup = self._interpolar_lineal(rotura, rot_sup_inf, rot_sup_sup,
                                         datos[rot_sup_inf][long_sup][0],
                                         datos[rot_sup_sup][long_sup][0])
        peso_sup = self._interpolar_lineal(rotura, rot_sup_inf, rot_sup_sup,
                                         datos[rot_sup_inf][long_sup][1],
                                         datos[rot_sup_sup][long_sup][1])
        
        # Interpolar entre longitudes
        diam_final = self._interpolar_lineal(longitud, long_inf, long_sup, diam_inf, diam_sup)
        peso_final = self._interpolar_lineal(longitud, long_inf, long_sup, peso_inf, peso_sup)
        
        return round(diam_final, 1), round(peso_final, 0), "OK"

    def _calcular_dimensiones_geometricas(self, geometria, prioridad_dimensionado="altura_libre"):
        """Calcula y almacena las dimensiones geométricas según prioridad configurada"""
        Hl_original = geometria.dimensiones.get('altura_total', 0)
        
        if prioridad_dimensionado == "altura_libre":
            # PRIORIDAD: MANTENER ALTURA LIBRE (comportamiento original)
            Hl = Hl_original
            He_inicial = max(1.5, Hl * 0.1)
            Ht_inicial = Hl + He_inicial
            Ht_redondeada = math.ceil(Ht_inicial * 2) / 2
            He_final = Ht_redondeada - Hl
            
            # Verificación: empotramiento mínimo 10% de Ht_comercial
            empotramiento_minimo = Ht_redondeada * 0.10
            if He_final < empotramiento_minimo:
                print(f"⚠️  Ajustando empotramiento: {He_final:.2f}m < {empotramiento_minimo:.2f}m (10% de {Ht_redondeada}m)")
                He_final = empotramiento_minimo
                Ht_redondeada = Hl + He_final
                # Redondear nuevamente al medio metro superior
                Ht_redondeada = math.ceil(Ht_redondeada * 2) / 2
                # Recalcular He_final con el nuevo Ht_redondeada
                He_final = Ht_redondeada - Hl
                print(f"✅ Nuevo empotramiento: {He_final:.2f}m, Nueva longitud total: {Ht_redondeada:.1f}m")
            
            return {
                'Hl': Hl,
                'He_inicial': He_inicial,
                'Ht_inicial': Ht_inicial,
                'Ht_comercial': Ht_redondeada,
                'He_final': He_final,
                'prioridad': 'altura_libre',
                'Hl_original': Hl_original
            }
        
        else:  # PRIORIDAD_DIMENSIONADO == "longitud_total"
            # PRIORIDAD: MANTENER LONGITUD TOTAL COMERCIAL
            # Primero calcular la longitud total comercial basada en la altura libre original
            He_inicial = max(1.5, Hl_original * 0.1)
            Ht_inicial = Hl_original + He_inicial
            Ht_redondeada = math.ceil(Ht_inicial * 2) / 2
            
            # Verificar empotramiento mínimo y ajustar altura libre si es necesario
            empotramiento_minimo = Ht_redondeada * 0.10
            He_final = Ht_redondeada - Hl_original
            
            if He_final >= empotramiento_minimo:
                # Caso ideal: el empotramiento cumple con el mínimo
                Hl_final = Hl_original
                print(f"✅ Empotramiento cumple mínimo: {He_final:.2f}m ≥ {empotramiento_minimo:.2f}m")
            else:
                # Ajustar: reducir altura libre para aumentar empotramiento
                Hl_final = Ht_redondeada - empotramiento_minimo
                He_final = empotramiento_minimo
                print(f"⚠️  Ajustando altura libre: {Hl_original:.2f}m → {Hl_final:.2f}m")
                print(f"✅ Empotramiento ajustado: {He_final:.2f}m (10% de {Ht_redondeada}m)")
            
            return {
                'Hl': Hl_final,
                'He_inicial': He_inicial,
                'Ht_inicial': Ht_inicial,
                'Ht_comercial': Ht_redondeada,
                'He_final': He_final,
                'prioridad': 'longitud_total',
                'Hl_original': Hl_original,
                'Hl_ajustada': Hl_final != Hl_original
            }

    def _procesar_hipotesis_criticas(self, mecanica):
        """Procesa todas las hipótesis una sola vez y almacena resultados"""
        resultados = {}
        
        for nombre_hip, datos in mecanica.resultados_reacciones.items():
            Fx, Fy = datos['Tiro_X_daN'], datos['Tiro_Y_daN']
            codigo = nombre_hip.split('_')[-2] if len(nombre_hip.split('_')) >= 2 else nombre_hip
            
            resultados[nombre_hip] = {
                'codigo': codigo,
                'Fx': Fx,
                'Fy': Fy,
                'Fr_monoposte': math.sqrt(Fx**2 + Fy**2),
                'Fr_biposte_transversal': math.sqrt((Fx/8)**2 + (Fy/2)**2),
                'Fr_biposte_longitudinal': math.sqrt((Fx/2)**2 + (Fy/8)**2),
                'Fr_triposte': (1/9) * math.sqrt(Fx**2 + Fy**2)
            }
        
        return resultados

    def calcular_seleccion_postes(self, geometria, mecanica, FORZAR_N_POSTES=0, FORZAR_ORIENTACION="No", ANCHO_CRUCETA=0.2, PRIORIDAD_DIMENSIONADO="altura_libre", AJUSTE_RO_POR_HT=False, KE_estructura_ensayada=1.0):
        """
        Calcula la selección completa de postes basada en la estructura y configuraciones
        
        Args:
            geometria: Objeto EstructuraAEA_Geometria
            mecanica: Objeto EstructuraAEA_Mecanica
            PRIORIDAD_DIMENSIONADO: "altura_libre" (default) o "longitud_total"
                - "altura_libre": Mantiene altura libre, ajusta longitud total
                - "longitud_total": Mantiene longitud total, ajusta altura libre
        """
        print("🔧 SELECCIÓN DE POSTE - MÉTODO LRFD AEA 95301-2007")
        print("=" * 80)
        
        # ================= CONFIGURACIÓN =================
        self.FORZAR_N_POSTES = FORZAR_N_POSTES
        self.FORZAR_ORIENTACION = FORZAR_ORIENTACION
        self.ANCHO_CRUCETA = ANCHO_CRUCETA
        self.PRIORIDAD_DIMENSIONADO = PRIORIDAD_DIMENSIONADO
        self.AJUSTE_RO_POR_HT = AJUSTE_RO_POR_HT
        
        # Almacenar referencias a los objetos
        self.geometria = geometria
        self.mecanica = mecanica
        
        # Obtener datos de la geometría
        self.TIPO_ESTRUCTURA = geometria.tipo_estructura
        self.TENSION = geometria.tension_nominal
        
        # Factores LRFD
        φ_tc = self.factores_lrfd['φ_tc']
        φ_tor = self.factores_lrfd['φ_tor']
        CoefServ = self.factores_lrfd['CoefServ']
        KE = KE_estructura_ensayada
        KC = self.KC_dict.get(self.TIPO_ESTRUCTURA, 1.0)
        
        # ================= CALCULAR DIMENSIONES =================
        dimensiones = self._calcular_dimensiones_geometricas(geometria, PRIORIDAD_DIMENSIONADO)
        
        # ================= PROCESAR HIPÓTESIS =================
        resultados_hipotesis = self._procesar_hipotesis_criticas(mecanica)
        
        # Identificar hipótesis críticas
        hipotesis_A0 = None
        for nombre_hip, datos in resultados_hipotesis.items():
            if 'A0' in nombre_hip:
                hipotesis_A0 = nombre_hip
                break

        # Configuraciones a evaluar
        configs = ["Monoposte", "Biposte_TRANSVERSAL", "Biposte_LONGITUDINAL", "Triposte"]
        configuraciones = {config: {"Fr_max":0, "Fr_serv":0, "hip_max":"", "Fr_max_ajustado":0, "Fr_serv_ajustado":0} for config in configs}

        # Procesar todas las hipótesis
        for nombre_hip, datos in resultados_hipotesis.items():
            codigo = datos['codigo']
            
            for config in configs:
                if config == "Monoposte":
                    Fr = datos['Fr_monoposte']
                elif config == "Biposte_TRANSVERSAL":
                    Fr = datos['Fr_biposte_transversal']
                elif config == "Biposte_LONGITUDINAL":
                    Fr = datos['Fr_biposte_longitudinal']
                elif config == "Triposte":
                    Fr = datos['Fr_triposte']
                else:
                    Fr = 0
                
                if Fr > configuraciones[config]["Fr_max"] and 'A0' not in nombre_hip:
                    configuraciones[config]["Fr_max"] = Fr
                    configuraciones[config]["hip_max"] = codigo

        # Procesar hipótesis A0 para ELS
        if hipotesis_A0:
            datos_A0 = resultados_hipotesis[hipotesis_A0]
            
            for config in configs:
                if config == "Monoposte":
                    Fr_serv = datos_A0['Fr_monoposte']
                elif config == "Biposte_TRANSVERSAL":
                    Fr_serv = datos_A0['Fr_biposte_transversal']
                elif config == "Biposte_LONGITUDINAL":
                    Fr_serv = datos_A0['Fr_biposte_longitudinal']
                elif config == "Triposte":
                    Fr_serv = datos_A0['Fr_triposte']
                else:
                    Fr_serv = 0
                    
                configuraciones[config]["Fr_serv"] = Fr_serv

        # ================= AJUSTE DE RESISTENCIA =================
        if AJUSTE_RO_POR_HT:
            for config in configs:
                configuraciones[config]["Fr_max_ajustado"] = self._ajustar_tiro_altura_total(
                    configuraciones[config]["Fr_max"], dimensiones['Hl'], dimensiones['Ht_comercial'])
                configuraciones[config]["Fr_serv_ajustado"] = self._ajustar_tiro_altura_total(
                    configuraciones[config]["Fr_serv"], dimensiones['Hl'], dimensiones['Ht_comercial'])
        else:
            for config in configs:
                configuraciones[config]["Fr_max_ajustado"] = configuraciones[config]["Fr_max"]
                configuraciones[config]["Fr_serv_ajustado"] = configuraciones[config]["Fr_serv"]

        # ================= CALCULAR RESISTENCIAS =================
        for config in configs:
            # Resistencia requerida por ELU
            Rc_min = (KE * KC * configuraciones[config]["Fr_max_ajustado"]) / φ_tc
            
            # Resistencia requerida por ELS
            Rc_serv = configuraciones[config]["Fr_serv_ajustado"] / CoefServ if configuraciones[config]["Fr_serv_ajustado"] > 0 else 0
            
            # Resistencia mínima por transporte
            Rc_transp = self._obtener_resistencia_minima_transporte(dimensiones['Ht_comercial'])
            
            # Resistencia adoptada (máxima de los tres criterios)
            Rc_adopt = self._redondear_resistencia(max(Rc_min, Rc_serv, Rc_transp))
            
            configuraciones[config].update({
                'Rc_adopt_red': Rc_adopt, 
                'Rc_min': Rc_min, 
                'Rc_serv': Rc_serv, 
                'Rc_transp': Rc_transp
            })

        # ================= SELECCIÓN DE CONFIGURACIÓN =================
        if FORZAR_N_POSTES == 0:
            config_seleccionada = min(configuraciones.items(), key=lambda x: x[1]['Rc_adopt_red'])[0]
        else:
            config_map = {1: "Monoposte", 
                          2: "Biposte_TRANSVERSAL" if FORZAR_ORIENTACION == "Transversal" else "Biposte_LONGITUDINAL",
                          3: "Triposte"}
            config_seleccionada = config_map[FORZAR_N_POSTES]

        Rc_adopt_seleccionada = configuraciones[config_seleccionada]['Rc_adopt_red']
        
        # ================= ALMACENAR RESULTADOS EN CACHE =================
        self._resultados_cache = {
            'config_seleccionada': config_seleccionada,
            'dimensiones': dimensiones,
            'Rc_adopt': Rc_adopt_seleccionada,
            'configuraciones': configuraciones,
            'resultados_hipotesis': resultados_hipotesis,
            'hipotesis_A0': hipotesis_A0,
            'factores': {
                'φ_tc': φ_tc,
                'φ_tor': φ_tor,
                'CoefServ': CoefServ,
                'KE': KE,
                'KC': KC
            },
            'geometria': geometria,
            'mecanica': mecanica
        }

        return self._resultados_cache

    def _calcular_fuerza_equivalente(self, Fx, Fy, config):
        """Calcula fuerza equivalente según configuración de postes"""
        if config == "Monoposte": 
            return math.sqrt(Fx**2 + Fy**2)
        elif config == "Biposte_TRANSVERSAL": 
            return math.sqrt((Fx/8)**2 + (Fy/2)**2)
        elif config == "Biposte_LONGITUDINAL": 
            return math.sqrt((Fx/2)**2 + (Fy/8)**2)
        elif config == "Triposte": 
            return (1/9) * math.sqrt(Fx**2 + Fy**2)
        return 0

    def _ajustar_tiro_altura_total(self, Fr, Hl, Ht):
        """Ajusta el tiro a la altura total"""
        return Fr * (Hl / Ht) if Ht > 0 else Fr

    def _redondear_resistencia(self, valor, base=100):
        """Redondea resistencia al múltiplo de base superior"""
        return math.ceil(valor / base) * base

    def _obtener_resistencia_minima_transporte(self, longitud):
        """Obtiene resistencia mínima por transporte según longitud"""
        for rango, resistencia in self.resistencia_minima_transporte.items():
            if rango[0] < longitud <= rango[1]: 
                return resistencia
        return self.resistencia_minima_transporte[(29, 30)] if longitud > 30 else 0

    def buscar_postes_mejorado(self, longitud, rotura_requerida):
        """
        Búsqueda mejorada de postes con interpolación más robusta
        """
        # Primero buscar coincidencia exacta de longitud y rotura
        cat_nombre, cat_datos = self._encontrar_categoria(longitud)
        if cat_nombre:
            # Buscar en la categoría específica primero
            for rotura, datos_rotura in cat_datos['datos'].items():
                if rotura == rotura_requerida and longitud in datos_rotura:
                    diametro, peso = datos_rotura[longitud]
                    return diametro, peso, "OK (coincidencia exacta)"
        
        # Si no hay coincidencia exacta, buscar la rotura mínima que cumple
        mejor_diametro = None
        mejor_peso = None
        mejor_rotura = float('inf')
        
        cat_nombre, cat_datos = self._encontrar_categoria(longitud)
        if cat_nombre:
            for rotura, datos_rotura in cat_datos['datos'].items():
                if longitud in datos_rotura and rotura >= rotura_requerida and rotura < mejor_rotura:
                    mejor_rotura = rotura
                    mejor_diametro, mejor_peso = datos_rotura[longitud]
        
        if mejor_diametro is not None:
            return mejor_diametro, mejor_peso, f"OK (rotura {mejor_rotura} daN)"
        
        # Si no hay coincidencia exacta, usar interpolación mejorada
        return self._buscar_con_interpolacion_mejorada(longitud, rotura_requerida)

    def _buscar_con_interpolacion_mejorada(self, longitud, rotura):
        """Interpolación mejorada para casos sin coincidencia exacta - usa 2 puntos"""
        # Encontrar la categoría correcta
        cat_nombre, cat_datos = self._encontrar_categoria(longitud)
        if not cat_nombre:
            return None, None, f"Longitud {longitud}m fuera de rango"
        
        # Recolectar todos los puntos disponibles
        puntos = []
        for rot, datos_rot in cat_datos['datos'].items():
            for long, (diam, peso) in datos_rot.items():
                puntos.append((long, rot, diam, peso))
        
        if len(puntos) < 2:
            return None, None, "No hay suficientes datos para interpolación"
        
        # Ordenar por distancia euclidiana al punto deseado
        puntos.sort(key=lambda p: math.sqrt((p[0]-longitud)**2 + (p[1]-rotura)**2))
        
        # Tomar los 2 puntos más cercanos
        p1, p2 = puntos[:2]
        
        # Interpolación lineal simple entre los 2 puntos
        try:
            # Calcular pesos basados en distancia inversa
            d1 = math.sqrt((p1[0]-longitud)**2 + (p1[1]-rotura)**2)
            d2 = math.sqrt((p2[0]-longitud)**2 + (p2[1]-rotura)**2)
            
            # Evitar división por cero
            if d1 + d2 == 0:
                diam_interp = (p1[2] + p2[2]) / 2
                peso_interp = (p1[3] + p2[3]) / 2
            else:
                w1 = 1 / (d1 + 0.0001)  # Evitar división por cero
                w2 = 1 / (d2 + 0.0001)
                
                diam_interp = (w1 * p1[2] + w2 * p2[2]) / (w1 + w2)
                peso_interp = (w1 * p1[3] + w2 * p2[3]) / (w1 + w2)
            
            return round(diam_interp, 1), round(peso_interp, 0), "OK (interpolado)"
        except:
            return None, None, "Error en interpolación"

    def _estimar_diametro(self, resistencia):
        """Estima diámetro basado en resistencia requerida"""
        if resistencia <= 1000:
            return 170
        elif resistencia <= 2000:
            return 215
        elif resistencia <= 3000:
            return 260
        elif resistencia <= 4000:
            return 305
        else:
            return 350

    def _estimar_peso(self, longitud, diametro):
        """Estima peso basado en longitud y diámetro"""
        return round((longitud * diametro * 0.8) + 200)

    def imprimir_desarrollo_seleccion_postes(self):
        """Imprime el desarrollo completo de selección de postes usando cache"""
        if not self._resultados_cache:
            print("❌ No hay resultados de selección. Ejecutar calcular_seleccion_postes primero.")
            return
        
        resultados = self._resultados_cache
        geometria = resultados.get('geometria')
        mecanica = resultados.get('mecanica')
        
        if not geometria or not mecanica:
            print("❌ Objetos geometría o mecánica no disponibles en cache")
            return
        
        print("🔧 SELECCIÓN DE POSTE - MÉTODO LRFD AEA 95301-2007")
        print("=" * 80)
        
        # ================= DIMENSIONADO GEOMÉTRICO =================
        print("\n📐 DIMENSIONADO GEOMÉTRICO DEL POSTE")
        print("=" * 40)
        
        dimensiones = resultados['dimensiones']
        prioridad = dimensiones.get('prioridad', 'altura_libre')
        
        print(f"Prioridad de dimensionado: {prioridad.upper().replace('_', ' ')}")
        
        if prioridad == "altura_libre":
            print(f"Altura libre requerida (Hl): {dimensiones['Hl']:.2f} m")
            print(f"Empotramiento mínimo: {dimensiones['He_inicial']:.2f} m")
            print(f"Longitud total mínima: {dimensiones['Ht_inicial']:.2f} m")
            print(f"Longitud total comercial (Ht): {dimensiones['Ht_comercial']:.1f} m")
            print(f"Empotramiento final (He): {dimensiones['He_final']:.2f} m")
        else:  # longitud_total
            print(f"Altura libre original: {dimensiones['Hl_original']:.2f} m")
            if dimensiones.get('Hl_ajustada', False):
                print(f"Altura libre ajustada (Hl): {dimensiones['Hl']:.2f} m ← REDUCIDA")
            else:
                print(f"Altura libre final (Hl): {dimensiones['Hl']:.2f} m")
            print(f"Longitud total comercial (Ht): {dimensiones['Ht_comercial']:.1f} m (FIJA)")
            print(f"Empotramiento mínimo requerido: {dimensiones['Ht_comercial'] * 0.10:.2f} m")
            print(f"Empotramiento final (He): {dimensiones['He_final']:.2f} m")

        # ================= IDENTIFICACIÓN DE HIPÓTESIS CRÍTICAS =================
        print(f"\n🔍 IDENTIFICACIÓN DE HIPÓTESIS CRÍTICAS")
        print("=" * 40)
        
        # Buscar hipótesis de mayor solicitación en monoposte
        Fr_max_mono = 0
        hip_max_mono = None
        
        for nombre_hip, datos in resultados['resultados_hipotesis'].items():
            if datos['Fr_monoposte'] > Fr_max_mono and 'A0' not in nombre_hip:
                Fr_max_mono = datos['Fr_monoposte']
                hip_max_mono = datos['codigo']
        
        # Hipótesis A0
        Fr_A0 = 0
        if resultados['hipotesis_A0']:
            datos_A0 = resultados['resultados_hipotesis'][resultados['hipotesis_A0']]
            Fr_A0 = datos_A0['Fr_monoposte']
        
        print(f"  Estado de mayor solicitación: {hip_max_mono} (Fr = {Fr_max_mono:.1f} daN en Hl)")
        if Fr_A0 > 1.0:
            print(f"  Servicio: A0 (Fr = {Fr_A0:.1f} daN en Hl)")
        else:
            print(f"  Servicio: A0 (Fr = {Fr_A0:.1f} daN en Hl) (No hay componente angular)")

        # ================= AJUSTE DE RESISTENCIA =================
        if self.AJUSTE_RO_POR_HT:
            print(f"\n📏 AJUSTE DE RESISTENCIA PARA ALTURA TOTAL")
            print("=" * 45)
            print("Se ajustan las hipótesis críticas a la altura libre sumada al empotramiento, de la siguiente manera:")
            print("Frt = Frl × Hl/Ht")
            
            # Ajustar tiros
            Fr_max_ajustado = self._ajustar_tiro_altura_total(Fr_max_mono, dimensiones['Hl'], dimensiones['Ht_comercial'])
            Fr_A0_ajustado = self._ajustar_tiro_altura_total(Fr_A0, dimensiones['Hl'], dimensiones['Ht_comercial'])
            
            print(f"\nHIPÓTESIS CRÍTICAS, TIROS AJUSTADOS A ALTURA TOTAL:")
            print(f"  Estado de mayor solicitación: {hip_max_mono} (Frt = {Fr_max_ajustado:.1f} daN en Ht)")
            if Fr_A0_ajustado > 1.0:
                print(f"  Servicio: A0 (Frt = {Fr_A0_ajustado:.1f} daN en Ht)")
            else:
                print(f"  Servicio: A0 (Frt = {Fr_A0_ajustado:.1f} daN en Ht) (No hay componente angular)")
        else:
            print(f"\n⚠️  AJUSTE DE RESISTENCIA DESACTIVADO")
            print("=" * 45)
            print("Los tiros se utilizan directamente en altura libre (Hl) sin ajustar a altura total (Ht).")

        # ================= CONFIGURACIÓN =================
        config_seleccionada = resultados['config_seleccionada']
        if "Biposte" in config_seleccionada:
            print(f"\n🔧 CONFIGURACIÓN: BIPOSTE")
            print("=" * 40)
            
            if "TRANSVERSAL" in config_seleccionada:
                orientacion = "TRANSVERSAL"
            else:
                orientacion = "LONGITUDINAL"
                
            print(f"Orientación: {orientacion} {'(Forzada)' if self.FORZAR_ORIENTACION != 'No' else '(Automática)'}")
            print("\nECUACIONES PARA BIPOSTE:")
            print("  - Biposte Transversal: Fr = √[(Fx/8)² + (Fy/2)²]")
            print("  - Biposte Longitudinal: Fr = √[(Fx/2)² + (Fy/8)²]")
            
            # Obtener tiros para configuración seleccionada
            config_data = resultados['configuraciones'][config_seleccionada]
            print(f"\nTIROS AJUSTADOS PARA CONFIGURACIÓN BIPOSTE {orientacion}:")
            print(f"  Estado crítico: {config_data['hip_max']} (Frt = {config_data['Fr_max_ajustado']:.1f} daN)")
            print(f"  Servicio A0: (Frt = {config_data['Fr_serv_ajustado']:.1f} daN)")

        # AGREGAR ESTA SECCIÓN PARA TRIPOSTE
        elif "Triposte" in config_seleccionada:
            print(f"\n🔧 CONFIGURACIÓN: TRIPOSTE")
            print("=" * 40)
            print("Orientación: TRIANGULAR (Automática)")
            print("\nECUACIÓN PARA TRIPOSTE:")
            print("  Fr = (1/9) × √(Fx² + Fy²)")
            
            # Obtener tiros para configuración seleccionada
            config_data = resultados['configuraciones'][config_seleccionada]
            print(f"\nTIROS AJUSTADOS PARA CONFIGURACIÓN TRIPOSTE:")
            print(f"  Estado crítico: {config_data['hip_max']} (Frt = {config_data['Fr_max_ajustado']:.1f} daN")
            print(f"  Servicio A0: (Frt = {config_data['Fr_serv_ajustado']:.1f} daN")

        # ================= DETERMINACIÓN DE RESISTENCIA =================
        print(f"\n🛡️ DETERMINACIÓN DE LA RESISTENCIA TOTAL")
        print("=" * 50)
        print("Se emplea la ecuación siguiente (Método LRFD):")
        print("KE × KC × S ≤ φ × R")
        
        factores = resultados['factores']
        print(f"\nVALORES DE LOS FACTORES DE CARGA:")
        print(f"  KE (estructura ensayada) = {factores['KE']}")
        print(f"  KC ({self.TIPO_ESTRUCTURA}) = {factores['KC']}")
        
        print(f"\nVALORES DE LOS FACTORES DE RESISTENCIA:")  
        print(f"  φ tc (tiro en cima) = {factores['φ_tc']}")
        print(f"  φ tor (torsión) = {factores['φ_tor']}")
        print(f"  CS (servicio) = {factores['CoefServ']}")

        # ================= RESULTADO FINAL =================
        Rc_adopt = resultados['Rc_adopt']
        n_postes = 1 if "Monoposte" in config_seleccionada else 2 if "Biposte" in config_seleccionada else 3
        
        if "Biposte" in config_seleccionada:
            if "TRANSVERSAL" in config_seleccionada:
                orientacion_final = "TRANSVERSAL"
            else:
                orientacion_final = "LONGITUDINAL"
        elif "Triposte" in config_seleccionada:
            orientacion_final = "CUALQUIERA"
        else:
            orientacion_final = "N/A"
        
        codigo_postes = f"{n_postes} x {dimensiones['Ht_comercial']:.1f}m / Ro {Rc_adopt:.0f}daN"
        
        print(f"\nDe esta manera, y aplicando la ecuación con los factores, los resultados del cálculo son los siguientes:")
        print(f"  Tipo: {config_seleccionada} ({'FORZADA' if self.FORZAR_N_POSTES != 0 else 'ÓPTIMA'})")
        print(f"  Código: {codigo_postes}")
        print(f"  Orientación: {orientacion_final}")
        print(f"  Resistencia en cima: {Rc_adopt:.0f} daN")
        
        # Calcular resistencia a torsión
        Mz_max = max([datos['Reaccion_Mz_daN_m'] for datos in mecanica.resultados_reacciones.values()])
        Rt_min = (factores['KE'] * factores['KC'] * Mz_max) / factores['φ_tor'] if Mz_max > 0 else 0
        
        # Resistencia mínima a torsión según Rc_adopt (Norma IRAM 1605)
        if Rc_adopt <= 1200:
            Rt_min_torsion = 900
        elif Rc_adopt <= 1800:
            Rt_min_torsion = 1000
        else:
            Rt_min_torsion = 1275
        
        Rt_adopt = max(Rt_min, Rt_min_torsion)
        print(f"  Resistencia a torsión: {Rt_adopt:.0f} daN·m")
        print(f"  Empotramiento: {dimensiones['He_final']:.2f} m")

        # ================= VERIFICACIÓN DE HIPÓTESIS =================
        print(f"\n✅ Y se comprueba su aptitud para todas las hipótesis:")
        
        # Ordenar hipótesis: A0 primero, luego por orden alfabético
        hipotesis_ordenadas = []
        for nombre_hip, datos in resultados['resultados_hipotesis'].items():
            hipotesis_ordenadas.append((datos['codigo'], nombre_hip))
        
        hipotesis_ordenadas.sort(key=lambda x: ('A0' not in x[0], x[0]))
        
        for codigo, nombre_hip in hipotesis_ordenadas:
            datos = resultados['resultados_hipotesis'][nombre_hip]
            Fx, Fy = datos['Fx'], datos['Fy']
            Fr = self._calcular_fuerza_equivalente(Fx, Fy, config_seleccionada)
            
            # Usar Fr ajustado o sin ajustar según configuración
            if self.AJUSTE_RO_POR_HT:
                Fr_verificacion = self._ajustar_tiro_altura_total(Fr, dimensiones['Hl'], dimensiones['Ht_comercial'])
            else:
                Fr_verificacion = Fr
            
            if codigo == 'A0':
                # Verificación de servicio
                lado_izq = Fr_verificacion
                lado_der = factores['CoefServ'] * Rc_adopt
                resultado = "CUMPLE" if lado_izq <= lado_der else "NO CUMPLE"
                print(f"  A0 (Servicio): {lado_izq:.1f} ≤ {factores['CoefServ']} × {Rc_adopt:.0f} = {lado_der:.1f} → {resultado}")
            else:
                # Verificación de estado último
                lado_izq = factores['KE'] * factores['KC'] * Fr_verificacion
                lado_der = factores['φ_tc'] * Rc_adopt
                resultado = "CUMPLE" if lado_izq <= lado_der else "NO CUMPLE"
                print(f"  {codigo}: {factores['KE']} × {factores['KC']} × {Fr_verificacion:.1f} = {lado_izq:.1f} ≤ {factores['φ_tc']} × {Rc_adopt:.0f} = {lado_der:.1f} → {resultado}")

        # ================= INFORMACIÓN ADICIONAL =================
        print(f"\n📊 INFORMACIÓN ADICIONAL DEL CÁLCULO")
        print("=" * 50)
        
        config_data = resultados['configuraciones'][config_seleccionada]
        
        # Detalle de los criterios que gobernaron el diseño
        criterios = []
        if config_data['Rc_adopt_red'] == self._redondear_resistencia(config_data['Rc_min']): 
            criterios.append("LRFD")
        if config_data['Rc_adopt_red'] == self._redondear_resistencia(config_data['Rc_serv']): 
            criterios.append("Servicio")
        if config_data['Rc_adopt_red'] == self._redondear_resistencia(config_data['Rc_transp']): 
            criterios.append("Transporte")
        gobernado_por = "+".join(criterios) if criterios else "N/A"
        
        print(f"Criterio gobernante: {gobernado_por}")
        print(f"Resistencia por LRFD: {config_data['Rc_min']:.0f} daN")
        print(f"Resistencia por Servicio: {config_data['Rc_serv']:.0f} daN") 
        print(f"Resistencia por Transporte: {config_data['Rc_transp']:.0f} daN")
        
        # Resistencia a torsión
        print(f"\nResistencia a torsión calculada: {Rt_min:.0f} daN·m")
        print(f"Resistencia mínima a torsión por Rc_adopt: {Rt_min_torsion:.0f} daN·m")
        print(f"Resistencia a torsión adoptada: {Rt_adopt:.0f} daN·m")

        # ================= TABLA COMPARATIVA =================
        print(f"\n📈 TABLA COMPARATIVA DE CONFIGURACIONES")
        print("=" * 100)
        print(f"{'Configuración':<22} {'Rc_LRFD':<8} {'Rc_Serv':<8} {'Rc_Transp':<9} {'Rc_Final':<9} {'Gobernado por':<12}")
        print("=" * 100)
        
        for config in ["Monoposte", "Biposte_TRANSVERSAL", "Biposte_LONGITUDINAL", "Triposte"]:
            if config in resultados['configuraciones']:
                datos = resultados['configuraciones'][config]
                criterios = []
                if datos['Rc_adopt_red'] == self._redondear_resistencia(datos['Rc_min']): criterios.append("LRFD")
                if datos['Rc_adopt_red'] == self._redondear_resistencia(datos['Rc_serv']): criterios.append("Servicio")
                if datos['Rc_adopt_red'] == self._redondear_resistencia(datos['Rc_transp']): criterios.append("Transporte")
                gobernado_por = "+".join(criterios) if criterios else "N/A"
                
                seleccion = f"← FORZADA" if config == config_seleccionada and self.FORZAR_N_POSTES != 0 else f"← ÓPTIMA" if config == config_seleccionada else ""
                print(f"{config:<22} {datos['Rc_min']:<8.0f} {datos['Rc_serv']:<8.0f} {datos['Rc_transp']:<9.0f} {datos['Rc_adopt_red']:<9.0f} {gobernado_por:<12} {seleccion}")

        # ================= ESTIMACIÓN DE POSTE =================
        print(f"\n📏 ESTIMACIÓN DE POSTE DE HORMIGÓN")
        
        # BUSCAR EL POSTE SOLO AQUÍ, después de tener la rotura final
        diametro, peso, mensaje = self.buscar_postes_mejorado(
            dimensiones['Ht_comercial'], 
            resultados['Rc_adopt']
        )
        
        if diametro:
            print(f"✅ Poste encontrado: Diámetro = {diametro} mm, Peso = {peso} kg")
        else:
            diametro_estimado = self._estimar_diametro(resultados['Rc_adopt'])
            peso_estimado = self._estimar_peso(dimensiones['Ht_comercial'], diametro_estimado)
            print(f"⚠️  {mensaje}")
            print(f"Diámetro estimado: {diametro_estimado} mm, Peso estimado: {peso_estimado} kg")

        # ================= CÁLCULO DE VÍNCULOS =================
        if n_postes > 1:
            print(f"\n🔗 CANTIDAD Y POSICIÓN DE VÍNCULOS")
            print("=" * 50)
            
            print("Se determina la cantidad de vínculos en base a la altura descubierta")
            print("(por debajo de la primer cruceta), en base a la siguiente tabla de coeficientes:")
            print("\n{:^12} {:^12} {:^12} {:^12} {:^12} {:^12} {:^12}".format(
                "Altura desde", "Altura hasta", "Coef. 1° v.", "Coef. 2° v.", "Coef. 3° v.", "Coef. 4° v.", "Coef. 5° v.", "Coef. 6° v."))
            print("=" * 95)
            
            # Tabla de vínculos (coeficientes acumulativos desde suelo)
            tabla_vinculos = [
                (0, 10, [0.3, 0.635, None, None, None, None]),
                (10, 12, [0.22, 0.46, 0.72, None, None, None]),
                (12, 15, [0.17, 0.355, 0.555, 0.77, None, None]),
                (15, 18, [0.15, 0.3, 0.46, 0.63, 0.81, None]),
                (18, 22, [0.113, 0.236, 0.369, 0.512, 0.665, 0.828])
            ]
            
            for min_h, max_h, coefs in tabla_vinculos:
                print("{:^12} {:^12} {:^12} {:^12} {:^12} {:^12} {:^12} {:^12}".format(
                    f"{min_h}m", f"{max_h}m", 
                    f"{coefs[0]}" if coefs[0] else "-",
                    f"{coefs[1]}" if coefs[1] else "-",
                    f"{coefs[2]}" if coefs[2] else "-", 
                    f"{coefs[3]}" if coefs[3] else "-",
                    f"{coefs[4]}" if coefs[4] else "-",
                    f"{coefs[5]}" if coefs[5] else "-"
                ))

            # Determinar configuración
            h1a = geometria.dimensiones.get('h1a', 0)
            altura_vulnerable = h1a - self.ANCHO_CRUCETA
            
            n_vinculos = None
            coeficientes = []
            for n, (min_h, max_h, coefs) in enumerate(tabla_vinculos, 2):
                if min_h <= altura_vulnerable < max_h:
                    n_vinculos = n
                    coeficientes = [c for c in coefs if c is not None]
                    break
            
            print(f"\nAltura a vincular: {altura_vulnerable:.2f}m")
            print(f"(Se resta {self.ANCHO_CRUCETA}m por ser el ancho estimado de cruceta)")
            
            if n_vinculos and coeficientes:
                alturas_vinculos = [h1a * coef for coef in coeficientes]
                
                print(f"\n→ Se requieren {n_vinculos} vínculos")
                print("\nAlturas desde suelo:")
                for i, altura in enumerate(alturas_vinculos, 1):
                    print(f"  Vínculo {i}: {altura:.2f} m")
            else:
                print(f"\n⚠️  No se requieren vínculos para altura a sujetar = {altura_vulnerable:.2f}m")
        else:
            print(f"\n🔗 VÍNCULOS")
            print("=" * 30)
            print("Monoposte - No requiere vínculos")

    def generar_geometria_multiposte(self, geometria, mecanica):
        """
        Convierte la estructura unifilar en multiposte según la configuración calculada
        
        Args:
            geometria: Objeto EstructuraAEA_Geometria
            mecanica: Objeto EstructuraAEA_Mecanica
            
        Returns:
            nodes_key_multiposte: Diccionario de nodos para estructura multiposte
            tramos_key: Diccionario de tramos con tipo y conexiones
        """
        print("🔄 GENERANDO GEOMETRÍA MULTIPOSTE...")
        
        # Obtener configuración de postes desde cache
        if not hasattr(self, '_resultados_cache'):
            raise ValueError("Primero debe ejecutar calcular_seleccion_postes")
            
        config_seleccionada = self._resultados_cache['config_seleccionada']
        dimensiones = self._resultados_cache['dimensiones']
        
        # Determinar número de postes y orientación
        if "Monoposte" in config_seleccionada:
            n_postes = 1
            orientacion = "Centrado"
        elif "Biposte" in config_seleccionada:
            n_postes = 2
            if "TRANSVERSAL" in config_seleccionada:
                orientacion = "Transversal"
            else:
                orientacion = "Longitudinal"
        elif "Triposte" in config_seleccionada:
            n_postes = 3
            orientacion = "Triangular"
        else:
            n_postes = 1
            orientacion = "Centrado"
        
        # Obtener datos de la estructura unifilar
        nodes_unifilar = geometria.nodes_key
        Ht = dimensiones['Ht_comercial']
        Hl = dimensiones['Hl']
        He = Ht - Hl                # Longitud empotrada bajo suelo
        
        # Buscar diámetro de cima del poste seleccionado
        Rc_adopt = self._resultados_cache['Rc_adopt']
        dc, _, _ = self.buscar_postes_mejorado(Ht, Rc_adopt)
        dc = dc/1000                # pasar a m
        if dc is None:
            dc = 0.30  # Valor por defecto 30 cm
        
        print(f"   Configuración: {n_postes} poste(s) - {orientacion}")
        print(f"   Diámetro cima: {dc}m, Altura total: {Ht}m")
        
        # Generar geometría multiposte
        nodes_multiposte, tramos = self._generar_nodos_y_tramos_multiposte(
            nodes_unifilar, n_postes, orientacion, Ht, dc, geometria
        )
        
        # Almacenar en cache para uso posterior
        self.nodes_key_multiposte = nodes_multiposte
        self.tramos_key = tramos
        self.geometria_multiposte = {
            'n_postes': n_postes,
            'orientacion': orientacion,
            'dc': dc,
            'Ht': Ht,
            'Hl': Hl
        }
        
        print(f"✅ Geometría multiposte generada:")
        print(f"   - Nodos: {len(nodes_multiposte)}")
        print(f"   - Tramos: {len(tramos)}")
        
        return nodes_multiposte, tramos
    
    def _generar_nodos_y_tramos_multiposte(self, nodes_unifilar, n_postes, orientacion, Ht, dc, geometria):
        """Genera nodos y tramos para estructura multiposte"""
        
        nodes_multiposte = {}
        tramos = {}
        
        # 1. GENERAR POSTES
        postes_data = self._generar_postes(n_postes, orientacion, Ht, dc)
        
        # Agregar nodos de postes al diccionario
        for poste_id, poste in postes_data.items():
            nodes_multiposte[poste_id + '_BASE'] = poste['base']
            nodes_multiposte[poste_id + '_CIMA'] = poste['cima']
            
            # Tramo del poste
            tramos[f'POSTE_{poste_id}'] = {
                'tipo': 'poste',
                'nodo_inicio': poste_id + '_BASE',
                'nodo_fin': poste_id + '_CIMA',
                'seccion': 'hormigon',
                'dc': dc,
                'db': poste['diametro_base']
            }
        
        # 2. GENERAR VÍNCULOS
        vinculos_data = self._generar_vinculos(postes_data, geometria)
        
        for i, vinculo in enumerate(vinculos_data):
            nodo_inicio = f"V{i+1}_INICIO"
            nodo_fin = f"V{i+1}_FIN"
            
            nodes_multiposte[nodo_inicio] = vinculo['inicio']
            nodes_multiposte[nodo_fin] = vinculo['fin']
            
            tramos[f'VINCULO_{i+1}'] = {
                'tipo': 'vinculo',
                'nodo_inicio': nodo_inicio,
                'nodo_fin': nodo_fin,
                'seccion': 'acero',
                'diametro': 0.5  # 0.5 m por defecto
            }
        
        # 3. GENERAR CRUCETAS Y MÉNSULAS
        crucetas_data = self._generar_crucetas_y_mensulas(nodes_unifilar, postes_data, geometria)
        
        for i, cruceta in enumerate(crucetas_data):
            if cruceta['tipo'] == 'cruceta':
                # Cruceta que une dos puntos
                nodo_inicio = f"CRU_{i+1}_INICIO"
                nodo_fin = f"CRU_{i+1}_FIN"
                
                nodes_multiposte[nodo_inicio] = cruceta['inicio']
                nodes_multiposte[nodo_fin] = cruceta['fin']
                
                tramos[f'CRUCETA_{i+1}'] = {
                    'tipo': 'cruceta',
                    'nodo_inicio': nodo_inicio,
                    'nodo_fin': nodo_fin,
                    'seccion': 'acero',
                    'diametro': 0.015  # 15 mm por defecto
                }
            else:
                # Ménsula (un solo punto de amarre)
                nodo_inicio = f"MEN_{i+1}_INICIO"
                nodo_fin = f"MEN_{i+1}_FIN"
                
                nodes_multiposte[nodo_inicio] = cruceta['inicio']
                nodes_multiposte[nodo_fin] = cruceta['fin']
                
                tramos[f'MENSULA_{i+1}'] = {
                    'tipo': 'mensula',
                    'nodo_inicio': nodo_inicio,
                    'nodo_fin': nodo_fin,
                    'seccion': 'acero',
                    'diametro': 0.012  # 12 mm por defecto
                }
        
        # 4. PRESERVAR NODOS ORIGINALES DE CABLES
        # Mantener nodos de conductores y guardia en sus posiciones originales
        for nombre, coords in nodes_unifilar.items():
            if nombre.startswith(('C1_', 'C2_', 'C3_', 'HG', 'TOP')):
                nodes_multiposte[nombre] = coords
        
        return nodes_multiposte, tramos
    
    def _generar_postes(self, n_postes, orientacion, Ht, dc):
        """Genera la geometría de los postes según configuración"""
        
        postes = {}
        inclinacion = 0.055  # 5.5%
        conicidad = 0.015    # 1.5%
        sep_cima = self.sep_externa + dc
        diametro_base = dc + (Ht * conicidad)
        desplazamiento_base = Ht * inclinacion

        print(f"   🛠️ Parámetros postes: dc={dc}m, sep_cima={sep_cima}m, Ht={Ht}m")
        
        if n_postes == 1:
            # Monoposte - centrado
            base = (0, 0, 0)
            cima = (0, 0, Ht)
            
            postes['P1'] = {
                'base': base,
                'cima': cima,
                'diametro_base': diametro_base,
                'diametro_total': diametro_base
            }
            
        elif n_postes == 2:
            # Biposte
            print(f"   🛠️ Biposte: desplazamiento_base={desplazamiento_base:.3f}m")
            
            if orientacion == "Transversal":
                # Separación en X
                for i, x_sign in enumerate([-1, 1], 1):
                    base_x = x_sign * (sep_cima/2 + desplazamiento_base)
                    cima_x = x_sign * sep_cima/2
                    
                    base = (base_x, 0, 0)
                    cima = (cima_x, 0, Ht)
                    
                    postes[f'P{i}'] = {
                        'base': base,
                        'cima': cima,
                        'diametro_base': diametro_base,
                        'diametro_total': diametro_base
                    }
            else:
                # Separación en Y (LONGITUDINAL)
                for i, y_sign in enumerate([-1, 1], 1):
                    base_y = y_sign * (sep_cima/2 + desplazamiento_base)
                    cima_y = y_sign * sep_cima/2

                    base = (0, base_y, 0)
                    cima = (0, cima_y, Ht)
                    
                    postes[f'P{i}'] = {
                        'base': base,
                        'cima': cima,
                        'diametro_base': diametro_base,
                        'diametro_total': diametro_base
                    }
                    
        elif n_postes == 3:
            # Triposte - configuración triangular
            radio = sep_cima / math.sqrt(3)
            
            puntos_cima = [
                (0, radio, Ht),                    # Norte
                (-sep_cima/2, -radio/2, Ht),       # Suroeste  
                (sep_cima/2, -radio/2, Ht)         # Sureste
            ]
            
            for i, (x_cima, y_cima, z_cima) in enumerate(puntos_cima, 1):
                # Calcular dirección de inclinación (hacia afuera del centro)
                distancia = math.sqrt(x_cima**2 + y_cima**2)
                if distancia > 0:
                    dir_x = (x_cima / distancia) * desplazamiento_base
                    dir_y = (y_cima / distancia) * desplazamiento_base
                else:
                    dir_x, dir_y = 0, 0
                
                base_x = x_cima + dir_x
                base_y = y_cima + dir_y
                
                base = (base_x, base_y, 0)
                cima = (x_cima, y_cima, z_cima)
                
                postes[f'P{i}'] = {
                    'base': base,
                    'cima': cima,
                    'diametro_base': diametro_base,
                    'diametro_total': diametro_base
                }
        
        return postes

    def _generar_vinculos(self, postes_data, geometria):
        """Genera vínculos entre postes basado en el cálculo real de vínculos"""
        
        n_postes = len(poste_data)
        if n_postes == 1:
            return []  # Monoposte no necesita vínculos

        # Obtener datos de la estructura para cálculo de vínculos
        h1a = geometria.dimensiones.get('h1a', 0)
        altura_vulnerable = h1a - self.ANCHO_CRUCETA
        
        # Determinar número de vínculos según tabla (mismo método que en imprimir_desarrollo_seleccion_postes)
        tabla_vinculos = [
            (0, 10, [0.3, 0.635, None, None, None, None]),
            (10, 12, [0.22, 0.46, 0.72, None, None, None]),
            (12, 15, [0.17, 0.355, 0.555, 0.77, None, None]),
            (15, 18, [0.15, 0.3, 0.46, 0.63, 0.81, None]),
            (18, 22, [0.113, 0.236, 0.369, 0.512, 0.665, 0.828])
        ]
        
        n_vinculos = 0
        coeficientes = []
        for min_h, max_h, coefs in tabla_vinculos:
            if min_h <= altura_vulnerable < max_h:
                n_vinculos = len([c for c in coefs if c is not None])
                coeficientes = [c for c in coefs if c is not None]
                break
        
        if n_vinculos == 0:
            return []

        Ht = self._resultados_cache['dimensiones']['Ht_comercial']
        vinculos = []
        
        # Generar vínculos en las alturas calculadas
        for coef in coeficientes:
            altura = h1a * coef
            
            if n_postes == 2:
                # Biposte - línea recta entre los dos postes
                p1 = postes_data['P1']
                p2 = postes_data['P2']
                
                # Calcular posición en cada poste a esta altura
                factor = altura / Ht
                
                x1 = p1['base'][0] + factor * (p1['cima'][0] - p1['base'][0])
                y1 = p1['base'][1] + factor * (p1['cima'][1] - p1['base'][1])
                z1 = altura
                
                x2 = p2['base'][0] + factor * (p2['cima'][0] - p2['base'][0])
                y2 = p2['base'][1] + factor * (p2['cima'][1] - p2['base'][1])
                z2 = altura
                
                vinculos.append({
                    'inicio': (x1, y1, z1),
                    'fin': (x2, y2, z2)
                })
                
            elif n_postes == 3:
                # Triposte - triángulo conectando los tres postes
                puntos = []
                for poste_id in ['P1', 'P2', 'P3']:
                    poste = postes_data[poste_id]
                    factor = altura / Ht
                    
                    x = poste['base'][0] + factor * (poste['cima'][0] - poste['base'][0])
                    y = poste['base'][1] + factor * (poste['cima'][1] - poste['base'][1])
                    z = altura
                    puntos.append((x, y, z))
                
                # Conectar los tres puntos formando triángulo
                vinculos.extend([
                    {'inicio': puntos[0], 'fin': puntos[1]},
                    {'inicio': puntos[1], 'fin': puntos[2]},
                    {'inicio': puntos[2], 'fin': puntos[0]}
                ])
        
        return vinculos

    def _generar_crucetas_y_mensulas(self, nodes_unifilar, postes_data, geometria):
        """Genera crucetas y ménsulas para conductores y guardia"""
        
        elementos = []
        n_postes = len(poste_data)
        
        # Agrupar nodos por altura
        nodos_por_altura = {}
        for nombre, coords in nodes_unifilar.items():
            if nombre.startswith(('C1_', 'C2_', 'C3_', 'HG')):
                x, y, z = coords
                if z not in nodos_por_altura:
                    nodos_por_altura[z] = []
                nodos_por_altura[z].append((nombre, x, y, z))
        
        # Procesar cada altura
        for altura, nodos in nodos_por_altura.items():
            # Separar conductores y guardia
            conductores = [n for n in nodos if n[0].startswith(('C1_', 'C2_', 'C3_'))]
            guardias = [n for n in nodos if n[0].startswith('HG')]
            
            # CRUCETAS PARA CONDUCTORES
            if len(conductores) >= 2:
                # Hay múltiples conductores a esta altura - crear cruceta
                # Ordenar por coordenada X para determinar extremos
                conductores.sort(key=lambda n: n[1])  # ordenar por x
                
                inicio = (conductores[0][1], conductores[0][2], conductores[0][3])
                fin = (conductores[-1][1], conductores[-1][2], conductores[-1][3])
                
                elementos.append({
                    'tipo': 'cruceta',
                    'inicio': inicio,
                    'fin': fin
                })
            elif len(conductores) == 1:
                # Un solo conductor - crear ménsula
                conductor = conductores[0]
                nombre, x, y, z = conductor
                
                # Encontrar poste más cercano en el plano XY
                poste_cercano = min(postes_data.values(), 
                                  key=lambda p: self._distancia_xy((x, y), (p['cima'][0], p['cima'][1])))
                
                # Punto en el poste a esta altura
                factor = z / self._resultados_cache['dimensiones']['Ht_comercial']
                x_post = poste_cercano['base'][0] + factor * (poste_cercano['cima'][0] - poste_cercano['base'][0])
                y_post = poste_cercano['base'][1] + factor * (poste_cercano['cima'][1] - poste_cercano['base'][1])
                
                elementos.append({
                    'tipo': 'mensula',
                    'inicio': (x_post, y_post, z),
                    'fin': (x, y, z)
                })
            
            # MÉNSULAS PARA GUARDIA
            for guardia in guardias:
                nombre, x, y, z = guardia
                
                if n_postes == 1:
                    # Monoposte - ménsula desde TOP a HG
                    if 'TOP' in nodes_unifilar:
                        x_top, y_top, z_top = nodes_unifilar['TOP']
                        elementos.append({
                            'tipo': 'mensula',
                            'inicio': (x_top, y_top, z_top),
                            'fin': (x, y, z)
                        })
                else:
                    # Multiposte - ménsula desde poste más cercano
                    poste_cercano = min(postes_data.values(), 
                                      key=lambda p: self._distancia_xy((x, y), (p['cima'][0], p['cima'][1])))
                    
                    factor = z / self._resultados_cache['dimensiones']['Ht_comercial']
                    x_post = poste_cercano['base'][0] + factor * (poste_cercano['cima'][0] - poste_cercano['base'][0])
                    y_post = poste_cercano['base'][1] + factor * (poste_cercano['cima'][1] - poste_cercano['base'][1])
                    
                    elementos.append({
                        'tipo': 'mensula',
                        'inicio': (x_post, y_post, z),
                        'fin': (x, y, z)
                    })
        
        return elementos
    
    def _distancia_xy(self, punto1, punto2):
        """Calcula distancia en plano XY entre dos puntos 3D"""
        return math.sqrt((punto1[0] - punto2[0])**2 + (punto1[1] - punto2[1])**2)
    
    def obtener_geometria_multiposte(self):
        """Devuelve la geometría multiposte generada"""
        if hasattr(self, 'nodes_key_multiposte'):
            return self.nodes_key_multiposte, self.tramos_key, self.geometria_multiposte
        else:
            raise ValueError("Primero debe ejecutar generar_geometria_multiposte")