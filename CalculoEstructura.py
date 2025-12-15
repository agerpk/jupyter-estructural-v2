### CalculoEstructura
# 
import matplotlib.pyplot as plt
import numpy as np
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
    
class Estructura_AEA:
    """
    Clase completa que representa una estructura según norma AEA
    Incluye dimensionamiento, cargas, visualización y exportación
    """
    
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
    
    # Alturas mínimas sobre terreno
    ALTURAS_MINIMAS_TERRENO = {
        "Peatonal": 4.70, "Rural": 5.90, "Urbana": 8.38, 
        "Autopista": 7.00, "Ferrocarril": 8.50, "Línea Eléctrica": 1.20
    }
    
    # Configuración de colores para visualización
    COLORES = {
        'conductor': '#1f77b4', 'guardia': '#2ca02c', 'poste': '#000000', 
        'cadena': "#717170", 'conductor_end': 'red', 'circulo': 'gray',
        'apantallamiento': '#84FF6B', 'texto_verde': '#006400',
        'dhg_circulo': 'gray', 'terreno': '#8B4513'
    }
    
    # Mapeo de estados climáticos
    ESTADOS_MAPEO = {
        "Vmax": "III", "Vmed": "IV", "TMA": "V", "Tmin": "II", "Tmax": "I"
    }
    
    def __init__(self, tipo_estructura, tension_nominal, zona_estructura, 
                disposicion, terna, cant_hg, alpha_quiebre,
                altura_minima_cable, long_mensula_min_conductor, long_mensula_min_guardia,
                hadd, hadd_entre_amarres, lk, ancho_cruceta,
                cable_conductor, cable_guardia, peso_estructura=0, peso_cadena=None, hipotesis_a_incluir="Todas"):
        """
        Inicializa una estructura completa
        
        Args:
            ... [otros parámetros] ...
            peso_estructura (float): Peso de la estructura en daN (requerido)
            peso_cadena (float): Peso de la cadena en daN (requerido para cálculo theta_max)
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
        self.hipotesis_a_incluir = hipotesis_a_incluir

        
        # Validar parámetros requeridos
        if self.peso_estructura == 0:
            raise ValueError("El parámetro 'peso_estructura' es requerido y debe ser mayor a 0")
        
        if self.peso_cadena is None:
            raise ValueError("El parámetro 'peso_cadena' es requerido para el cálculo de theta_max")
        
        # Cables asociados
        self.cable_conductor = cable_conductor
        self.cable_guardia = cable_guardia
        
        # Colección de nodos
        self.nodos = {}
        
        # Resultados de dimensionamiento
        self.dimensiones = {}
        self.nodes_key = {}  # Para compatibilidad
        
        # Para almacenar DataFrames de cargas
        self.df_cargas_completo = None
        self.cargas_key = {}
        
        # Configuración por defecto
        self._configurar_parametros_default()
        
        print(f"✅ ESTRUCTURA_AEA CREADA: {self.tipo_estructura} - {self.tension_nominal}kV - {self.zona_estructura}")
        
    
    def _configurar_parametros_default(self):
        """Configura parámetros por defecto y derivados"""
        self.tension_maxima = self.TABLA_TENSION_MAXIMA.get(
            self.tension_nominal, self.tension_nominal * 1.1
        )
        
        self.altura_minima_terreno = max(
            self.ALTURAS_MINIMAS_TERRENO.get(self.zona_estructura, 5.90),
            self.altura_minima_cable
        )
        
        # Determinar tipo de fijación base (CORREGIDO: lógica mejorada)
        tipo_lower = self.tipo_estructura.lower()
        if "retención" in tipo_lower or "terminal" in tipo_lower or "retencion" in tipo_lower:
            self.tipo_fijacion_base = "retención"
        elif "suspension" in tipo_lower or "suspensión" in tipo_lower:
            self.tipo_fijacion_base = "suspensión"
        else:
            # Por defecto asumir suspensión
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
    
    def dimensionar_unifilar(self, vano, flecha_max_conductor, flecha_max_guardia, df_cargas_totales=None):
        """
        Dimensiona la estructura y genera todos los nodos
        """
        print(f"📐 DIMENSIONANDO ESTRUCTURA UNIFILAR...")
        print(f"   Vano: {vano}m, Flechas: cond={flecha_max_conductor:.2f}m, guard={flecha_max_guardia:.2f}m")
        
        # Inicializar dimensiones si no existe
        if not hasattr(self, 'dimensiones'):
            self.dimensiones = {}
        
        # 1. CALCULAR TODOS LOS PARÁMETROS DEL CABEZAL (solo una vez)
        self._calcular_parametros_cabezal(vano, flecha_max_conductor, flecha_max_guardia, df_cargas_totales)
        
        # 2. EXTRAER PARÁMETROS CALCULADOS DEL DATAFRAME
        parametros = self.parametros_cabezal.iloc[0]
        k = parametros['k']
        D_fases = parametros['D_fases']
        s_estructura = parametros['s_estructura']
        Dhg = parametros['Dhg']
        b = parametros['b']
        altura_base_electrica = parametros['altura_base_electrica']
        theta_max = parametros['theta_max']
        
        # 3. DETERMINAR CONFIGURACIÓN DE ALTURAS SEGÚN DISPOSICIÓN Y TERNA
        h1a = altura_base_electrica + flecha_max_conductor + self.lk

        if self.terna == "Simple":
            if self.disposicion == "horizontal":
                h2a = h1a
                h3a = h1a
            elif self.disposicion == "triangular":
                h2a = h1a + D_fases + self.hadd_entre_amarres
                h3a = h2a
            else:  # vertical
                h2a = h1a + D_fases + self.hadd_entre_amarres
                h3a = h2a + D_fases + self.hadd_entre_amarres
        else:  # Terna Doble
            if self.disposicion == "horizontal":
                h2a = h1a
                h3a = h1a
            elif self.disposicion == "triangular":
                # Para doble terna triangular: SOLO 2 ALTURAS (no 3)
                h2a = h1a + D_fases + self.hadd_entre_amarres
                h3a = h2a  # No hay tercera altura, se mantiene igual para compatibilidad
            else:  # vertical
                h2a = h1a + D_fases + self.hadd_entre_amarres
                h3a = h2a + D_fases + self.hadd_entre_amarres
        
        # 4. CÁLCULO DE MENSULAS 
        lmen_base = max(s_estructura, 0.5)  # Solo mínimo de 0.5m
        lmen_adoptada = max(lmen_base, self.long_mensula_min_conductor)
        lmenhg = self.long_mensula_min_guardia
        
        # 5. ALTURA CABLE GUARDIA
        h_conductor_mas_alto = h3a if self.terna == "Doble" else h2a if self.disposicion == "triangular" else h1a
        h_conductor_real = h_conductor_mas_alto - self.lk
        hhg_inicial = h_conductor_real + Dhg
        
        # Ajuste por apantallamiento
        tangente_30 = math.tan(math.radians(30))
        cobertura_efectiva = False
        hhg = hhg_inicial
        
        if self.terna == "Doble" and self.cant_hg == 1:
            # Guardia centrado sobre estructura
            distancia_horizontal_max = lmen_adoptada
            distancia_vertical_minima = distancia_horizontal_max / tangente_30
            hhg_minimo = h_conductor_real + distancia_vertical_minima
            hhg = max(hhg_inicial, hhg_minimo)
            distancia_vertical_final = hhg - h_conductor_real
            distancia_diagonal = math.sqrt(distancia_horizontal_max**2 + distancia_vertical_final**2)
            angulo_apantallamiento = math.degrees(math.atan(distancia_horizontal_max / distancia_vertical_final))
            cobertura_efectiva = (angulo_apantallamiento <= 30) and (distancia_diagonal >= Dhg)
            lmenhg = 0.0
        else:
            # Cálculo iterativo para otras configuraciones 
            iteraciones = 0
            while not cobertura_efectiva and iteraciones < 10000:  #  a 10000
                distancia_vertical = hhg - h_conductor_real
                
                if self.terna == "Simple" and self.cant_hg == 1:
                    lmenhg_base = distancia_vertical * tangente_30
                    dist_horizontal_efectiva = lmen_adoptada + lmenhg_base
                    dist_diagonal = math.sqrt(dist_horizontal_efectiva**2 + distancia_vertical**2)
                    angulo_apant = math.degrees(math.atan(dist_horizontal_efectiva / distancia_vertical))
                    
                    if angulo_apant <= 30 and dist_diagonal >= Dhg:
                        cobertura_efectiva = True
                        lmenhg = max(lmenhg_base, self.long_mensula_min_guardia)
                    else:
                        hhg += 0.01
                        
                elif self.terna == "Doble" and self.cant_hg == 2:
                    lmenhg_base = distancia_vertical * tangente_30
                    dist_horizontal_efectiva = lmen_adoptada - lmenhg_base
                    if dist_horizontal_efectiva < 0:
                        dist_horizontal_efectiva = 0
                    dist_diagonal = math.sqrt(dist_horizontal_efectiva**2 + distancia_vertical**2)
                    angulo_apant = math.degrees(math.atan(dist_horizontal_efectiva / distancia_vertical))
                    
                    if angulo_apant <= 30 and dist_diagonal >= Dhg and lmenhg_base >= lmen_adoptada:
                        cobertura_efectiva = True
                        lmenhg = max(lmenhg_base, self.long_mensula_min_guardia)
                    else:
                        hhg += 0.01
                else:
                    cobertura_efectiva = True
                
                iteraciones += 1
        
        # 6. CREACIÓN DE NODOS
        self._crear_nodos_estructurales(h1a, h2a, h3a, hhg, lmen_adoptada, lmenhg)
        
        # 7. GUARDAR DIMENSIONES Y ACTUALIZAR PARÁMETROS EN EL DATAFRAME EXISTENTE
        dimensiones_adicionales = {
            "h1a": h1a, "h2a": h2a, "h3a": h3a, "hhg": hhg,
            "lmen_adoptada": lmen_adoptada, "lmenhg": lmenhg,
            "cobertura_efectiva": cobertura_efectiva,
            "altura_total": hhg if self.terna == "Doble" and self.cant_hg == 1 else hhg
        }
        
        self.dimensiones = dimensiones_adicionales
        
        # Actualizar el DataFrame de parámetros con las dimensiones adicionales
        for key, value in dimensiones_adicionales.items():
            self.parametros_cabezal[key] = value
        
        print(f"✅ DIMENSIONAMIENTO COMPLETADO")
        print(f"   - Alturas: h1a={h1a:.2f}m, h2a={h2a:.2f}m, h3a={h3a:.2f}m, hhg={hhg:.2f}m")
        print(f"   - Ménsulas: conductor={lmen_adoptada:.2f}m, guardia={lmenhg:.2f}m")
        print(f"   - Cobertura apantallamiento: {'SÍ' if cobertura_efectiva else 'NO'}")
        print(f"   - theta_max: {theta_max:.2f}°")

    def _calcular_parametros_cabezal(self, vano, flecha_max_conductor, flecha_max_guardia, df_cargas_totales=None):
        """
        Calcula todos los parámetros del cabezal y los almacena en un DataFrame interno
        """
        # Inicializar diccionario de parámetros
        parametros = {}
        
        # 1. PRIMERO CALCULAR THETA_MAX (ÁNGULO DE DECLINACIÓN) - CORREGIDO
        # Si no es estructura de suspensión O Lk = 0, entonces theta_max = 0
        if self.tipo_fijacion_base != "suspensión" or self.lk == 0:
            parametros['theta_max'] = 0.0
            print(f"   📐 theta_max = 0° (estructura no es suspensión o Lk=0)")
        else:
            try:
                # Obtener cargas reales del DataFrame de cargas si está disponible
                if df_cargas_totales is not None:
                    # Buscar carga de viento para conductor en estado de viento máximo
                    filtro_viento = (df_cargas_totales['Elemento'] == 'Conductor') & \
                                (df_cargas_totales['Estado Climático'] == 'Vmax') & \
                                (df_cargas_totales['Direccion'] == 'Transversal') & \
                                (df_cargas_totales['Carga'].str.contains('Viento'))
                    
                    if not df_cargas_totales[filtro_viento].empty:
                        carga_viento_conductor = df_cargas_totales[filtro_viento]['Magnitud'].iloc[0]
                    else:
                        # Fallback: calcular basado en propiedades del cable
                        resultado_viento = self.cable_conductor.cargaViento(
                            V=38.9,
                            phi_rel_deg=90, exp="C", clase="B",
                            Zc=10.0, Cf=1.0, L_vano=vano
                        )
                        carga_viento_conductor = resultado_viento["fuerza_daN_per_m"] * vano
                else:
                    # Fallback si no hay DataFrame
                    resultado_viento = self.cable_conductor.cargaViento(
                        V=38.9, phi_rel_deg=90, exp="C", clase="B",
                        Zc=10.0, Cf=1.0, L_vano=vano
                    )
                    carga_viento_conductor = resultado_viento["fuerza_daN_per_m"] * vano
                
                # Peso del conductor en el vano
                peso_conductor = self.cable_conductor.peso_unitario_dan_m * vano
                peso_cadena = self.peso_cadena
                
                # Calcular theta_max usando arctan(Fv/P)
                if (peso_conductor + peso_cadena) > 0:
                    theta_max_rad = math.atan(carga_viento_conductor / (peso_conductor + peso_cadena))
                    parametros['theta_max'] = math.degrees(theta_max_rad)
                else:
                    parametros['theta_max'] = 99.0

                print(f"   📐 Cálculo theta_max (suspensión con Lk>0):")
                print(f"      - Carga viento conductor: {carga_viento_conductor:.2f} daN")
                print(f"      - Peso conductor: {peso_conductor:.2f} daN")
                print(f"      - Peso cadena: {peso_cadena:.2f} daN")
                print(f"      - theta_max calculado: {parametros['theta_max']:.2f}°")
                
            except Exception as e:
                print(f"   ⚠️ Error calculando theta_max: {e}")
                parametros['theta_max'] = 99.0
        
        # 2. AHORA CALCULAR k BASADO EN THETA_MAX (CORREGIDO)
        k = self._obtener_coeficiente_k(parametros['theta_max'])
        parametros['k'] = k
        
        # 3. FINALMENTE CALCULAR LAS DISTANCIAS MÍNIMAS CON k CORRECTO
        termino_flecha = flecha_max_conductor + self.lk
        
        # Distancia mínima entre fases (D)
        parametros['D_fases'] = k * math.sqrt(termino_flecha) + self.tension_nominal / 150
        
        # Distancia mínima fase-estructura (s)
        s_base = 0.280 + 0.005 * (self.tension_maxima - 50)
        parametros['s_estructura'] = max(s_base, self.tension_nominal / 150)
        
        # Distancia mínima guardia-conductor (Dhg)
        parametros['Dhg'] = k * math.sqrt(termino_flecha) + (self.tension_nominal / math.sqrt(3)) / 150
        
        # Componente eléctrico adicional
        parametros['b'] = 0.01 * (self.tension_nominal / math.sqrt(3) - 22) if self.tension_nominal > 33 else 0.0
        
        # Altura base eléctrica
        parametros['altura_base_electrica'] = self.altura_minima_terreno + self.hadd + parametros['b']
        
        # 4. CREAR DATAFRAME CON TODOS LOS PARÁMETROS
        self.parametros_cabezal = pd.DataFrame([parametros])
        
        print(f"   📊 Parámetros del cabezal calculados:")
        print(f"      - theta_max: {parametros['theta_max']:.2f}°")
        print(f"      - k (basado en theta_max): {k:.3f}")
        print(f"      - D_fases: {parametros['D_fases']:.3f} m")
        print(f"      - s_estructura: {parametros['s_estructura']:.3f} m")
        print(f"      - Dhg: {parametros['Dhg']:.3f} m")
        
        # Guardar también en dimensiones para compatibilidad
        self.dimensiones['D_fases'] = parametros['D_fases']
        self.dimensiones['s_estructura'] = parametros['s_estructura']
        self.dimensiones['Dhg'] = parametros['Dhg']
        self.dimensiones['theta_max'] = parametros['theta_max']
    
    def obtener_parametros_cabezal(self):
        """Devuelve el DataFrame con todos los parámetros del cabezal"""
        return self.parametros_cabezal


    def _crear_nodos_estructurales(self, h1a, h2a, h3a, hhg, lmen_cond, lmen_guardia):
        """Crea todos los nodos de la estructura según configuración"""
        self.nodos = {}
        
        # NODO BASE
        self.nodos["BASE"] = NodoEstructural(
            "BASE", (0.0, 0.0, 0.0), "base", 
            tipo_fijacion=self.tipo_fijacion_base
        )
        
        # NODOS DE CRUCE (poste-ménsula)
        self.nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
        if h2a > h1a:
            self.nodos["CROSS_H2"] = NodoEstructural("CROSS_H2", (0.0, 0.0, h2a), "cruce")
        if h3a > h2a:
            self.nodos["CROSS_H3"] = NodoEstructural("CROSS_H3", (0.0, 0.0, h3a), "cruce")
        
        # NODOS DE CONDUCTORES según disposición y terna
        if self.terna == "Simple":
            if self.disposicion == "horizontal":
                # Todos en misma altura, separados horizontalmente
                self._crear_nodos_conductor_simple_horizontal(h1a, lmen_cond)
            elif self.disposicion == "triangular":
                # Dos niveles
                self._crear_nodos_conductor_simple_triangular(h1a, h2a, lmen_cond)
            else:  # vertical
                # Tres niveles
                self._crear_nodos_conductor_simple_vertical(h1a, h2a, h3a, lmen_cond)
        else:  # Terna Doble
            if self.disposicion == "horizontal":
                self._crear_nodos_conductor_doble_horizontal(h1a, lmen_cond)
            elif self.disposicion == "triangular":
                # DIFERENCIAR POR TIPO DE ESTRUCTURA (SUSPENSIÓN vs RETENCIÓN/TERMINAL)
                # Suspensiones tienen Lk > 0 y necesitan distribución de conductores diferente
                if self.tipo_fijacion_base == "suspensión" and self.lk > 0:
                    print(f"   🏗️ Usando configuración DOBLE TERNA TRIANGULAR para SUSPENSIÓN (Lk={self.lk}m)")
                    self._crear_nodos_conductor_doble_triangular(h1a, h2a, lmen_cond)
                else:
                    # Retención/Terminal: Lk = 0, conductores agrupados
                    print(f"   🏗️ Usando configuración DOBLE TERNA TRIANGULAR para RETENCIÓN/TERMINAL (Lk={self.lk}m)")
                    self._crear_nodos_conductor_doble_triangular(h1a, h2a, lmen_cond)
            else:  # vertical
                self._crear_nodos_conductor_doble_vertical(h1a, h2a, h3a, lmen_cond)
        
        # NODOS DE GUARDIA
        self._crear_nodos_guardia(hhg, lmen_guardia)
        
        # NODO DE VIENTO (a 2/3 de la altura total)
        altura_v = (2/3) * hhg
        self.nodos["V"] = NodoEstructural("V", (0.0, 0.0, altura_v), "viento")
        
        # NODO MEDIO (auxiliar)
        self.nodos["MEDIO"] = NodoEstructural(
            "MEDIO", (0.0, 0.0, (h1a + hhg) / 2), "general"
        )
        
        # Actualizar nodes_key para compatibilidad
        self._actualizar_nodes_key()
    
    def _crear_nodos_conductor_simple_horizontal(self, altura, lmen):
        """Crea nodos para terna simple disposición horizontal"""
        h1a = altura
        s_estructura = self.dimensiones.get('s_estructura', 0.5)
        D_fases = self.dimensiones.get('D_fases', 1.5)
        theta_max = self.dimensiones.get('theta_max', 0.0)
        print(f"   🔍 DEBUG horizontal: s_estructura={s_estructura}, D_fases={D_fases}, theta_max={theta_max}, Lk={self.lk}")
        
        # Calcular distancias
        dist_columna_x = max(self.lk * math.sin(math.radians(theta_max)) + s_estructura, D_fases / 2)
        dist_conductor_final = max(D_fases, dist_columna_x + self.lk * math.sin(math.radians(theta_max)) + s_estructura + self.ancho_cruceta/2)
        print(f"   🔍 DEBUG: dist_columna_x={dist_columna_x:.3f}, dist_conductor_final={dist_conductor_final:.3f}")
        
        # Nodos estructurales Y#
        altura_y1 = h1a - 2*self.lk - s_estructura
        self.nodos["Y1"] = NodoEstructural("Y1", (0.0, 0.0, altura_y1), "general")
        self.nodos["Y2"] = NodoEstructural("Y2", (dist_columna_x, 0.0, h1a - self.lk), "general")
        self.nodos["Y3"] = NodoEstructural("Y3", (-dist_columna_x, 0.0, h1a - self.lk), "general")
        self.nodos["Y4"] = NodoEstructural("Y4", (dist_columna_x, 0.0, h1a), "general")
        self.nodos["Y5"] = NodoEstructural("Y5", (-dist_columna_x, 0.0, h1a), "general")
        
        # Nodos de conductores C1, C2, C3
        self.nodos["C1"] = NodoEstructural("C1", (dist_conductor_final, 0.0, h1a), "conductor",
                                  self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2"] = NodoEstructural("C2", (0.0, 0.0, h1a), "conductor",
                                  self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3"] = NodoEstructural("C3", (-dist_conductor_final, 0.0, h1a), "conductor",
                                  self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
    
    def _crear_nodos_conductor_simple_triangular(self, h1a, h2a, lmen):
        """Crea nodos para terna simple disposición triangular"""
        self.nodos["C1_L"] = NodoEstructural(
            "C1_L", (-lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C1_R"] = NodoEstructural(
            "C1_R", (lmen, 0.0, h1a), "conductor", 
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C2_L"] = NodoEstructural(
            "C2_L", (0.0, 0.0, h2a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
    
    def _crear_nodos_conductor_simple_vertical(self, h1a, h2a, h3a, lmen):
        """Crea nodos para terna simple disposición vertical"""
        self.nodos["C1_L"] = NodoEstructural(
            "C1_L", (-lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C2_L"] = NodoEstructural(
            "C2_L", (-lmen, 0.0, h2a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C3_L"] = NodoEstructural(
            "C3_L", (-lmen, 0.0, h3a), "conductor", 
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
    
    def _crear_nodos_conductor_doble_horizontal(self, altura, lmen):
        """Crea nodos para terna doble disposición horizontal - MODIFICADO PARA TERMINAL"""
        # Lado izquierdo
        self.nodos["C1_L"] = NodoEstructural("C1_L", (-lmen, 0.0, altura), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2_L"] = NodoEstructural("C2_L", (-lmen, 0.0, altura), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3_L"] = NodoEstructural("C3_L", (-lmen, 0.0, altura), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        # Lado derecho
        self.nodos["C1_R"] = NodoEstructural("C1_R", (lmen, 0.0, altura), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2_R"] = NodoEstructural("C2_R", (lmen, 0.0, altura), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3_R"] = NodoEstructural("C3_R", (lmen, 0.0, altura), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
    
    def _crear_nodos_conductor_doble_triangular(self, h1a, h2a, lmen):
        """Crea nodos para terna doble disposición triangular - MODIFICADO PARA TERMINAL"""
        # Nivel inferior
        self.nodos["C1_L"] = NodoEstructural("C1_L", (-lmen, 0.0, h1a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C1_R"] = NodoEstructural("C1_R", (lmen, 0.0, h1a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2_L"] = NodoEstructural("C2_L", (-lmen, 0.0, h1a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2_R"] = NodoEstructural("C2_R", (lmen, 0.0, h1a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        # Nivel superior
        self.nodos["C3_L"] = NodoEstructural("C3_L", (0.0, 0.0, h2a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3_R"] = NodoEstructural("C3_R", (0.0, 0.0, h2a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)

    
    def _crear_nodos_conductor_doble_vertical(self, h1a, h2a, h3a, lmen):
        """Crea nodos para terna doble disposición vertical - MODIFICADO PARA TERMINAL"""
        # Lado izquierdo - 3 conductores
        self.nodos["C1_L"] = NodoEstructural("C1_L", (-lmen, 0.0, h1a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2_L"] = NodoEstructural("C2_L", (-lmen, 0.0, h2a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3_L"] = NodoEstructural("C3_L", (-lmen, 0.0, h3a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        # Lado derecho - 3 conductores
        self.nodos["C1_R"] = NodoEstructural("C1_R", (lmen, 0.0, h1a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C2_R"] = NodoEstructural("C2_R", (lmen, 0.0, h2a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
        self.nodos["C3_R"] = NodoEstructural("C3_R", (lmen, 0.0, h3a), "conductor",
                                        self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base)
    
    # Modificación en el método asignar_cargas_hipotesis para el patrón dos-unilaterales en Terminal
    def _aplicar_patron_dos_unilaterales_terminal(self, nodo, config_tiro, tiro_base, es_guardia=False):
        """
        Aplica patrón dos-unilaterales inverso para Terminal: 
        todos menos un conductor y un guardia se cargan con tiro unilateral
        """
        if es_guardia:
            # Para guardias: determinar qué guardia NO se carga (el eliminado)
            nodos_guardia = [n for n in self.nodes_key.keys() if n.startswith('HG')]
            if len(nodos_guardia) > 1:
                # Eliminar el primer guardia (HG1), cargar los demás con tiro unilateral
                guardia_eliminado = "HG1"
                if nodo == guardia_eliminado:
                    # Este guardia se elimina - no se carga
                    return 0.0, 0.0, 0.0, 0.0  # tiro_trans, tiro_long, factor_peso, factor_viento
                else:
                    # Los demás guardias se cargan con tiro unilateral
                    factor_guardia = config_tiro.get("factor_guardia", 1.0)
                    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                        tiro_base, self.alpha_quiebre, factor_guardia
                    )
                    return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
            else:
                # Solo un guardia - se carga con tiro unilateral
                factor_guardia = config_tiro.get("factor_guardia", 1.0)
                tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                    tiro_base, self.alpha_quiebre, factor_guardia
                )
                return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
        
        else:
            # Para conductores: determinar qué conductor NO se carga (el eliminado)
            nodos_conductor = [n for n in self.nodes_key.keys() if n.startswith(('C1_', 'C2_', 'C3_'))]
            
            if nodos_conductor:
                # Elegir un conductor a eliminar (por ejemplo, el primero)
                conductor_eliminado = nodos_conductor[0]
                
                if nodo == conductor_eliminado:
                    # Este conductor se elimina - no se carga
                    return 0.0, 0.0, 0.0, 0.0
                else:
                    # Los demás conductores se cargan con tiro unilateral
                    factor_cond = config_tiro.get("factor_cond", 1.0)
                    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                        tiro_base, self.alpha_quiebre, factor_cond
                    )
                    return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
            else:
                return 0.0, 0.0, 0.0, 0.0

    def _crear_nodos_guardia(self, hhg, lmen_guardia):
        """Crea nodos para cables de guardia según configuración"""
        if self.terna == "Doble" and self.cant_hg == 1:
            # Guardia centrado
            self.nodos["HG1"] = NodoEstructural(
                "HG1", (0.0, 0.0, hhg), "guardia",
                self.cable_guardia, self.alpha_quiebre, self.tipo_fijacion_base
            )
        elif self.terna == "Simple" and self.cant_hg == 1:
            # Guardia en un extremo
            self.nodos["HG1"] = NodoEstructural(
                "HG1", (-lmen_guardia, 0.0, hhg), "guardia",
                self.cable_guardia, self.alpha_quiebre, self.tipo_fijacion_base
            )
            self.nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg), "general")
        elif self.terna == "Doble" and self.cant_hg == 2:
            # Dos guardias
            self.nodos["HG1"] = NodoEstructural(
                "HG1", (-lmen_guardia, 0.0, hhg), "guardia",
                self.cable_guardia, self.alpha_quiebre, self.tipo_fijacion_base
            )
            self.nodos["HG2"] = NodoEstructural(
                "HG2", (lmen_guardia, 0.0, hhg), "guardia",
                self.cable_guardia, self.alpha_quiebre, self.tipo_fijacion_base
            )
            self.nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg), "general")
        else:
            # Configuración por defecto
            self.nodos["HG1"] = NodoEstructural(
                "HG1", (0.0, 0.0, hhg), "guardia",
                self.cable_guardia, self.alpha_quiebre, self.tipo_fijacion_base
            )
    
    def _actualizar_nodes_key(self):
        """Actualiza el diccionario nodes_key para compatibilidad"""
        self.nodes_key = {}
        for nombre, nodo in self.nodos.items():
            self.nodes_key[nombre] = list(nodo.coordenadas)
    
    def obtener_nodes_key(self):
        """Devuelve el diccionario de nodos en formato compatible"""
        return self.nodes_key
    
    def listar_nodos(self):
        """Lista todos los nodos de la estructura"""
        print(f"\n📋 NODOS DE LA ESTRUCTURA ({len(self.nodos)} nodos):")
        print("=" * 80)
        for nombre, nodo in sorted(self.nodos.items()):
            print(f"  {nombre}: {nodo.coordenadas} - {nodo.tipo_nodo}")
    
    def obtener_nodo(self, nombre_nodo):
        """Obtiene un nodo por nombre"""
        return self.nodos.get(nombre_nodo)
    
    def obtener_nodos_por_tipo(self, tipo):
        """Obtiene todos los nodos de un tipo específico"""
        return [nodo for nodo in self.nodos.values() if nodo.tipo_nodo == tipo]
    
    def info_estructura(self):
        """Devuelve información completa de la estructura"""
        tipo_detallado = f"{self.tipo_estructura} - {self.disposicion} - {self.terna}"
        if self.disposicion == "triangular" and self.terna == "Doble":
            if self.tipo_fijacion_base == "suspensión" and self.lk > 0:
                tipo_detallado += " (Suspensión - Lk>0)"
            else:
                tipo_detallado += " (Retención/Terminal - Lk=0)"
        
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
            "Altura total": f"{self.dimensiones.get('altura_total', 0):.2f} m"
        }
        return info

    # ================= MÉTODOS DE CÁLCULO DE CARGAS =================

    def _calcular_componentes_tiro(self, tiro, angulo_grados, reduccion=0.0, es_guardia=False):
        """Calcula componentes transversal y longitudinal del tiro"""
        ang_rad = math.radians(angulo_grados / 2)
        
        if reduccion > 0:
            factor_trans = 2.0 * math.sin(ang_rad) * (1 - reduccion/2)
            factor_long = 2.0 * math.cos(ang_rad) * (reduccion/2)
        else:
            factor_trans = 2.0 * math.sin(ang_rad)
            factor_long = 0.0
        
        tiro_trans = factor_trans * tiro
        tiro_long = factor_long * tiro
        
        return tiro_trans, tiro_long

    def _calcular_componentes_tiro_unilateral(self, tiro, angulo_grados, factor=1.0):
        """Calcula componentes para tiro unilateral"""
        ang_rad = math.radians(angulo_grados / 2)
        
        factor_trans = factor * math.sin(ang_rad)
        factor_long = factor * math.cos(ang_rad)
        
        tiro_trans = factor_trans * tiro
        tiro_long = factor_long * tiro
        
        return tiro_trans, tiro_long

    def _obtener_carga_por_codigo(self, df_cargas_totales, codigo_buscar):
        """Busca carga por código en DataFrame de cargas"""
        try:
            filtro = df_cargas_totales['Código'] == codigo_buscar
            if not df_cargas_totales[filtro].empty:
                return df_cargas_totales[filtro]['Magnitud'].iloc[0]
            else:
                return 0.0
        except Exception as e:
            print(f"   ❌ Error buscando código {codigo_buscar}: {e}")
            return 0.0

    def _obtener_tiro_estado(self, resultados_dict, estado, componente="longitudinal"):
        """Obtiene tiro para estado específico"""
        if estado in resultados_dict:
            tiro_total = resultados_dict[estado]["tiro_daN"]
            alpha_rad = math.radians(self.alpha_quiebre / 2.0)
            if componente == "transversal":
                return round(tiro_total * math.sin(alpha_rad), 2)
            else:
                return round(tiro_total * math.cos(alpha_rad), 2)
        return 0.0

    def asignar_cargas_hipotesis(self, df_cargas_totales, resultados_conductor, resultados_guardia, vano, hipotesis_maestro, t_hielo):        
        """
        Asigna cargas a todos los nodos según las hipótesis definidas
        
        Args:
            df_cargas_totales (DataFrame): DataFrame con todas las cargas
            resultados_conductor (dict): Resultados del cálculo mecánico del conductor
            resultados_guardia (dict): Resultados del cálculo mecánico del guardia
            vano (float): Longitud del vano en metros
            hipotesis_maestro (dict): Diccionario con definición de hipótesis
            t_hielo (float): Espesor de hielo en metros

        """
        print(f"\n🔄 ASIGNANDO CARGAS SEGÚN HIPÓTESIS...")
        
        # Pesos base
        peso_conductor_base = self.cable_conductor.peso_unitario_dan_m
        peso_guardia_base = self.cable_guardia.peso_unitario_dan_m
        
        # Pesos con hielo
        peso_hielo_conductor = self.cable_conductor._calcular_peso_hielo(t_hielo)
        peso_hielo_guardia = self.cable_guardia._calcular_peso_hielo(t_hielo)
        
        # Nodos especiales
        NODOS_DOS_UNILATERAL = ["C3_L", "HG1"]
        
        # Filtrar hipótesis si se especificó
        if self.tipo_estructura in hipotesis_maestro:
            hipotesis_dict = hipotesis_maestro[self.tipo_estructura]
            
            # Determinar qué hipótesis procesar
            if self.hipotesis_a_incluir == "Todas":
                hipotesis_a_procesar = hipotesis_dict.items()
                print(f"   Procesando TODAS las hipótesis disponibles")
            else:
                hipotesis_a_procesar = []
                for codigo in self.hipotesis_a_incluir:
                    if codigo in hipotesis_dict:
                        hipotesis_a_procesar.append((codigo, hipotesis_dict[codigo]))
                    else:
                        print(f"   ⚠️ Hipótesis {codigo} no encontrada para {self.tipo_estructura}")
                print(f"   Procesando hipótesis: {self.hipotesis_a_incluir}")

            for codigo_hip, config in hipotesis_maestro[self.tipo_estructura].items():
                nombre_completo = f"HIP_{self.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_')}_{codigo_hip}_{config['desc']}"
                
                # Inicializar cargas para esta hipótesis
                cargas_hipotesis = {nombre: [0.00, 0.00, 0.00] for nombre in self.nodes_key.keys()}
                
                try:
                    # Obtener estados
                    estado_viento_config = config["viento"]["estado"] if config["viento"] else None
                    estado_viento = self.ESTADOS_MAPEO.get(estado_viento_config, estado_viento_config) if estado_viento_config else None
                    
                    estado_tiro_config = config["tiro"]["estado"] if config["tiro"] else None
                    estado_tiro = self.ESTADOS_MAPEO.get(estado_tiro_config, estado_tiro_config) if estado_tiro_config else None
                    
                    config_tiro = config["tiro"] if config["tiro"] else None
                    patron_tiro = config_tiro["patron"] if config_tiro else "bilateral"
                    
                    factor_peso = config["peso"]["factor"]
                    
                    # Calcular pesos
                    if config["peso"]["hielo"]:
                        peso_cond = (peso_conductor_base + peso_hielo_conductor) * vano * factor_peso
                        peso_guardia = (peso_guardia_base + peso_hielo_guardia) * vano * factor_peso
                    else:
                        peso_cond = peso_conductor_base * vano * factor_peso
                        peso_guardia = peso_guardia_base * vano * factor_peso
                    
                    # Obtener tiros
                    if estado_tiro == "máximo":
                        tiro_cond_base = max([d["tiro_daN"] for d in resultados_conductor.values()])
                        tiro_guardia_base = max([d["tiro_daN"] for d in resultados_guardia.values()])
                    elif estado_tiro in resultados_conductor and estado_tiro in resultados_guardia:
                        tiro_cond_base = resultados_conductor[estado_tiro]["tiro_daN"]
                        tiro_guardia_base = resultados_guardia[estado_tiro]["tiro_daN"]
                    else:
                        tiro_cond_base = 0.0
                        tiro_guardia_base = 0.0
                    
                    # VIENTO SOBRE ESTRUCTURA
                    if config["viento"]:
                        direccion_viento = config["viento"]["direccion"]
                        factor_viento = config["viento"]["factor"]
                        estado_v = config["viento"]["estado"]
                        
                        if direccion_viento == "Transversal":
                            if estado_v == "Vmax":
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "VeT")
                            else:
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "Vemedt")
                            cargas_hipotesis['V'] = [viento_estructura * factor_viento, 0.0, 0.0]
                            
                        elif direccion_viento == "Longitudinal":
                            if estado_v == "Vmax":
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "VeL")
                            else:
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "Vemedl")
                            cargas_hipotesis['V'] = [0.0, viento_estructura * factor_viento, 0.0]
                            
                        elif direccion_viento == "Oblicua":
                            if estado_v == "Vmax":
                                viento_estructura_trans = self._obtener_carga_por_codigo(df_cargas_totales, "VeoT")
                                viento_estructura_long = self._obtener_carga_por_codigo(df_cargas_totales, "VeoL")
                            else:
                                viento_estructura_trans = self._obtener_carga_por_codigo(df_cargas_totales, "VemedoT")
                                viento_estructura_long = self._obtener_carga_por_codigo(df_cargas_totales, "VemedoL")
                            cargas_hipotesis['V'] = [
                                viento_estructura_trans * factor_viento,
                                viento_estructura_long * factor_viento,
                                0.0
                            ]
                    
                    # CARGAS EN CONDUCTORES
                    nodos_conductor = [n for n in self.nodes_key.keys() if n.startswith(('C1_', 'C2_', 'C3_'))]
                    
                    for nodo in nodos_conductor:
                        carga_x, carga_y, carga_z = 0.0, 0.0, 0.0

                        if patron_tiro == "doble-terna-a-simple":
                            # Para conductores: aplicar patrón doble-terna-a-simple
                            tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_doble_terna_a_simple(
                                nodo, config_tiro, tiro_cond_base, es_guardia=False
                            )

                        elif patron_tiro == "unilateral":
                            es_unilateral = True
                            factor_peso_nodo = 0.5
                            factor_viento_nodo = 0.5
                            factor_cond = config_tiro.get("factor_cond", 1.0)
                            tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                                tiro_cond_base, self.alpha_quiebre, factor_cond
                            )
                        elif patron_tiro == "dos-unilaterales":
                            if self.tipo_estructura == "Terminal":
                                # Para Terminal: patrón inverso - todos menos un conductor se cargan con tiro unilateral
                                tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_dos_unilaterales_terminal(
                                    nodo, config_tiro, tiro_cond_base, es_guardia=False
                                )
                            else:
                                # Comportamiento original para otras estructuras
                                es_unilateral = (nodo in NODOS_DOS_UNILATERAL)
                                factor_peso_nodo = 0.5 if es_unilateral else 1.0
                                factor_viento_nodo = 0.5 if es_unilateral else 1.0
                                if es_unilateral:
                                    factor_cond = config_tiro.get("factor_cond", 1.0)
                                    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                                        tiro_cond_base, self.alpha_quiebre, factor_cond
                                    )
                                else:
                                    reduccion_cond = config_tiro.get("reduccion_cond", 0.0)
                                    tiro_trans, tiro_long = self._calcular_componentes_tiro(
                                        tiro_cond_base, self.alpha_quiebre, reduccion_cond, False
                                    )
                        else:  # bilateral
                            es_unilateral = False
                            factor_peso_nodo = 1.0
                            factor_viento_nodo = 1.0
                            reduccion_cond = config_tiro.get("reduccion_cond", 0.0)
                            tiro_trans, tiro_long = self._calcular_componentes_tiro(
                                tiro_cond_base, self.alpha_quiebre, reduccion_cond, False
                            )
                        
                        carga_x += tiro_trans
                        carga_y += tiro_long
                        carga_z = -peso_cond * factor_peso_nodo
                        
                        # VIENTO EN CABLES
                        if config["viento"]:
                            direccion_viento = config["viento"]["direccion"]
                            estado_v = config["viento"]["estado"]
                            factor_viento = config["viento"]["factor"]
                            
                            if direccion_viento == "Transversal":
                                if estado_v == "Vmax":
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "Vc")
                                else:
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed")
                                carga_x += viento_cond * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Longitudinal":
                                if estado_v == "Vmax":
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "VcL")
                                else:
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "VcmedL")
                                carga_y += viento_cond * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Oblicua":
                                if es_unilateral:
                                    lado = 1 if "L" in nodo else 2
                                    if estado_v == "Vmax":
                                        viento_cond_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vc_o_t_{lado}")
                                        viento_cond_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vc_o_l_{lado}")
                                    else:
                                        viento_cond_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcmed_o_t_{lado}")
                                        viento_cond_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcmed_o_l_{lado}")
                                    
                                    carga_x += viento_cond_x * factor_viento * factor_viento_nodo
                                    carga_y += viento_cond_y * factor_viento * factor_viento_nodo
                                else:
                                    if estado_v == "Vmax":
                                        viento_cond_x = (self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_t_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_t_2"))
                                        viento_cond_y = (self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_l_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_l_2"))
                                    else:
                                        viento_cond_x = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed_o_t_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed_o_t_2"))
                                        viento_cond_y = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed_o_l_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed_o_l_2"))
                                    
                                    carga_x += viento_cond_x * factor_viento * factor_viento_nodo
                                    carga_y += viento_cond_y * factor_viento * factor_viento_nodo
                        
                        # SOBRECARGA ADICIONAL
                        if config["sobrecarga"] and nodo == "C1_L":
                            carga_z -= config["sobrecarga"]
                        
                        cargas_hipotesis[nodo] = [round(carga_x, 2), round(carga_y, 2), round(carga_z, 2)]
                    
                    # CARGAS EN GUARDIA
                    nodos_guardia = [n for n in self.nodes_key.keys() if n.startswith('HG')]
                    
                    for nodo in nodos_guardia:
                        carga_x, carga_y, carga_z = 0.0, 0.0, 0.0

                        if patron_tiro == "doble-terna-a-simple":
                            # Para guardia: aplicar patrón doble-terna-a-simple
                            tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_doble_terna_a_simple(
                                nodo, config_tiro, tiro_guardia_base, es_guardia=True
                            )

                        elif patron_tiro == "unilateral":
                            es_unilateral = True
                            factor_peso_nodo = 0.5
                            factor_viento_nodo = 0.5
                            factor_guardia = config_tiro.get("factor_guardia", 1.0)
                            tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                                tiro_guardia_base, self.alpha_quiebre, factor_guardia
                            )
                        elif patron_tiro == "dos-unilaterales":
                            if self.tipo_estructura == "Terminal":
                                # Para Terminal: patrón inverso - todos menos un guardia se cargan con tiro unilateral
                                tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_dos_unilaterales_terminal(
                                    nodo, config_tiro, tiro_guardia_base, es_guardia=True
                                )
                            else:
                                # Comportamiento original para otras estructuras
                                es_unilateral = (nodo in NODOS_DOS_UNILATERAL)
                                factor_peso_nodo = 0.5 if es_unilateral else 1.0
                                factor_viento_nodo = 0.5 if es_unilateral else 1.0
                                if es_unilateral:
                                    factor_guardia = config_tiro.get("factor_guardia", 1.0)
                                    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                                        tiro_guardia_base, self.alpha_quiebre, factor_guardia
                                    )
                                else:
                                    reduccion_guardia = config_tiro.get("reduccion_guardia", 0.0)
                                    tiro_trans, tiro_long = self._calcular_componentes_tiro(
                                        tiro_guardia_base, self.alpha_quiebre, reduccion_guardia, True
                                    )
                        else:  # bilateral
                            es_unilateral = False
                            factor_peso_nodo = 1.0
                            factor_viento_nodo = 1.0
                            reduccion_guardia = config_tiro.get("reduccion_guardia", 0.0)
                            tiro_trans, tiro_long = self._calcular_componentes_tiro(
                                tiro_guardia_base, self.alpha_quiebre, reduccion_guardia, True
                            )
                        
                        carga_x += tiro_trans
                        carga_y += tiro_long
                        carga_z = -peso_guardia * factor_peso_nodo
                        
                        # VIENTO EN GUARDIA
                        if config["viento"]:
                            direccion_viento = config["viento"]["direccion"]
                            estado_v = config["viento"]["estado"]
                            factor_viento = config["viento"]["factor"]
                            
                            if direccion_viento == "Transversal":
                                if estado_v == "Vmax":
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, "Vcg")
                                else:
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, "Vcgmed")
                                carga_x += viento_guardia * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Longitudinal":
                                if estado_v == "Vmax":
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, "VcgL")
                                else:
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, "VcgmedL")
                                carga_y += viento_guardia * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Oblicua":
                                if es_unilateral:
                                    lado = 1
                                    if estado_v == "Vmax":
                                        viento_guardia_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg_o_t_{lado}")
                                        viento_guardia_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg_o_l_{lado}")
                                    else:
                                        viento_guardia_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcgmed_o_t_{lado}")
                                        viento_guardia_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcgmed_o_l_{lado}")
                                    
                                    carga_x += viento_guardia_x * factor_viento * factor_viento_nodo
                                    carga_y += viento_guardia_y * factor_viento * factor_viento_nodo
                                else:
                                    if estado_v == "Vmax":
                                        viento_guardia_x = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg_o_t_1") + 
                                                          self._obtener_carga_por_codigo(df_cargas_totales, "Vcg_o_t_2"))
                                        viento_guardia_y = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg_o_l_1") + 
                                                          self._obtener_carga_por_codigo(df_cargas_totales, "Vcg_o_l_2"))
                                    else:
                                        viento_guardia_x = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcgmed_o_t_1") + 
                                                          self._obtener_carga_por_codigo(df_cargas_totales, "Vcgmed_o_t_2"))
                                        viento_guardia_y = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcgmed_o_l_1") + 
                                                          self._obtener_carga_por_codigo(df_cargas_totales, "Vcgmed_o_l_2"))
                                    
                                    carga_x += viento_guardia_x * factor_viento * factor_viento_nodo
                                    carga_y += viento_guardia_y * factor_viento * factor_viento_nodo
                        
                        cargas_hipotesis[nodo] = [round(carga_x, 2), round(carga_y, 2), round(carga_z, 2)]
                    
                    self.cargas_key[nombre_completo] = cargas_hipotesis
                    print(f"✅ Cargas asignadas: {codigo_hip} - {config['desc']}")
                    
                except Exception as e:
                    print(f"❌ Error en hipótesis {codigo_hip}: {e}")
                    self.cargas_key[nombre_completo] = {nombre: [0.00, 0.00, 0.00] for nombre in self.nodes_key.keys()}
        else:
            print(f"❌ Tipo de estructura '{self.tipo_estructura}' no encontrado en hipótesis maestro")
        
        print(f"✅ Asignación completada: {len(self.cargas_key)} hipótesis procesadas")

    def generar_dataframe_cargas(self):
        """Genera DataFrame completo de cargas por nodo e hipótesis"""
        print(f"\n📊 GENERANDO DATAFRAME DE CARGAS...")
        
        if not self.cargas_key:
            print("❌ No hay cargas asignadas. Ejecutar asignar_cargas_hipotesis primero.")
            return None
        
        todos_nodos = list(self.nodes_key.keys())
        clave_busqueda = f"HIP_{self.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_')}_"
        hipotesis_filtradas = sorted([k for k in self.cargas_key.keys() if k.startswith(clave_busqueda)])
        
        # Crear multi-index
        nivel_superior = [''] * 2
        nivel_inferior = ['Nodo', 'Unidad']
        
        codigos_hipotesis = []
        for hip_larga in hipotesis_filtradas:
            partes = hip_larga.split('_')
            codigo_corto = partes[-3] if len(partes) > 3 else hip_larga
            codigos_hipotesis.append(codigo_corto)
            nivel_superior.extend([codigo_corto] * 3)
            nivel_inferior.extend(['x', 'y', 'z'])
        
        multi_index = pd.MultiIndex.from_arrays([nivel_superior, nivel_inferior])
        
        # Crear filas
        filas = []
        for nodo in todos_nodos:
            fila = [nodo, 'daN']
            
            for hip_larga in hipotesis_filtradas:
                cargas_nodo = self.cargas_key[hip_larga].get(nodo, [0.00, 0.00, 0.00])
                fila.extend(cargas_nodo)
            
            filas.append(fila)
        
        self.df_cargas_completo = pd.DataFrame(filas, columns=multi_index)
        
        print(f"✅ DataFrame creado: {len(self.df_cargas_completo)} nodos × {len(self.df_cargas_completo.columns)} columnas")
        return self.df_cargas_completo

    # ================= MÉTODOS DE VISUALIZACIÓN =================

    def graficar_estructura(self, zoom_cabezal=0.95, titulo_reemplazo=None):
        """Grafica la estructura completa"""
        print(f"\n🎨 GENERANDO GRÁFICO DE ESTRUCTURA...")
        
        plt.figure(figsize=(8, 12))
        
        # Determinar título
        tipo_estructura_titulo = titulo_reemplazo if titulo_reemplazo else self.tipo_estructura
        
        # Terreno
        plt.axhline(y=0, color=self.COLORES['terreno'], linewidth=3, alpha=0.7, label='Nivel del terreno')
        
        # Poste vertical
        altura_maxima = self.dimensiones.get('altura_total', 0)
        plt.plot([0, 0], [0, altura_maxima], color=self.COLORES['poste'], linewidth=4, label='Estructura')
        
        # Nodos centrales para mediciones
        nodos_centrales = ["BASE", "CROSS_H1", "CROSS_H2", "CROSS_H3"]
        if "HG1" in self.nodes_key and self.terna == "Doble" and self.cant_hg == 1:
            nodos_centrales.append("HG1")
        elif "TOP" in self.nodes_key:
            nodos_centrales.append("TOP")
        
        coordenadas_centrales = sorted([(n, self.nodes_key[n]) for n in nodos_centrales if n in self.nodes_key], 
                                      key=lambda x: x[1][2])
        
        # Anotar distancias entre nodos centrales
        for i in range(len(coordenadas_centrales)-1):
            dist = coordenadas_centrales[i+1][1][2] - coordenadas_centrales[i][1][2]
            if dist > 0:
                z_medio = (coordenadas_centrales[i][1][2] + coordenadas_centrales[i+1][1][2]) / 2
                plt.plot([0, 0.3], [z_medio, z_medio], color='gray', linestyle=':', alpha=0.7, linewidth=1)
                plt.annotate(f'{dist:.2f} m', xy=(0.3, z_medio), xytext=(5, 0), textcoords='offset points', 
                            fontsize=9, fontweight='bold', 
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8), 
                            verticalalignment='center')
        
        # Dibujar todos los nodos y conexiones
        for nombre, coordenadas in self.nodes_key.items():
            x, y, z = coordenadas
            
            if abs(y) > 0.001:  # Solo nodos en plano XZ
                continue
                
            # Nodos de conductor
            if nombre.startswith(('C1_', 'C2_', 'C3_')):
                plt.scatter(x, z, color=self.COLORES['conductor'], s=120, marker='o', 
                           edgecolors='white', linewidth=1.5, zorder=5)
                # Conectar con nodo de cruce correspondiente
                cross_node = f"CROSS_H{nombre[1]}"
                if cross_node in self.nodes_key:
                    plt.plot([x, self.nodes_key[cross_node][0]], [z, self.nodes_key[cross_node][2]], 
                            color=self.COLORES['poste'], linewidth=3, linestyle='-', alpha=1.0)
            
            # Nodos de guardia
            elif nombre.startswith('HG'):
                plt.scatter(x, z, color=self.COLORES['guardia'], s=120, marker='o', 
                           edgecolors='white', linewidth=1.5, zorder=5)
                # Conectar con TOP si existe
                if "TOP" in self.nodes_key:
                    plt.plot([x, self.nodes_key["TOP"][0]], [z, self.nodes_key["TOP"][2]], 
                            color=self.COLORES['poste'], linewidth=3, linestyle='-', alpha=1.0)
            
            # Nodo base
            elif "BASE" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=150, marker='s', zorder=5, label='Base')
            
            # Nodo top
            elif "TOP" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=120, marker='^', zorder=5, label='Top estructura')
        
        # Configurar ejes
        x_coords = [x for x, y, z in self.nodes_key.values()]
        z_coords = [z for x, y, z in self.nodes_key.values()]
        
        x_range = max(x_coords) - min(x_coords) if x_coords else 10
        z_range = max(z_coords) - min(z_coords) if z_coords else 15
        max_range = max(x_range, z_range)
        margin = max_range * 0.1
        
        x_center = (max(x_coords) + min(x_coords)) / 2 if x_coords else 0
        z_center = (max(z_coords) + min(z_coords)) / 2 if z_coords else altura_maxima / 2
        
        plt.xlim(x_center - max_range/2 - margin, x_center + max_range/2 + margin)
        plt.ylim(-1, z_center + max_range/2 + margin)
        
        # Etiquetas y título
        plt.xlabel('Distancia Horizontal X [m]', fontsize=11, fontweight='bold')
        plt.ylabel('Altura Z [m]', fontsize=11, fontweight='bold')
        plt.title(f'ESTRUCTURA {self.tension_nominal}kV - {self.zona_estructura.upper()} - {tipo_estructura_titulo.upper()} - {self.terna} Terna', 
                 fontsize=12, fontweight='bold', pad=15)
        
        # Leyenda
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=self.COLORES['conductor'], edgecolor='white', linewidth=1.5, label='Amarre de Conductores'),
            Patch(facecolor=self.COLORES['guardia'], edgecolor='white', linewidth=1.5, label='Cable guardia'),
            Patch(facecolor=self.COLORES['poste'], label='Estructura')
        ]
        plt.legend(handles=legend_elements, loc='upper right', framealpha=0.95)
        
        # Cuadrícula y aspecto
        plt.gca().set_aspect('equal', adjustable='box')
        plt.grid(True, alpha=0.15, linestyle='-', linewidth=0.5)
        
        # Información adicional
        info_text = f'H Libre: {altura_maxima:.2f} m\nMénsula: {self.dimensiones.get("lmen_adoptada", 0):.1f} m\nTipo: {tipo_estructura_titulo}\nTerna: {self.terna}\nCables guardia: {self.cant_hg}'
        plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, fontsize=9, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8), verticalalignment='top')
        
        plt.text(0.98, 0.85, f'Altura Libre Total: {altura_maxima:.2f} m', transform=plt.gca().transAxes, 
                fontsize=10, fontweight='bold', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.9), 
                horizontalalignment='right', verticalalignment='top')
        
        plt.tight_layout()
        plt.show()
        
        print(f"✅ Gráfico de estructura generado")

    def _dibujar_cadena(self, nodo_amarre, angulo=0, etiqueta=None, radio=None, color_circulo='gray'):
        """Dibuja una cadena de aisladores con declinación opcional y círculo de distancia"""
        if nodo_amarre not in self.nodes_key:
            return None, None

        x_amarre, y_amarre, z_amarre = self.nodes_key[nodo_amarre]
        ang_rad = math.radians(angulo)
        x_conductor = x_amarre + self.lk * math.sin(ang_rad)
        z_conductor = z_amarre - self.lk * math.cos(ang_rad)

        # Dibujar la cadena (línea)
        label_cadena = 'Cadena' if 'C1_L' in nodo_amarre and angulo > 0 else ""
        plt.plot([x_amarre, x_conductor], [z_amarre, z_conductor], color=self.COLORES['cadena'], 
                linewidth=2, label=label_cadena)

        # Dibujar el extremo del conductor
        label_conductor = 'Extremo conductor' if 'C1_L' in nodo_amarre and angulo > 0 else ""
        plt.scatter(x_conductor, z_conductor, color=self.COLORES['conductor_end'], s=80, marker='o', 
                edgecolors='white', linewidth=1.5, zorder=5, label=label_conductor)

        # Dibujar círculo de distancia si se especifica
        if radio and radio > 0:
            label_circulo = etiqueta if 'C1_L' in nodo_amarre and angulo > 0 else ""
            plt.gca().add_patch(plt.Circle((x_conductor, z_conductor), radio, color=color_circulo, 
                                        fill=False, linestyle='--', linewidth=1.5, alpha=0.7,
                                        label=label_circulo))

            # Etiquetas de distancia
            if etiqueta == 's (fase-estructura)':
                plt.annotate(etiqueta, xy=(x_conductor, z_conductor - radio), xytext=(0, -8),
                            textcoords='offset points', fontsize=8, fontweight='bold', color=color_circulo, 
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8), 
                            horizontalalignment='center', verticalalignment='top')
                plt.annotate(f'{radio:.2f} m', xy=(x_conductor, z_conductor - radio), xytext=(0, -23),
                            textcoords='offset points', fontsize=8, fontweight='bold', color=color_circulo,
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8),
                            horizontalalignment='center', verticalalignment='top')
            else:
                offset_vertical = 0.017
                plt.annotate(etiqueta, xy=(x_conductor + radio/2, z_conductor + offset_vertical), 
                            xytext=(5, 2), textcoords='offset points', fontsize=8, fontweight='bold', 
                            color=color_circulo, 
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8), 
                            verticalalignment='bottom')
                plt.annotate(f'{radio:.2f} m', xy=(x_conductor + radio/2, z_conductor - offset_vertical), 
                            xytext=(5, -2), textcoords='offset points', fontsize=8, fontweight='bold', 
                            color=color_circulo,
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8), 
                            verticalalignment='top')

        return x_conductor, z_conductor

    def graficar_cabezal(self, zoom_cabezal=0.7, titulo_reemplazo=None):
        """Grafica el cabezal usando los parámetros calculados durante el dimensionamiento"""
        print(f"\n🎨 GENERANDO GRÁFICO DE CABEZAL...")
        
        plt.figure(figsize=(12, 10))
        
        # Determinar título
        tipo_estructura_titulo = titulo_reemplazo if titulo_reemplazo else self.tipo_estructura
        
        # Obtener parámetros del cabezal
        if not hasattr(self, 'parametros_cabezal'):
            print("❌ No se han calculado los parámetros del cabezal. Ejecutar dimensionar_unifilar primero.")
            return
        
        theta_max = self.parametros_cabezal['theta_max'].iloc[0]
        D_fases = self.parametros_cabezal['D_fases'].iloc[0]
        s_estructura = self.parametros_cabezal['s_estructura'].iloc[0]
        Dhg = self.parametros_cabezal['Dhg'].iloc[0]
        altura_total = self.dimensiones.get('altura_total', 0)
        
        # 1. DIBUJAR POSTE Y MENSULAS
        alturas_nodos = [coord[2] for coord in self.nodes_key.values()]
        if alturas_nodos:
            altura_min_plot = min(alturas_nodos) - 1
        else:
            altura_min_plot = 0
        
        plt.plot([0, 0], [altura_min_plot, altura_total], color=self.COLORES['poste'], linewidth=4, label='Estructura')
        
        # DIBUJAR MENSULAS HORIZONTALES
        nodos_conductor = [n for n in self.nodes_key.keys() if n.startswith(('C1_', 'C2_', 'C3_'))]
        for nodo in nodos_conductor:
            x_nodo, y_nodo, z_nodo = self.nodes_key[nodo]
            # Buscar nodo de cruce más cercano en altura
            altura_cruce = z_nodo
            cross_node = None
            min_diff = float('inf')
            
            for cross_name, cross_coord in self.nodes_key.items():
                if "CROSS" in cross_name:
                    diff = abs(cross_coord[2] - altura_cruce)
                    if diff < min_diff:
                        min_diff = diff
                        cross_node = cross_name
            
            if cross_node:
                x_cross, y_cross, z_cross = self.nodes_key[cross_node]
                # Dibujar ménsula horizontal
                plt.plot([x_cross, x_nodo], [z_cross, z_nodo], 
                        color=self.COLORES['poste'], linewidth=3, alpha=0.8)
        
        # 2. APANTALLAMIENTO (solo si hay guardia)
        nodos_guardia = [n for n in self.nodes_key.keys() if n.startswith('HG')]
        if nodos_guardia:
            h_guardia = self.dimensiones.get('hhg', 0)
            h1a = self.dimensiones.get('h1a', 0)
            angulo_apant = 30
            
            lmenhg = self.dimensiones.get('lmenhg', 0)
            
            # Determinar posiciones de guardia
            if len(nodos_guardia) == 1:
                x_hg = self.nodes_key[nodos_guardia[0]][0]
                x_hg_izq, x_hg_der = x_hg, x_hg
            else:
                x_hg_izq = min(self.nodes_key[hg][0] for hg in nodos_guardia)
                x_hg_der = max(self.nodes_key[hg][0] for hg in nodos_guardia)
            
            x_izq_extremo = x_hg_izq - (h_guardia - h1a) * math.tan(math.radians(angulo_apant))
            x_der_extremo = x_hg_der + (h_guardia - h1a) * math.tan(math.radians(angulo_apant))
            
            for x_hg, x_ext in [(x_hg_izq, x_izq_extremo), (x_hg_der, x_der_extremo)]:
                plt.plot([x_hg, x_ext], [h_guardia, h1a], color=self.COLORES['apantallamiento'],
                        linestyle='--', alpha=0.7, linewidth=1.5, 
                        label=f'Apantallamiento {angulo_apant}°' if x_hg == x_hg_izq else "")
            
            # Rellenar zona protegida
            x_fill, z_fill = [x_izq_extremo, x_hg_izq, x_hg_der, x_der_extremo], [h1a, h_guardia, h_guardia, h1a]
            plt.fill(x_fill, z_fill, color=self.COLORES['apantallamiento'], alpha=0.1)
            
            # Etiqueta ángulo apantallamiento
            plt.annotate(f'Ángulo: {angulo_apant}°', xy=(x_hg_izq - 0.5, (h_guardia + h1a) / 2),
                        xytext=(-5, 0), textcoords='offset points', fontsize=8, fontweight='bold', 
                        color=self.COLORES['texto_verde'], 
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8), 
                        horizontalalignment='right')
        
        # 3. DIBUJAR CADENAS CON DECLINACIÓN (usando theta_max calculado)
        puntos_conductor = {}
        
        for nodo in nodos_conductor:
            if nodo.endswith('_L') and "C1" in nodo:  # Primer conductor izquierdo (declinado)
                x, z = self._dibujar_cadena(nodo, angulo=theta_max, 
                                        etiqueta='s (fase-estructura)', 
                                        radio=s_estructura)
            elif nodo.endswith('_R') and "C2" in nodo:  # Conductor para distancia entre fases
                x, z = self._dibujar_cadena(nodo, etiqueta='D (entre fases)', 
                                        radio=D_fases)
            elif nodo.endswith('_L') and "C3" in nodo:  # Conductor para distancia guardia-conductor
                x, z = self._dibujar_cadena(nodo, etiqueta='Dhg (guardia-conductor)', 
                                        radio=Dhg,
                                        color_circulo=self.COLORES['dhg_circulo'])
            else:
                x, z = self._dibujar_cadena(nodo)  # Cadenas normales
            
            if x is not None:
                puntos_conductor[nodo] = (x, z)
        
        # 4. DIBUJAR NODOS Y CONEXIONES RESTANTES
        for nombre, coordenadas in self.nodes_key.items():
            x, y, z = coordenadas
            
            if abs(y) > 0.001:  # Solo plano XZ
                continue
                
            # Nodos de cruce
            if "CROSS" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=80, marker='o', zorder=5, 
                        label='Cruce poste-ménsula' if nombre == 'CROSS_H1' else "")
            
            # Nodos de conductor (puntos de amarre)
            elif nombre.startswith(('C1_', 'C2_', 'C3_')):
                if nombre not in puntos_conductor:  # Solo si no se dibujó ya
                    plt.scatter(x, z, color=self.COLORES['conductor'], s=100, marker='o', 
                            edgecolors='white', linewidth=1.5, zorder=5, 
                            label='Punto amarre' if nombre == 'C1_L' else "")
            
            # Nodos de guardia
            elif nombre.startswith('HG'):
                plt.scatter(x, z, color=self.COLORES['guardia'], s=100, marker='o', 
                        edgecolors='white', linewidth=1.5, zorder=5, 
                        label='Cable guardia' if nombre == nodos_guardia[0] else "")
                
                # Conectar con TOP si existe
                if "TOP" in self.nodes_key:
                    top_x, top_y, top_z = self.nodes_key["TOP"]
                    plt.plot([x, top_x], [z, top_z], color=self.COLORES['poste'], 
                            linewidth=2, alpha=0.8)
            
            # Nodo top
            elif "TOP" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=120, marker='^', zorder=5, 
                        label='Top estructura')
        
        # 5. CONFIGURACIÓN DE EJES CON ZOOM MEJORADO EN CABEZAL
        # Calcular límites basados en D_fases
        h1a = self.dimensiones.get('h1a', 0)
        hhg = self.dimensiones.get('hhg', 0)
        
        # Límites verticales: desde conductor más bajo - D hasta punto más alto + D
        z_min_cabezal = h1a - D_fases
        z_max_cabezal = hhg + D_fases
        
        # Límites horizontales: 3 D's centrados
        x_center = 0
        x_range_cabezal = 3 * D_fases
        
        # Aplicar zoom
        zoom_factor = zoom_cabezal if zoom_cabezal > 0 else 0.7
        plt.xlim(x_center - x_range_cabezal/2 * zoom_factor, x_center + x_range_cabezal/2 * zoom_factor)
        plt.ylim(z_min_cabezal, z_max_cabezal)
        
        # 6. CUADRÍCULA DETALLADA
        x_min, x_max = plt.xlim()
        z_min, z_max = plt.ylim()
        x_ticks = np.arange(np.floor(x_min * 10) / 10, np.ceil(x_max * 10) / 10 + 0.1, 0.1)
        z_ticks = np.arange(np.floor(z_min * 10) / 10, np.ceil(z_max * 10) / 10 + 0.1, 0.1)
        plt.gca().set_xticks(x_ticks, minor=True)
        plt.gca().set_yticks(z_ticks, minor=True)
        plt.grid(which='minor', color='lightgray', linestyle='-', linewidth=0.4, alpha=0.5)
        plt.grid(which='major', alpha=0.2, linestyle='-', linewidth=0.7)
        
        # 7. TÍTULOS Y ETIQUETAS
        plt.xlabel('Distancia Horizontal X [m]', fontsize=11, fontweight='bold')
        plt.ylabel('Altura Z [m]', fontsize=11, fontweight='bold')
        plt.title(f'CABEZAL DE ESTRUCTURA - DETALLE CADENAS Y DISTANCIAS', 
                fontsize=12, fontweight='bold', pad=15)
        
        terna_formato = "Doble Terna" if self.terna == "Doble" else "Simple Terna"
        plt.title(f'{self.tension_nominal}kV - {tipo_estructura_titulo.upper()} - {self.disposicion.upper()} - {terna_formato}', 
                fontsize=10, pad=10)
        
        # 8. LEYENDA SIMPLIFICADA
        from matplotlib.patches import Patch
        leyenda = [
            Patch(facecolor=self.COLORES['conductor'], edgecolor='white', linewidth=1.5, label='Punto amarre'),
            Patch(facecolor=self.COLORES['conductor_end'], edgecolor='white', linewidth=1.5, label='Extremo conductor'),
            Patch(facecolor=self.COLORES['guardia'], edgecolor='white', linewidth=1.5, label='Cable guardia'),
            Patch(facecolor=self.COLORES['poste'], label='Estructura'),
            plt.Line2D([0], [0], color=self.COLORES['cadena'], linewidth=2, label='Cadena'),
            plt.Line2D([0], [0], color=self.COLORES['circulo'], linestyle='--', linewidth=1.5, label='D (entre fases)'),
            plt.Line2D([0], [0], color=self.COLORES['circulo'], linestyle='--', linewidth=1.5, label='s (fase-estructura)'),
            plt.Line2D([0], [0], color=self.COLORES['dhg_circulo'], linestyle='--', linewidth=1.5, label='Dhg (guardia-conductor)'),
        ]
        
        # Agregar apantallamiento solo si existe
        if nodos_guardia:
            leyenda.append(
                plt.Line2D([0], [0], color=self.COLORES['apantallamiento'], linestyle='--', linewidth=1.5, 
                        label=f'Apantallamiento {angulo_apant}°')
            )
        
        plt.legend(handles=leyenda, loc='upper right', framealpha=0.95)
        
        # 9. INFORMACIÓN TÉCNICA
        info_text = f'H libre: {altura_total:.2f} m\nMénsula: {self.dimensiones.get("lmen_adoptada", 0):.2f} m\nTipo: {tipo_estructura_titulo}\nTerna: {self.terna}\nCables guardia: {self.cant_hg}'
        plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8), verticalalignment='top')
        
        # Altura libre
        plt.text(0.98, 0.85, f'Altura Libre: {altura_total:.2f} m', transform=plt.gca().transAxes, 
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.9), 
                horizontalalignment='right', verticalalignment='top')
        
        # Etiqueta theta para conductor declinado
        if theta_max > 0 and 'C1_L' in puntos_conductor:
            x_med = (self.nodes_key['C1_L'][0] + puntos_conductor['C1_L'][0]) / 2
            z_med = (self.nodes_key['C1_L'][2] + puntos_conductor['C1_L'][1]) / 2
            plt.annotate(f'θ = {theta_max:.1f}°', xy=(x_med, z_med), xytext=(-20, 0), 
                        textcoords='offset points', fontsize=9, fontweight='bold', 
                        color=self.COLORES['cadena'],
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8), 
                        horizontalalignment='right', verticalalignment='center')
        
        plt.gca().set_aspect('equal', adjustable='box')
        plt.tight_layout()
        plt.show()
        
        print(f"✅ Gráfico de cabezal generado (theta_max: {theta_max:.1f}°)")

    def imprimir_datos_dimensionamiento(self, vano, flecha_max_conductor, flecha_max_guardia):
        """Imprime en consola los datos de dimensionamiento similares al código de ejemplo"""
        
        print(f"\n📐 DIMENSIONES MÍNIMAS - {self.zona_estructura.upper()} - {self.tension_nominal}kV - {self.tipo_estructura.upper()}")
        print(f"{'Parámetro':<50} {'Valor':<12} {'Unidad':<10}")
        print("-" * 80)
        
        # Obtener theta_max del cálculo real
        theta_max = self.parametros_cabezal['theta_max'].iloc[0]
        
        # CORRECCIÓN: Obtener valores de parametros_cabezal O de dimensiones (prioridad a parametros_cabezal)
        if hasattr(self, 'parametros_cabezal') and not self.parametros_cabezal.empty:
            D_fases = self.parametros_cabezal['D_fases'].iloc[0]
            s_estructura = self.parametros_cabezal['s_estructura'].iloc[0]
            Dhg = self.parametros_cabezal['Dhg'].iloc[0]
        else:
            # Fallback a dimensiones
            D_fases = self.dimensiones.get('D_fases', 0.0)
            s_estructura = self.dimensiones.get('s_estructura', 0.0)
            Dhg = self.dimensiones.get('Dhg', 0.0)
        
        # Resto del método igual pero usando las variables correctas...
        params = [
            ("Tipo de estructura", self.tipo_estructura, ""),
            ("TERNA", self.terna, ""),
            ("Disposición", self.disposicion, ""),
            ("Tensión nominal (Vn)", f"{self.tension_nominal:.1f}", "kV"),
            ("Tensión máxima (Vm)", f"{self.tension_maxima:.1f}", "kV"),
            ("Altura mínima sobre terreno", f"{self.altura_minima_terreno:.2f}", "m"),
            ("Componente eléctrico (b)", f"{0.01 * (self.tension_nominal/math.sqrt(3) - 22) if self.tension_nominal > 33 else 0.0:.2f}", "m"),
            ("Altura base eléctrica adoptada", f"{self.altura_minima_terreno + self.hadd:.2f}", "m"),
            ("Ángulo declinación máximo", f"{theta_max:.1f}", "°"),
            ("Coeficiente k", f"{self._obtener_coeficiente_k(theta_max):.2f}", ""),
            ("Distancia mín. entre fases (D)", f"{D_fases:.2f}", "m"),
            ("Distancia mín. guardia-fase (Dhg)", f"{Dhg:.2f}", "m"),
            ("Distancia mín. fase-estructura (s)", f"{s_estructura:.2f}", "m"),
            ("Altura adicional (HADD)", f"{self.hadd:.2f}", "m"),
            ("Distancia adicional vertical entre fases", f"{self.hadd_entre_amarres:.2f}", "m"),
            ("", "", ""),
            ("Alturas de Sujeción", "", ""),
            ("Primer amarre (h1a)", f"{self.dimensiones.get('h1a', 0):.2f}", "m"),
            ("Segundo amarre (h2a)", f"{self.dimensiones.get('h2a', 0):.2f}", "m"),
            ("Tercer amarre (h3a)", f"{self.dimensiones.get('h3a', 0):.2f}", "m"),
            ("Cable guardia (hhg)", f"{self.dimensiones.get('hhg', 0):.2f}", "m"),
            ("Longitud ménsula adoptada conductor", f"{self.dimensiones.get('lmen_adoptada', 0):.2f}", "m"),
            ("Longitud ménsula adoptada guardia", f"{self.dimensiones.get('lmenhg', 0):.2f} {'(CENTRADO)' if self.dimensiones.get('lmenhg', 0) == 0 else ''}", "m")
        ]
        
        for param, val, unit in params:
            if param == "":
                print("-" * 80)
            else:
                print(f"{param:<50} {val:<12} {unit:<10}")
        
        # CÁLCULO DE APANTALLAMIENTO
        print(f"\n🛡️  CÁLCULO DE APANTALLAMIENTO - TERNA {self.terna}")
        print(f"{'Parámetro':<40} {'Valor':<8} {'Unidad':<10}")
        print("-" * 60)
        
        h_conductor_real = self.dimensiones.get('h3a' if self.terna == "Doble" else 'h2a' if self.disposicion == "triangular" else 'h1a', 0) - self.lk
        hhg = self.dimensiones.get('hhg', 0)
        distancia_vertical_final = hhg - h_conductor_real
        
        if self.terna == "Doble" and self.cant_hg == 1:
            distancia_horizontal_max = self.dimensiones.get('lmen_adoptada', 0)
            angulo_apantallamiento_real = math.degrees(math.atan(distancia_horizontal_max / distancia_vertical_final))
            distancia_diagonal_final = math.sqrt(distancia_horizontal_max**2 + distancia_vertical_final**2)
            
            apant_params = [
                ("Tipo de terna", self.terna, ""), 
                ("Cant. cables guardia", f"{self.cant_hg}", ""),
                ("Altura conductor real más alto", f"{h_conductor_real:.2f}", "m"),
                ("Altura final cable guardia", f"{hhg:.2f}", "m"), 
                ("Distancia vertical final", f"{distancia_vertical_final:.2f}", "m"),
                ("Distancia horizontal máxima", f"{distancia_horizontal_max:.2f}", "m"),
                ("Ángulo apantallamiento real", f"{angulo_apantallamiento_real:.1f}", "°"),
                ("Distancia diagonal final", f"{distancia_diagonal_final:.2f}", "m"),
                ("Distancia mínima requerida (Dhg)", f"{Dhg:.2f}", "m"),  # CORREGIDO
                ("Cumple ángulo 30°", "Sí" if angulo_apantallamiento_real <= 30 else "No", ""),
                ("Cumple distancia mínima", "Sí" if distancia_diagonal_final >= Dhg else "No", ""),  # CORREGIDO
                ("Cobertura efectiva", "Sí" if self.dimensiones.get('cobertura_efectiva', False) else "No", "")
            ]
        else:
            if self.terna == "Simple" and self.cant_hg == 1:
                distancia_horizontal_efectiva = self.dimensiones.get('lmen_adoptada', 0) + self.dimensiones.get('lmenhg', 0)
            elif self.terna == "Doble" and self.cant_hg == 2:
                distancia_horizontal_efectiva = self.dimensiones.get('lmen_adoptada', 0) - self.dimensiones.get('lmenhg', 0)
                if distancia_horizontal_efectiva < 0:
                    distancia_horizontal_efectiva = 0
            else:
                distancia_horizontal_efectiva = 0
                
            angulo_apantallamiento_real = math.degrees(math.atan(distancia_horizontal_efectiva / distancia_vertical_final))
            distancia_diagonal_final = math.sqrt(distancia_horizontal_efectiva**2 + distancia_vertical_final**2)
            
            apant_params = [
                ("Tipo de terna", self.terna, ""), 
                ("Cant. cables guardia", f"{self.cant_hg}", ""),
                ("Altura conductor real más alto", f"{h_conductor_real:.2f}", "m"),
                ("Altura final cable guardia", f"{hhg:.2f}", "m"), 
                ("Distancia vertical final", f"{distancia_vertical_final:.2f}", "m"),
                ("Ménsula guardia", f"{self.dimensiones.get('lmenhg', 0):.2f}", "m"),
                ("Distancia horizontal efectiva", f"{distancia_horizontal_efectiva:.2f}", "m"),
                ("Ángulo apantallamiento real", f"{angulo_apantallamiento_real:.1f}", "°"),
                ("Distancia diagonal final", f"{distancia_diagonal_final:.2f}", "m"),
                ("Distancia mínima requerida (Dhg)", f"{Dhg:.2f}", "m"),  # CORREGIDO
                ("Cumple ángulo 30°", "Sí" if angulo_apantallamiento_real <= 30 else "No", ""),
                ("Cumple distancia mínima", "Sí" if distancia_diagonal_final >= Dhg else "No", ""),  # CORREGIDO
                ("Cobertura efectiva", "Sí" if self.dimensiones.get('cobertura_efectiva', False) else "No", "")
            ]

        for param, val, unit in apant_params: 
            print(f"{param:<40} {val:<8} {unit:<10}")

        print(f"\nVariables guardadas: h1a, h2a, h3a, hhg, lmen_adoptada, lmenhg, D_fases, s_estructura, Dhg, nodes_key")
        print(f"Cobertura efectiva: {'SÍ' if self.dimensiones.get('cobertura_efectiva', False) else 'NO'}")


    def guardar_resultados(self, folder):
        """Guarda todos los resultados en archivos CSV"""
        import os
        
        print(f"\n💾 GUARDANDO RESULTADOS...")
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
        
        # 3. Guardar cargas si existen
        if self.df_cargas_completo is not None:
            ruta_cargas = f"{folder}/8_{self.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_').lower()}_CARGAS_POO.csv"
            self.df_cargas_completo.to_csv(ruta_cargas, index=False, encoding='utf-8')
            print(f"✅ Cargas guardadas: {ruta_cargas}")
        
        # 4. Guardar información de estructura
        info_df = pd.DataFrame([self.info_estructura()])
        ruta_info = f"{folder}/9_{self.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_').lower()}_INFO_POO.csv"
        info_df.to_csv(ruta_info, index=False, encoding='utf-8')
        print(f"✅ Información guardada: {ruta_info}")
        
        print(f"✅ Todos los resultados guardados en: {folder}")

    def calcular_reacciones_tiros_cima(self, nodo_apoyo="BASE", nodo_cima=None):
        """
        Calcula reacciones en el nodo de apoyo y tiros equivalentes en la cima
        
        Args:
            nodo_apoyo (str): Nodo considerado como apoyo (por defecto "BASE")
            nodo_cima (str): Nodo considerado como cima (por defecto se autodetecta)
        """
        print(f"\n🔧 CÁLCULO DE REACCIONES Y TIROS EN CIMA")
        print(f"   Apoyo: {nodo_apoyo}, Cima: {nodo_cima if nodo_cima else 'Auto-detectar'}")
        
        # 1. DETECTAR NODO CIMA SI NO SE ESPECIFICA
        if nodo_cima is None:
            if "TOP" in self.nodes_key:
                nodo_cima = "TOP"
            elif "HG1" in self.nodes_key:
                nodo_cima = "HG1"
            else:
                # Buscar el nodo más alto
                nodo_cima = max(self.nodes_key.items(), key=lambda x: x[1][2])[0]
        
        # 2. VERIFICAR QUE EXISTEN LOS NODOS
        if nodo_apoyo not in self.nodes_key:
            raise ValueError(f"Nodo de apoyo '{nodo_apoyo}' no encontrado")
        if nodo_cima not in self.nodes_key:
            raise ValueError(f"Nodo cima '{nodo_cima}' no encontrado")
        
        # 3. OBTENER COORDENADAS
        x_apoyo, y_apoyo, z_apoyo = self.nodes_key[nodo_apoyo]
        x_cima, y_cima, z_cima = self.nodes_key[nodo_cima]
        
        altura_efectiva = z_cima - z_apoyo
        print(f"   Altura efectiva: {altura_efectiva:.2f} m")
        
        # 4. CALCULAR REACCIONES PARA CADA HIPÓTESIS
        self.resultados_reacciones = {}
        
        for nombre_hipotesis, cargas_nodo in self.cargas_key.items():
            # Inicializar reacciones
            Fx, Fy, Fz = 0.0, 0.0, 0.0
            Mx, My, Mz = 0.0, 0.0, 0.0
            
            for nodo, carga in cargas_nodo.items():
                if nodo != nodo_apoyo:  # No considerar el propio nodo de apoyo
                    x, y, z = self.nodes_key[nodo]
                    Fx_n, Fy_n, Fz_n = carga
                    
                    # Sumatoria de fuerzas
                    Fx += Fx_n
                    Fy += Fy_n
                    Fz += Fz_n
                    
                    # Vector posición relativa
                    rx, ry, rz = x - x_apoyo, y - y_apoyo, z - z_apoyo
                    
                    # Cálculo de momentos - producto vectorial r × F
                    Mx += (ry * Fz_n) - (rz * Fy_n)
                    My += (rz * Fx_n) - (rx * Fz_n)
                    Mz += (rx * Fy_n) - (ry * Fx_n)
            
            # 5. REDUCIR MOMENTOS A TIROS EN CIMA
            Tiro_X = My / altura_efectiva if altura_efectiva > 0 else 0.0
            Tiro_Y = -Mx / altura_efectiva if altura_efectiva > 0 else 0.0
            Tiro_resultante = math.sqrt(Tiro_X**2 + Tiro_Y**2)
            
            # Cálculo del ángulo
            if Tiro_resultante > 0:
                angulo_rad = math.atan2(Tiro_Y, Tiro_X)
                angulo_grados = math.degrees(angulo_rad)
                if angulo_grados < 0:
                    angulo_grados += 360
            else:
                angulo_grados = 0.0
            
            # Almacenar resultados
            self.resultados_reacciones[nombre_hipotesis] = {
                'Reaccion_Fx_daN': round(Fx, 1),
                'Reaccion_Fy_daN': round(Fy, 1),
                'Reaccion_Fz_daN': round(Fz, 1),
                'Reaccion_Mx_daN_m': round(Mx, 1),
                'Reaccion_My_daN_m': round(My, 1),
                'Reaccion_Mz_daN_m': round(Mz, 1),
                'Tiro_X_daN': round(Tiro_X, 1),
                'Tiro_Y_daN': round(Tiro_Y, 1),
                'Tiro_resultante_daN': round(Tiro_resultante, 1),
                'Angulo_grados': round(angulo_grados, 1),
                'Nodo_apoyo': nodo_apoyo,
                'Nodo_cima': nodo_cima,
                'Altura_efectiva_m': round(altura_efectiva, 2)
            }
        
        # 6. CREAR DATAFRAME CON RESULTADOS
        self.df_reacciones = pd.DataFrame.from_dict(self.resultados_reacciones, orient='index')
        
        print(f"✅ Cálculo completado: {len(self.resultados_reacciones)} hipótesis procesadas")
        return self.df_reacciones
    
    def imprimir_reacciones_tiros(self, mostrar_c2=True):
        """
        Imprime tabla resumen de reacciones y tiros en cima
        """
        if not hasattr(self, 'df_reacciones'):
            print("❌ No hay datos de reacciones. Ejecutar calcular_reacciones_tiros_cima primero.")
            return
        
        print(f"\n{'='*120}")
        print("TABLA RESUMEN - REACCIONES Y TIROS EQUIVALENTES EN LA CIMA")
        print(f"{'='*120}")
        
        # Filtrar hipótesis C2 si corresponde
        df_mostrar = self.df_reacciones.copy()
        if not mostrar_c2:
            df_mostrar = df_mostrar[~df_mostrar.index.str.contains('_C2_')]
        
        # Crear tabla formateada
        tabla_resumen = []
        for hipotesis, datos in df_mostrar.iterrows():
            # Extraer código corto de hipótesis
            codigo = hipotesis.split('_')[-2] if len(hipotesis.split('_')) >= 2 else hipotesis
            
            fila = [
                codigo,
                f"{datos['Reaccion_Fx_daN']:7.1f}",
                f"{datos['Reaccion_Fy_daN']:7.1f}",
                f"{datos['Reaccion_Fz_daN']:7.1f}",
                f"{datos['Reaccion_Mx_daN_m']:7.1f}",
                f"{datos['Reaccion_My_daN_m']:7.1f}",
                f"{datos['Reaccion_Mz_daN_m']:7.1f}",
                f"{datos['Tiro_X_daN']:6.1f}",
                f"{datos['Tiro_Y_daN']:6.1f}",
                f"{datos['Tiro_resultante_daN']:6.1f}",
                f"{datos['Angulo_grados']:5.1f}"
            ]
            tabla_resumen.append(fila)
        
        # Encabezados
        headers = ["Hipótesis", "Fx [daN]", "Fy [daN]", "Fz [daN]", "Mx [daN·m]", "My [daN·m]", "Mz [daN·m]", 
                  "Tiro_X [daN]", "Tiro_Y [daN]", "Tiro_Res [daN]", "Ángulo [°]"]
        
        # Mostrar tabla
        try:
            from tabulate import tabulate
            print(tabulate(tabla_resumen, headers=headers, tablefmt='grid'))
        except ImportError:
            # Tabla básica
            print(" | ".join(headers))
            print("-" * len(" | ".join(headers)))
            for fila in tabla_resumen:
                print(" | ".join(fila))
        
        # RESUMEN EJECUTIVO
        print(f"\n{'='*80}")
        print("RESUMEN EJECUTIVO")
        print(f"{'='*80}")
        
        max_tiro = df_mostrar['Tiro_resultante_daN'].max()
        max_fz = df_mostrar['Reaccion_Fz_daN'].max()
        hip_max_tiro = df_mostrar['Tiro_resultante_daN'].idxmax()
        hip_max_fz = df_mostrar['Reaccion_Fz_daN'].idxmax()
        
        print(f"Estructura: {self.tension_nominal}kV - {self.tipo_estructura}")
        print(f"Altura efectiva: {df_mostrar['Altura_efectiva_m'].iloc[0]:.2f} m")
        print(f"Nodo apoyo: {df_mostrar['Nodo_apoyo'].iloc[0]}, Nodo cima: {df_mostrar['Nodo_cima'].iloc[0]}")
        print(f"\n🔴 Hipótesis más desfavorable por tiro en cima:")
        print(f"   {hip_max_tiro}: {max_tiro:.1f} daN")
        print(f"\n🔴 Hipótesis más desfavorable por carga vertical:")
        print(f"   {hip_max_fz}: {max_fz:.1f} daN")
    
    def diagrama_polar_tiros(self, titulo=None):
        """
        Genera diagrama polar de tiros en cima
        """
        if not hasattr(self, 'df_reacciones'):
            print("❌ No hay datos de reacciones. Ejecutar calcular_reacciones_tiros_cima primero.")
            return
        
        print(f"\n🎨 GENERANDO DIAGRAMA POLAR DE TIROS EN CIMA...")
        
        plt.figure(figsize=(10, 8))
        ax = plt.subplot(111, projection='polar')
        
        # Colores para hipótesis
        colores_hipotesis = {
            'A1': '#FF0000', 'A2': '#00FF00', 'A3': '#0000FF', 'A4': "#7A7A7A",
            'A5': '#FF00FF', 'B1': '#00FFFF', 'B2': '#FF8000', 'C1': '#8000FF', 'C2': '#008000'
        }
        
        # Plotear cada hipótesis
        max_tiro = 0
        for hipotesis, datos in self.df_reacciones.iterrows():
            # Extraer código corto
            codigo = hipotesis.split('_')[-2] if len(hipotesis.split('_')) >= 2 else hipotesis
            
            angulo_rad = math.radians(datos['Angulo_grados'])
            magnitud = datos['Tiro_resultante_daN']
            color = colores_hipotesis.get(codigo, '#000000')
            
            # Plotear vector (sumando 90° para visualización)
            angulo_visual = angulo_rad + math.radians(90)
            ax.plot([0, angulo_visual], [0, magnitud], linewidth=2, color=color, 
                   label=f"{codigo}: {magnitud:.1f} daN", alpha=0.7)
            ax.plot(angulo_visual, magnitud, 'o', color=color, markersize=6)
            
            max_tiro = max(max_tiro, magnitud)
        
        # Configurar gráfico polar
        ax.set_theta_offset(math.pi)  # 0° a la izquierda
        ax.set_theta_direction(-1)    # Sentido horario
        
        # Ajustar límites
        ax.set_ylim(0, max_tiro * 1.2)
        ax.grid(True, alpha=0.3)
        
        # Añadir rótulos de ángulos
        ax.set_xticks(np.linspace(0, 2*math.pi, 8, endpoint=False))
        ax.set_xticklabels(['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°'])
        
        # Título
        titulo_grafico = titulo if titulo else f'DIAGRAMA POLAR DE TIROS EN LA CIMA\n{self.tension_nominal}kV - {self.tipo_estructura.upper()}'
        ax.set_title(titulo_grafico, fontsize=12, fontweight='bold', pad=20)
        
        # Leyenda
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Hipótesis")
        
        plt.tight_layout()
        plt.show()
        
        print(f"✅ Diagrama polar generado")
    
    def diagrama_barras_tiros(self, titulo=None):
        """
        Genera diagrama de barras comparativo de tiros en cima
        """
        if not hasattr(self, 'df_reacciones'):
            print("❌ No hay datos de reacciones. Ejecutar calcular_reacciones_tiros_cima primero.")
            return
        
        print(f"\n📊 GENERANDO DIAGRAMA DE BARRAS DE TIROS...")
        
        plt.figure(figsize=(12, 6))
        
        # Preparar datos
        hipotesis_barras = []
        tiros_barras = []
        angulos_barras = []
        colores_barras = []
        
        colores_hipotesis = {
            'A1': '#FF0000', 'A2': '#00FF00', 'A3': '#0000FF', 'A4': "#7A7A7A",
            'A5': '#FF00FF', 'B1': '#00FFFF', 'B2': '#FF8000', 'C1': '#8000FF', 'C2': '#008000'
        }
        
        for hipotesis, datos in self.df_reacciones.iterrows():
            codigo = hipotesis.split('_')[-2] if len(hipotesis.split('_')) >= 2 else hipotesis
            
            hipotesis_barras.append(codigo)
            tiros_barras.append(datos['Tiro_resultante_daN'])
            angulos_barras.append(datos['Angulo_grados'])
            colores_barras.append(colores_hipotesis.get(codigo, 'black'))
        
        # Crear gráfico de barras
        barras = plt.bar(hipotesis_barras, tiros_barras, color=colores_barras, alpha=0.7, edgecolor='black')
        
        # Añadir valores en las barras
        for i, (barra, valor, angulo) in enumerate(zip(barras, tiros_barras, angulos_barras)):
            height = barra.get_height()
            plt.text(barra.get_x() + barra.get_width()/2., height + max(tiros_barras)*0.01,
                    f'{valor:.1f} daN\n({angulo:.0f}°)', 
                    ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        # Configurar gráfico
        plt.ylabel('Tiro Resultante [daN]', fontweight='bold')
        plt.xlabel('Hipótesis de Carga', fontweight='bold')
        
        titulo_grafico = titulo if titulo else f'COMPARACIÓN DE TIROS EN LA CIMA\n{self.tension_nominal}kV - {self.tipo_estructura.upper()}'
        plt.title(titulo_grafico, fontsize=12, fontweight='bold')
        
        plt.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
        
        print(f"✅ Diagrama de barras generado")
    
    def guardar_reacciones_csv(self, folder="resultados"):
        """
        Guarda los resultados de reacciones en archivo CSV
        """
        import os
        
        if not hasattr(self, 'df_reacciones'):
            print("❌ No hay datos de reacciones para guardar.")
            return
        
        os.makedirs(folder, exist_ok=True)
        
        nombre_archivo = f"{folder}/10_{self.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_').lower()}_REACCIONES_POO.csv"
        self.df_reacciones.to_csv(nombre_archivo, encoding='utf-8')
        
        print(f"✅ Resultados de reacciones guardados: {nombre_archivo}")

    def _aplicar_patron_doble_terna_a_simple(self, nodo, config_tiro, tiro_base, es_guardia=False):
        """
        Aplica patrón doble-terna-a-simple CORREGIDO: 
        - Todos los conductores del lado L (CX_L) se cargan con tiro unilateral
        - Los conductores del lado R se cargan con tiro bilateral
        - Los guardias se cargan con tiro unilateral
        """
        if es_guardia:
            # Para guardias: aplicar tiro unilateral a todos
            factor_guardia = config_tiro.get("factor_guardia", 1.0)
            tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                tiro_base, self.alpha_quiebre, factor_guardia
            )
            return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
        
        else:
            # Para conductores: determinar si es del lado L o R
            if nodo.endswith('_L'):
                # Conductores del lado L: tiro unilateral
                factor_cond = config_tiro.get("factor_cond", 1.0)
                tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                    tiro_base, self.alpha_quiebre, factor_cond
                )
                return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
            else:
                # Conductores del lado R: tiro bilateral (NO eliminados)
                reduccion_cond = config_tiro.get("reduccion_cond", 0.0)
                tiro_trans, tiro_long = self._calcular_componentes_tiro(
                    tiro_base, self.alpha_quiebre, reduccion_cond, False
                )
                return tiro_trans, tiro_long, 1.0, 1.0  # bilateral: factor 1.0

    def _crear_nodos_conductor_doble_triangular(self, h1a, h2a, lmen):
        """
        Crea nodos para terna doble disposición triangular - PARA SUSPENSIONES (Lk > 0)
        
        Configuración DOBLE TERNA TRIANGULAR para SUSPENSIÓN:
        - Primera altura (h1a): 4 conductores (2 por lado) con separación D_fases
        - Segunda altura (h2a): 2 conductores (1 por lado) CENTRADOS en X=0
        """
        # Obtener D_fases de las dimensiones calculadas
        D_fases = self.dimensiones.get('D_fases', 0.0)
        
        print(f"   📐 Creando nodos doble terna triangular (SUSPENSIÓN - Lk={self.lk}m):")
        print(f"      - h1a: {h1a:.2f}m, h2a: {h2a:.2f}m, lmen: {lmen:.2f}m, D_fases: {D_fases:.2f}m")
        
        # Nivel inferior (h1a): 4 conductores (2 por lado) CON SEPARACIÓN D_fases
        # Lado izquierdo - dos conductores separados por D_fases
        self.nodos["C1_L"] = NodoEstructural(
            "C1_L", (-lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C2_L"] = NodoEstructural(
            "C2_L", (-lmen - D_fases, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        
        # Lado derecho - dos conductores separados por D_fases
        self.nodos["C1_R"] = NodoEstructural(
            "C1_R", (lmen, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C2_R"] = NodoEstructural(
            "C2_R", (lmen + D_fases, 0.0, h1a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        
        # Nivel superior (h2a): 2 conductores (1 por lado) separados lmen

        self.nodos["C3_L"] = NodoEstructural(
            "C3_L", (-lmen, 0.0, h2a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        self.nodos["C3_R"] = NodoEstructural(
            "C3_R", (lmen, 0.0, h2a), "conductor",
            self.cable_conductor, self.alpha_quiebre, self.tipo_fijacion_base
        )
        
        print(f"      - Nodos creados: 4 en h1a (con separación lmen, lmen+D_fases), 2 en h2a (lmen)")

