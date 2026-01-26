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
        
        # Calcular theta_tormenta usando Vtormenta
        if not hasattr(self.geo, 'Vtormenta'):
            raise ValueError("ERROR: Parámetro 'Vtormenta' no encontrado en estructura")
        
        theta_tormenta = self.geo.calcular_theta_tormenta(vano, self.geo.Vtormenta)
        
        distancias = self.geo.calcular_distancias_minimas(flecha_max_conductor, theta_max)
        
        # SOBREESCRIBIR s si flag está activo
        if getattr(self.geo, 'sobreescribir_s', False):
            s_reposo_custom = getattr(self.geo, 's_reposo', None)
            s_tormenta_custom = getattr(self.geo, 's_tormenta', None)
            s_decmax_custom = getattr(self.geo, 's_decmax', None)
            
            # Validar que no sean 0
            if s_reposo_custom is not None and s_reposo_custom <= 0:
                raise ValueError(f"Error: s_reposo no puede valer {s_reposo_custom}. Debe ser mayor a 0.")
            if s_tormenta_custom is not None and s_tormenta_custom <= 0:
                raise ValueError(f"Error: s_tormenta no puede valer {s_tormenta_custom}. Debe ser mayor a 0.")
            if s_decmax_custom is not None and s_decmax_custom <= 0:
                raise ValueError(f"Error: s_decmax no puede valer {s_decmax_custom}. Debe ser mayor a 0.")
            
            if s_reposo_custom is not None:
                distancias['s_reposo'] = s_reposo_custom
                print(f"   🔧 s_reposo sobreescrito: {s_reposo_custom:.3f}m")
            else:
                distancias['s_reposo'] = distancias['s_estructura']
            
            if s_tormenta_custom is not None:
                distancias['s_tormenta'] = s_tormenta_custom
                print(f"   🔧 s_tormenta sobreescrito: {s_tormenta_custom:.3f}m")
            else:
                distancias['s_tormenta'] = distancias['s_estructura']
            
            if s_decmax_custom is not None:
                distancias['s_decmax'] = s_decmax_custom
                print(f"   🔧 s_decmax sobreescrito: {s_decmax_custom:.3f}m")
            else:
                distancias['s_decmax'] = distancias['s_estructura']
        else:
            # Si no se sobreescribe, usar s_estructura para todos
            distancias['s_reposo'] = distancias['s_estructura']
            distancias['s_tormenta'] = distancias['s_estructura']
            distancias['s_decmax'] = distancias['s_estructura']
        
        # Imprimir valores finales usados en checkeos
        print(f"   📏 Distancias usadas en checkeos:")
        print(f"      s_estructura (calculado): {distancias['s_estructura']:.3f}m")
        print(f"      s_reposo: {distancias.get('s_reposo', distancias['s_estructura']):.3f}m")
        print(f"      s_tormenta: {distancias.get('s_tormenta', distancias['s_estructura']):.3f}m")
        print(f"      s_decmax: {distancias.get('s_decmax', distancias['s_estructura']):.3f}m")
        
        # Calcular h1a con fórmula obligatoria: h1a = max(a + b, altura_minima_cable) + fmax + Lk + HADD
        a = self.geo.ALTURAS_MINIMAS_TERRENO.get(self.geo.zona_estructura, 5.90)
        
        # Verificar si se sobreescribe altura_a_cable
        sobreescribir_altura_a_cable = getattr(self.geo, 'sobreescribir_altura_a_cable', False)
        if sobreescribir_altura_a_cable:
            a_sobreescrita = getattr(self.geo, 'altura_a_cable_sobreescrita', None)
            if a_sobreescrita is not None and a_sobreescrita > 0:
                a = a_sobreescrita
                print(f"   🔧 Altura 'a' sobreescrita: {a:.3f}m")
        
        b = distancias['b']
        altura_minima_cable = getattr(self.geo, 'altura_minima_cable', 6.5)
        fmax = flecha_max_conductor
        Lk = self.geo.lk
        HADD = self.geo.hadd
        
        # Aplicar max(a + b, altura_minima_cable)
        a_mas_b = a + b
        base_altura = max(a_mas_b, altura_minima_cable)
        h1a = base_altura + fmax + Lk + HADD
        
        print(f"   📐 Cálculo h1a: max({a:.2f} + {b:.2f}, {altura_minima_cable:.2f}) + {fmax:.2f} + {Lk:.2f} + {HADD:.2f}")
        print(f"   📐 h1a = max({a_mas_b:.2f}, {altura_minima_cable:.2f}) + {fmax:.2f} + {Lk:.2f} + {HADD:.2f} = {h1a:.2f}m")
        
        # Calcular Lmen1 iterativamente
        Lmen1_iterado = self._calcular_lmen1_iterativo(h1a, distancias, theta_max)
        
        # Agregar HADD_LMEN al valor final
        HADD_LMEN = getattr(self.geo, 'hadd_lmen', 0.0)
        Lmen1_pre_hielo = Lmen1_iterado + HADD_LMEN
        
        # Guardar Lmen1 PRE-hielo para uso en C2
        Lmen1_sin_defasaje = Lmen1_pre_hielo
        
        # Agregar defasaje por hielo si corresponde (solo afecta a C1)
        Lmen1 = Lmen1_pre_hielo
        if self.geo.defasaje_mensula_hielo and ("primera" in self.geo.mensula_defasar):
            Lmen1 += self.geo.lmen_extra_hielo
            print(f"   ➕ HADD_LMEN + hielo: {Lmen1_iterado:.3f}m + {HADD_LMEN:.3f}m + {self.geo.lmen_extra_hielo:.3f}m = {Lmen1:.3f}m")
        elif HADD_LMEN > 0:
            print(f"   ➕ HADD_LMEN aplicado: {Lmen1_iterado:.3f}m + {HADD_LMEN:.3f}m = {Lmen1:.3f}m")
        
        # Guardar resultados (s_reposo, s_tormenta, s_decmax ya están en distancias)
        self.geo.dimensiones.update({
            "h1a": h1a,
            "Lmen1": Lmen1,
            "Lmen1_sin_defasaje": Lmen1_sin_defasaje,
            "theta_tormenta": theta_tormenta,
            **distancias
        })
        
        # DEBUG: Verificar que se guardaron correctamente
        print(f"   💾 DEBUG: Valores guardados en dimensiones:")
        print(f"      s_reposo: {self.geo.dimensiones.get('s_reposo', 'NO EXISTE')}")
        print(f"      s_tormenta: {self.geo.dimensiones.get('s_tormenta', 'NO EXISTE')}")
        print(f"      s_decmax: {self.geo.dimensiones.get('s_decmax', 'NO EXISTE')}")
        
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
        
        # Obtener theta_tormenta de dimensiones (ya calculado en ejecutar)
        theta_tormenta = self.geo.dimensiones.get('theta_tormenta', theta_max / 2.0)
        
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
        
        # CASO GENERAL: Iterativo verificando 3 condiciones
        s_reposo = distancias.get('s_reposo', distancias['s_estructura'])
        s_tormenta = distancias.get('s_tormenta', distancias['s_estructura'])
        s_decmax = distancias.get('s_decmax', distancias['s_estructura'])
        Lmen_minima = self.geo.long_mensula_min_conductor
        Lk = self.geo.lk
        
        Lmen1 = 0.0
        max_iteraciones = 1000
        incremento = 0.01
        
        print(f"   🔍 Lmen1 iterativo: Lmen_min={Lmen_minima:.3f}m, Lk={Lk:.3f}m")
        print(f"      s_reposo={s_reposo:.3f}m, s_tormenta={s_tormenta:.3f}m, s_decmax={s_decmax:.3f}m")
        print(f"      theta_max={theta_max:.2f}°, theta_tormenta={theta_tormenta:.2f}°")
        
        for i in range(max_iteraciones):
            # Verificar 3 condiciones en paralelo
            # 1. Reposo (theta=0, conductor cuelga verticalmente)
            x_reposo = Lmen1
            z_reposo = h1a - Lk
            infr_col_reposo = self._verificar_infraccion_columna(x_reposo, z_reposo, s_reposo, h1a, 0, 0)
            infr_men_reposo = self._verificar_infraccion_mensula(Lmen1, h1a, x_reposo, z_reposo, s_reposo, 0, 0)
            
            # DEBUG: Imprimir cada 100 iteraciones
            if i % 100 == 0:
                print(f"      Iter {i}: Lmen1={Lmen1:.3f}m, x_rep={x_reposo:.3f}, z_rep={z_reposo:.3f}")
                print(f"         infr_col={infr_col_reposo}, infr_men={infr_men_reposo}")
            
            # 2. Tormenta (theta=theta_tormenta)
            x_tormenta = Lmen1 - Lk * math.sin(math.radians(theta_tormenta))
            z_tormenta = h1a - Lk * math.cos(math.radians(theta_tormenta))
            infr_col_tormenta = self._verificar_infraccion_columna(x_tormenta, z_tormenta, s_tormenta, h1a, theta_tormenta, theta_tormenta)
            infr_men_tormenta = self._verificar_infraccion_mensula(Lmen1, h1a, x_tormenta, z_tormenta, s_tormenta, theta_tormenta, theta_tormenta)
            
            # 3. Declinación máxima (theta=theta_max)
            x_decmax = Lmen1 - Lk * math.sin(math.radians(theta_max))
            z_decmax = h1a - Lk * math.cos(math.radians(theta_max))
            infr_col_decmax = self._verificar_infraccion_columna(x_decmax, z_decmax, s_decmax, h1a, theta_max, theta_tormenta)
            infr_men_decmax = self._verificar_infraccion_mensula(Lmen1, h1a, x_decmax, z_decmax, s_decmax, theta_max, theta_tormenta)
            
            # Si hay cualquier infracción columna, incrementar
            if infr_col_reposo or infr_col_tormenta or infr_col_decmax:
                Lmen1 += incremento
                continue
            
            # Si Lk > 0, verificar distancias verticales a ménsula (chequeo simplificado)
            if Lk > 0.0:
                dist_vertical_reposo = Lk  # En reposo, distancia vertical es Lk completo
                if dist_vertical_reposo < s_reposo:
                    raise ValueError(f"Lk insuficiente: dist_vertical={dist_vertical_reposo:.3f}m < s_reposo={s_reposo:.3f}m")

                dist_vertical_tormenta = Lk * math.cos(math.radians(theta_tormenta))
                if dist_vertical_tormenta < s_tormenta:
                    raise ValueError(f"Lk insuficiente: dist_vertical={dist_vertical_tormenta:.3f}m < s_tormenta={s_tormenta:.3f}m")

                dist_vertical_decmax = Lk * math.cos(math.radians(theta_max))
                if dist_vertical_decmax < s_decmax:
                    raise ValueError(f"Lk insuficiente: dist_vertical={dist_vertical_decmax:.3f}m < s_decmax={s_decmax:.3f}m")

            # Si hay infracción ménsula (verificación completa con geometria_zonas)
            # Con Lk=0, la verificación completa da False y este bloque se salta
            if infr_men_reposo or infr_men_tormenta or infr_men_decmax:
                Lmen1 += incremento
                continue
            
            break
        
        resultado = max(Lmen1, Lmen_minima)
        print(f"   ✅ Lmen1={resultado:.3f}m ({i+1} iter)")
        return resultado
    
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
            's_reposo': self.geo.dimensiones.get('s_reposo', 0),
            's_decmax': s_decmax,
            's_tormenta': self.geo.dimensiones.get('s_tormenta', 0),
            'Dhg': 0,
            'theta_max': theta_max,
            'theta_tormenta': theta_tormenta,
            'offset_columna_base': self.geo.offset_columna_base,
            'offset_columna_base_tipo': self.geo.offset_columna_base_tipo,
            'offset_columna_base_inicio': self.geo.offset_columna_base_inicio,
            'offset_columna_base_fin': self.geo.offset_columna_base_fin,
            'h_cross_h1': h1a
        }
        
        # Crear verificador y verificar punto
        verificador = crear_verificador_desde_nodos(nodos_temp, parametros)
        resultado = verificador.verificar_punto(x_conductor, z_conductor)
        
        return resultado['infringe']
    
    def _verificar_infraccion_mensula(self, Lmen1, h1a, x_conductor, z_conductor, s_decmax, theta_max, theta_tormenta):
        """Verificar si conductor infringe zona de ménsula usando geometria_zonas"""
        # Si Lk es 0, el conductor está en el punto de amarre, no hay checkeo de ménsula.
        if self.geo.lk == 0.0:
            return False

        if Lmen1 < 0.001:
            return False
        
        # Crear estructura temporal de nodos
        nodos_temp = {}
        nodos_temp["CROSS_H1"] = Nodo("CROSS_H1", 0, 0, h1a, "cruce")
        nodos_temp["C1_TEMP"] = Nodo("C1_TEMP", Lmen1, 0, h1a, "conductor")
        nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp["C1_TEMP"], "mensula")
        
        # Ménsula usa s_decmax (conductor en theta_max)
        parametros = {
            'Lk': self.geo.lk,
            'D_fases': 0,
            's_reposo': 0,
            's_decmax': s_decmax,
            's_tormenta': 0,
            'Dhg': 0,
            'theta_max': theta_max,
            'theta_tormenta': theta_tormenta,
            'z_min_corte': h1a,
            'offset_mensula': self.geo.offset_mensula,
            'offset_mensula_tipo': self.geo.offset_mensula_tipo,
            'offset_mensula_inicio': self.geo.offset_mensula_inicio,
            'offset_mensula_fin': self.geo.offset_mensula_fin
        }
        
        verificador = crear_verificador_desde_nodos(nodos_temp, parametros)
        resultado = verificador.verificar_punto(x_conductor, z_conductor)
        
        return resultado['infringe']
    
    def _crear_nodos_conductores_h1a(self, h1a, Lmen1):
        """Crear nodos conductores en primera altura según disposición/terna"""
        
        # Horizontal simple: NO aplica defasaje por hielo (ya está incluido en Lmen1)
        if self.geo.disposicion == "horizontal" and self.geo.terna == "Simple":
            self._crear_horizontal_simple(h1a, Lmen1)
            return
        
        # Para todos los demás casos, Lmen1 ya incluye HADD_LMEN + defasaje hielo
        if self.geo.terna == "Simple" and self.geo.disposicion == "vertical":
            # Vertical simple: C1
            self.geo.nodos["C1"] = NodoEstructural(
                "C1", (Lmen1, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodo C1 creado en ({Lmen1:.2f}, 0, {h1a:.2f})")
        
        elif self.geo.terna == "Simple" and (self.geo.disposicion == "triangular" or self.geo.disposicion == "triangular-mensulas"):
            # Triangular simple (y triangular-mensulas): C1 usa Lmen1 (con defasaje), C2 usa Lmen1_sin_defasaje
            Lmen1_sin_defasaje = self.geo.dimensiones.get('Lmen1_sin_defasaje', Lmen1)
            
            self.geo.nodos["C1"] = NodoEstructural(
                "C1", (Lmen1, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C2"] = NodoEstructural(
                "C2", (-Lmen1_sin_defasaje, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodo C1 creado en ({Lmen1:.2f}, 0, {h1a:.2f})")
            print(f"   🔵 Nodo C2 creado en ({-Lmen1_sin_defasaje:.2f}, 0, {h1a:.2f}) [sin defasaje]")
        
        elif self.geo.terna == "Doble" and self.geo.disposicion == "vertical":
            # Doble vertical: C1_R, C1_L
            self.geo.nodos["C1_R"] = NodoEstructural(
                "C1_R", (Lmen1, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C1_L"] = NodoEstructural(
                "C1_L", (-Lmen1, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodos C1_R, C1_L creados en (±{Lmen1:.2f}, 0, {h1a:.2f})")
        
        elif self.geo.terna == "Doble" and self.geo.disposicion == "triangular":
            # Doble triangular: C1_R, C2_R, C1_L, C2_L
            D_fases = self.geo.dimensiones['D_fases']
            Lmen12 = max(D_fases, self.geo.long_mensula_min_conductor)
            
            # Guardar Lmen12 en dimensiones
            self.geo.dimensiones['Lmen12'] = Lmen12
            
            self.geo.nodos["C1_R"] = NodoEstructural(
                "C1_R", (Lmen1, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C2_R"] = NodoEstructural(
                "C2_R", (Lmen1 + Lmen12, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C1_L"] = NodoEstructural(
                "C1_L", (-Lmen1, 0.0, h1a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C2_L"] = NodoEstructural(
                "C2_L", (-(Lmen1 + Lmen12), 0.0, h1a), "conductor",
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
