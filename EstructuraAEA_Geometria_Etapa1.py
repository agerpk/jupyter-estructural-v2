# EstructuraAEA_Geometria_Etapa1.py
import math
from NodoEstructural import NodoEstructural
from utils.geometria_zonas import Nodo, crear_verificador_desde_nodos


class GeometriaEtapa1:
    """Etapa 1: h1a y Lmen1 (Primer Amarre)"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def ejecutar(self, vano, flecha_max_conductor, flecha_max_guardia):
        print("🔧 ETAPA 1: h1a y Lmen1")
        
        # Calcular parámetros base
        theta_max = self.geo.calcular_theta_max(vano)
        
        # Validar theta_max
        if theta_max >= 99.0:
            print("   ⚠️  WARNING: No se pudo calcular theta_max correctamente (falta cache de viento)")
            print("   ⚠️  WARNING: Continuando con theta_max = 0°")
            theta_max = 0.0
        
        distancias = self.geo.calcular_distancias_minimas(flecha_max_conductor, theta_max)
        
        # Calcular h1a con fórmula obligatoria: h1a = a + b + fmax + Lk + HADD
        a = self.geo.ALTURAS_MINIMAS_TERRENO.get(self.geo.zona_estructura, 5.90)
        b = distancias['b']
        fmax = flecha_max_conductor
        Lk = self.geo.lk
        HADD = self.geo.hadd
        h1a = a + b + fmax + Lk + HADD
        
        # Calcular Lmen1 iterativamente
        Lmen1 = self._calcular_lmen1_iterativo(h1a, distancias, theta_max)
        
        # Guardar resultados
        self.geo.dimensiones.update({
            "h1a": h1a,
            "Lmen1": Lmen1,
            "s_tormenta": distancias['s_estructura'],
            "s_decmax": distancias['s_estructura'],
            **distancias
        })
        
        # Crear nodos conductores según disposición/terna
        self._crear_nodos_conductores_h1a(h1a, Lmen1)
        
        # Crear nodo CROSS en h1a (si no es horizontal simple)
        if not (self.geo.disposicion == "horizontal" and self.geo.terna == "Simple"):
            self.geo.nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
            print(f"   🔵 Nodo CROSS_H1 creado en (0, 0, {h1a:.2f})")
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ h1a={h1a:.2f}m, Lmen1={Lmen1:.2f}m")
    
    def _calcular_lmen1_iterativo(self, h1a, distancias, theta_max):
        """Calcular Lmen1 chequeando zona s_decmax en declinación máxima"""
        
        # Calcular theta_tormenta como theta_max/2
        theta_tormenta = theta_max / 2.0
        
        # CASO ESPECIAL: Horizontal Simple con Lk=0 y NO Suspensión
        if (self.geo.disposicion == "horizontal" and 
            self.geo.terna == "Simple" and 
            self.geo.lk == 0 and
            self.geo.tipo_estructura not in ["Suspensión", "Suspension"]):
            
            D_fases = distancias['D_fases']
            Lmen_minima = self.geo.long_mensula_min_conductor
            Lmen1 = max(D_fases, Lmen_minima)
            print(f"   🔵 Horizontal Simple Lk=0: Lmen1 = max(D_fases={D_fases:.2f}, Lmen_min={Lmen_minima:.2f}) = {Lmen1:.2f}m")
            return Lmen1
        
        # CASO GENERAL: Iterativo con s_decmax
        s_decmax = distancias['s_estructura']
        Lmen_minima = self.geo.long_mensula_min_conductor
        Lk = self.geo.lk
        
        Lmen1 = Lmen_minima
        max_iteraciones = 100
        incremento = 0.05
        
        for i in range(max_iteraciones):
            # Calcular posición conductor declinado
            x_conductor = Lmen1 + Lk * math.sin(math.radians(theta_max))
            z_conductor = h1a - Lk * math.cos(math.radians(theta_max))
            
            # Verificar infracciones con elementos fijos
            infraccion_columna = self._verificar_infraccion_columna(x_conductor, z_conductor, s_decmax, h1a, theta_max, theta_tormenta)
            infraccion_mensula = self._verificar_infraccion_mensula(Lmen1, h1a, x_conductor, z_conductor, s_decmax, theta_max, theta_tormenta)
            
            if infraccion_columna:
                Lmen1 += incremento
                continue
            
            if infraccion_mensula:
                if Lk > 0:
                    # Calcular distancia de infracción
                    dist_mensula = math.sqrt((Lmen1 - x_conductor)**2 + (h1a - z_conductor)**2)
                    falta = s_decmax - dist_mensula  # Positivo = falta distancia
                    if falta > 0:
                        print(f"   ⚠️  Infracción detectada: ménsula a {dist_mensula:.3f}m del conductor declinado")
                        print(f"      Distancia mínima requerida (s_decmax): {s_decmax:.3f}m")
                        print(f"      Falta: {falta:.3f}m")
                        print(f"      Lk actual: {Lk:.3f}m")
                        print(f"      Lk mínimo necesario: {Lk + falta:.3f}m")
                        raise ValueError(
                            f"Lk insuficiente para evitar infracción con ménsula. "
                            f"Lk actual={Lk:.3f}m, Lk mínimo={Lk + falta:.3f}m, "
                            f"aumentar {falta:.3f}m"
                        )
                else:
                    if not infraccion_columna:
                        break
            
            break
        
        return max(Lmen1, Lmen_minima)
    
    def _verificar_infraccion_columna(self, x_conductor, z_conductor, s_decmax, h1a, theta_max, theta_tormenta):
        """Verificar si conductor infringe zonas prohibidas usando geometria_zonas"""
        # Crear estructura temporal de nodos para verificación
        nodos_temp = {}
        
        # Nodo BASE
        nodos_temp["BASE"] = Nodo("BASE", 0, 0, 0, "base")
        # Nodo CROSS_H1 (si existe)
        nodos_temp["CROSS_H1"] = Nodo("CROSS_H1", 0, 0, h1a, "cruce")
        # Conexión columna
        nodos_temp["BASE"].agregar_conexion(nodos_temp["CROSS_H1"], "columna")
        
        # Parámetros
        parametros = {
            'Lk': self.geo.lk,
            'D_fases': self.geo.dimensiones.get('D_fases', 0),
            's_reposo': self.geo.dimensiones.get('s_estructura', 0),
            's_decmax': s_decmax,
            's_tormenta': self.geo.dimensiones.get('s_tormenta', 0),
            'Dhg': 0,
            'theta_max': theta_max,
            'theta_tormenta': theta_tormenta
        }
        
        # Crear verificador y verificar punto
        verificador = crear_verificador_desde_nodos(nodos_temp, parametros)
        resultado = verificador.verificar_punto(x_conductor, z_conductor)
        
        return resultado['infringe']
    
    def _verificar_infraccion_mensula(self, Lmen1, h1a, x_conductor, z_conductor, s_decmax, theta_max, theta_tormenta):
        """Verificar si conductor infringe zona de ménsula usando geometria_zonas"""
        if Lmen1 < 0.001:
            return False
        
        # Crear estructura temporal de nodos
        nodos_temp = {}
        nodos_temp["CROSS_H1"] = Nodo("CROSS_H1", 0, 0, h1a, "cruce")
        nodos_temp["C1_TEMP"] = Nodo("C1_TEMP", Lmen1, 0, h1a, "conductor")
        nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp["C1_TEMP"], "mensula")
        
        parametros = {
            'Lk': self.geo.lk,
            'D_fases': 0,
            's_reposo': self.geo.dimensiones.get('s_estructura', 0),
            's_decmax': s_decmax,
            's_tormenta': 0,
            'Dhg': 0,
            'theta_max': theta_max,
            'theta_tormenta': theta_tormenta
        }
        
        verificador = crear_verificador_desde_nodos(nodos_temp, parametros)
        resultado = verificador.verificar_punto(x_conductor, z_conductor)
        
        return resultado['infringe']
    
    def _crear_nodos_conductores_h1a(self, h1a, Lmen1):
        """Crear nodos conductores en primera altura según disposición/terna"""
        
        # Horizontal simple: NO aplica defasaje por hielo
        if self.geo.disposicion == "horizontal" and self.geo.terna == "Simple":
            self._crear_horizontal_simple(h1a, Lmen1)
            return
        
        # Aplicar defasaje por hielo si corresponde (para todos los demás casos)
        Lmen1_con_hielo = Lmen1
        if self.geo.defasaje_mensula_hielo and ("primera" in self.geo.mensula_defasar):
            Lmen1_con_hielo += self.geo.lmen_extra_hielo
            print(f"   ❄️  Defasaje hielo aplicado: Lmen1_con_hielo = {Lmen1_con_hielo:.2f}m")
        
        if self.geo.terna == "Simple" and self.geo.disposicion == "vertical":
            # Vertical simple: C1
            self.geo.nodos["C1"] = NodoEstructural(
                "C1", (Lmen1_con_hielo, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodo C1 creado en ({Lmen1_con_hielo:.2f}, 0, {h1a:.2f})")
        
        elif self.geo.terna == "Simple" and self.geo.disposicion == "triangular":
            # Triangular simple: C1, C2
            self.geo.nodos["C1"] = NodoEstructural(
                "C1", (Lmen1_con_hielo, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C2"] = NodoEstructural(
                "C2", (-Lmen1_con_hielo, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodos C1, C2 creados en (±{Lmen1_con_hielo:.2f}, 0, {h1a:.2f})")
        
        elif self.geo.terna == "Doble" and self.geo.disposicion == "vertical":
            # Doble vertical: C1_R, C1_L
            self.geo.nodos["C1_R"] = NodoEstructural(
                "C1_R", (Lmen1_con_hielo, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C1_L"] = NodoEstructural(
                "C1_L", (-Lmen1_con_hielo, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodos C1_R, C1_L creados en (±{Lmen1_con_hielo:.2f}, 0, {h1a:.2f})")
        
        elif self.geo.terna == "Doble" and self.geo.disposicion == "triangular":
            # Doble triangular: C1_R, C2_R, C1_L, C2_L
            D_fases = self.geo.dimensiones['D_fases']
            Lmen12 = max(D_fases, self.geo.long_mensula_min_conductor)
            
            # Guardar Lmen12 en dimensiones
            self.geo.dimensiones['Lmen12'] = Lmen12
            
            self.geo.nodos["C1_R"] = NodoEstructural(
                "C1_R", (Lmen1_con_hielo, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C2_R"] = NodoEstructural(
                "C2_R", (Lmen1_con_hielo + Lmen12, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C1_L"] = NodoEstructural(
                "C1_L", (-Lmen1_con_hielo, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C2_L"] = NodoEstructural(
                "C2_L", (-(Lmen1_con_hielo + Lmen12), 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodos C1_R, C2_R, C1_L, C2_L creados en h1a={h1a:.2f}m, Lmen12={Lmen12:.2f}m")
    
    def _crear_horizontal_simple(self, h1a, Lmen1):
        """Crear nodos para horizontal simple: C1, C2, C3"""
        self.geo.nodos["C1"] = NodoEstructural(
            "C1", (Lmen1, 0.0, h1a), "conductor",
            self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        self.geo.nodos["C2"] = NodoEstructural(
            "C2", (0.0, 0.0, h1a), "conductor",
            self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        self.geo.nodos["C3"] = NodoEstructural(
            "C3", (-Lmen1, 0.0, h1a), "conductor",
            self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        print(f"   🔵 Nodos C1, C2, C3 creados en h1a={h1a:.2f}m")
    
    def _ejecutar_conectador(self):
        """Ejecutar conectador de nodos al finalizar etapa"""
        print("   🔌 Ejecutando conectador de nodos...")
        
        # Inicializar conexiones si no existe
        if not hasattr(self.geo, 'conexiones'):
            self.geo.conexiones = []
        
        conexiones_anteriores = set(self.geo.conexiones)
        
        self.geo._generar_conexiones()
        
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        if conexiones_nuevas:
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      INFO: {origen} → {destino} ({tipo})")
