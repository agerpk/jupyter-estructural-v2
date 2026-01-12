# EstructuraAEA_Geometria_Etapa2.py
import math
from NodoEstructural import NodoEstructural
from utils.geometria_zonas import Nodo, crear_verificador_desde_nodos


class GeometriaEtapa2:
    """Etapa 2: h2a (Segundo Amarre)"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def ejecutar(self):
        print("🔧 ETAPA 2: h2a (segundo amarre)")
        
        # Solo aplica para disposiciones que tienen segunda altura
        if self.geo.disposicion == "horizontal":
            print("   ⏭️  No aplica h2a para disposición horizontal")
            return
        
        # Calcular theta_max y theta_tormenta
        vano = self.geo.dimensiones.get('vano', 400)
        theta_max = self.geo.calcular_theta_max(vano)
        if theta_max >= 99.0:
            theta_max = 0.0
        theta_tormenta = theta_max / 2.0
        
        # Calcular h2a_inicial
        h1a = self.geo.dimensiones["h1a"]
        D_fases = self.geo.dimensiones["D_fases"]
        s_reposo = self.geo.dimensiones["s_estructura"]
        Lk = self.geo.lk
        HADD_ENTRE_AMARRES = self.geo.hadd_entre_amarres
        
        # Inicializar Lmen2 PRE hielo (siempre basado en Lmen1 PRE hielo)
        Lmen1_original = self.geo.dimensiones["Lmen1"]  # PRE hielo
        Lmen2 = max(Lmen1_original, self.geo.long_mensula_min_conductor)
        
        if Lk > 0:
            h2a_inicial = max(
                h1a + D_fases + HADD_ENTRE_AMARRES,
                h1a + s_reposo + Lk + HADD_ENTRE_AMARRES
            )
        else:
            h2a_inicial = h1a + D_fases + HADD_ENTRE_AMARRES
        
        # Optimizar h2a si hay defasaje por hielo
        h2a_final = h2a_inicial
        
        if self.geo.defasaje_mensula_hielo and self.geo.lmen_extra_hielo > 0:
            mensula_defasar = self.geo.mensula_defasar
            
            # Si la defasada es "primera" O "primera y tercera"
            if mensula_defasar == "primera" or mensula_defasar == "primera y tercera":
                # Lmen1 fue incrementada en Etapa1, Lmen2 permanece normal (PRE hielo)
                # Buscar altura óptima con Lmen2 normal considerando todas las zonas prohibidas
                zoptimo2 = self._buscar_altura_fuera_zonas_prohibidas_h1a(Lmen2, h1a, D_fases, s_reposo, theta_max, theta_tormenta)
                h2a_final = zoptimo2 + HADD_ENTRE_AMARRES
                print(f"   🔵 Optimización por defasaje '{mensula_defasar}': h2a reducida a {h2a_final:.2f}m")
            
            elif mensula_defasar == "segunda":
                # Lmen2 será incrementada, luego buscar altura óptima
                Lmen2 = Lmen2 + self.geo.lmen_extra_hielo
                # Recheckear altura considerando zonas prohibidas de h1a
                zoptimo2 = self._buscar_altura_fuera_zonas_prohibidas_h1a(Lmen2, h1a, D_fases, s_reposo, theta_max, theta_tormenta)
                h2a_final = zoptimo2 + HADD_ENTRE_AMARRES
                print(f"   ❄️  Defasaje hielo 'segunda': Lmen2 = {Lmen2:.2f}m, h2a = {h2a_final:.2f}m")
        
        # Guardar resultados
        self.geo.dimensiones["h2a"] = h2a_final
        self.geo.dimensiones["Lmen2"] = Lmen2
        
        # Checkear zonas de prohibición D_fases entre conductores h1a y h2a
        self._checkear_zonas_dfases_entre_alturas(h2a_final, Lmen2, h1a, theta_max, theta_tormenta)
        
        # Checkear zonas de prohibición s antes de crear nodos
        self._checkear_zonas_prohibicion_s(h2a_final, Lmen2, h1a, theta_max, theta_tormenta)
        
        # Crear nodos conductores según disposición/terna
        self._crear_nodos_conductores_h2a(h2a_final, Lmen2)
        
        # Crear nodo CROSS en h2a (siempre, incluso si h2a = h1a)
        self.geo.nodos["CROSS_H2"] = NodoEstructural("CROSS_H2", (0.0, 0.0, h2a_final), "cruce")
        print(f"   🔵 Nodo CROSS_H2 creado en (0, 0, {h2a_final:.2f})")
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ h2a={h2a_final:.2f}m, Lmen2={Lmen2:.2f}m")
    
    def _buscar_altura_fuera_zonas_prohibidas_h1a(self, x_linea, h1a, D_fases, s_reposo, theta_max, theta_tormenta):
        """Buscar altura mínima en línea x=x_linea que no infringe zonas prohibidas de h1a
        
        Usa el módulo de zonas prohibidas geométricas con estructura de nodos.
        """
        Lk = self.geo.lk
        s_decmax = self.geo.dimensiones.get("s_decmax", s_reposo)
        Lmen1 = self.geo.dimensiones["Lmen1"]
        
        # Construir estructura de nodos temporal
        nodos_temp = {}
        
        # BASE
        nodos_temp["BASE"] = Nodo("BASE", 0, 0, 0, "base")
        
        # CROSS_H1
        nodos_temp["CROSS_H1"] = Nodo("CROSS_H1", 0, 0, h1a, "cruce")
        nodos_temp["BASE"].agregar_conexion(nodos_temp["CROSS_H1"], "columna")
        
        # Nodos conductores h1a
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h1a) < 1e-3:
                x, y, z = nodo.coordenadas
                nodos_temp[nombre] = Nodo(nombre, x, y, z, "conductor")
                nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp[nombre], "mensula")
        
        # Parámetros
        parametros = {
            'Lk': Lk,
            'D_fases': D_fases,
            's_reposo': s_reposo,
            's_decmax': s_decmax,
            's_tormenta': self.geo.dimensiones.get('s_tormenta', 0),
            'Dhg': 0,
            'theta_max': theta_max,
            'theta_tormenta': theta_tormenta
        }
        
        # Crear verificador y buscar altura mínima
        verificador = crear_verificador_desde_nodos(nodos_temp, parametros)
        z_minima, razon = verificador.buscar_altura_minima(x_linea)
        
        print(f"   🔍 Altura óptima en x={x_linea:.2f}m: z={z_minima:.3f}m (razón: {razon})")
        
        return z_minima
    
    def _buscar_altura_fuera_zonas_dfases(self, x_linea, h1a, D_fases):
        """Buscar altura mínima en línea x=x_linea que no infringe zonas D_fases de h1a
        
        Checkea que el conductor en h2a no infrinja la zona D_fases del conductor en h1a.
        Considera el conductor en REPOSO (sin declinación).
        """
        Lk = self.geo.lk
        z_conductor_h1a = h1a - Lk
        
        # Zona prohibida D_fases alrededor de conductor h1a
        z_max_prohibida = z_conductor_h1a + D_fases
        
        # Altura óptima: justo arriba de zona prohibida + Lk (altura de amarre)
        zoptimo2 = z_max_prohibida + Lk
        
        # Verificar que no infringe (checkeo)
        z_conductor_h2a = zoptimo2 - Lk
        distancia = abs(z_conductor_h2a - z_conductor_h1a)
        
        if distancia < D_fases:
            print(f"   ⚠️  WARNING: Distancia entre conductores h1a-h2a: {distancia:.3f}m < D_fases({D_fases:.3f}m)")
        
        return zoptimo2
    
    def _checkear_zonas_dfases_entre_alturas(self, h2a, Lmen2, h1a, theta_max, theta_tormenta):
        """Checkear que conductores h2a no infringen zonas D_fases de conductores h1a
        
        Verifica en 3 declinaciones: reposo, tormenta, máxima (ambos conductores con misma declinación)
        """
        Lk = self.geo.lk
        D_fases = self.geo.dimensiones["D_fases"]
        
        # Posiciones conductores h1a
        conductores_h1a = [(n, nodo) for n, nodo in self.geo.nodos.items() 
                          if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h1a) < 1e-3]
        
        # Verificar en REPOSO
        z_conductor_h2a_reposo = h2a - Lk
        for nombre_h1a, nodo_h1a in conductores_h1a:
            x_h1a, y_h1a, z_amarre_h1a = nodo_h1a.coordenadas
            z_conductor_h1a_reposo = z_amarre_h1a - Lk
            dist_reposo = abs(z_conductor_h2a_reposo - z_conductor_h1a_reposo)
            if dist_reposo < D_fases:
                print(f"   ⚠️  WARNING: Distancia D_fases {nombre_h1a}-h2a (reposo): {dist_reposo:.3f}m < D_fases({D_fases:.3f}m)")
        
        # Verificar en TORMENTA
        if theta_tormenta > 0:
            x_h2a_tormenta = Lmen2 + Lk * math.sin(math.radians(theta_tormenta))
            z_h2a_tormenta = h2a - Lk * math.cos(math.radians(theta_tormenta))
            for nombre_h1a, nodo_h1a in conductores_h1a:
                x_h1a, y_h1a, z_amarre_h1a = nodo_h1a.coordenadas
                x_h1a_tormenta = x_h1a + Lk * math.sin(math.radians(theta_tormenta))
                z_h1a_tormenta = z_amarre_h1a - Lk * math.cos(math.radians(theta_tormenta))
                dist_tormenta = math.sqrt((x_h2a_tormenta - x_h1a_tormenta)**2 + (z_h2a_tormenta - z_h1a_tormenta)**2)
                if dist_tormenta < D_fases:
                    print(f"   ⚠️  WARNING: Distancia D_fases {nombre_h1a}-h2a (tormenta): {dist_tormenta:.3f}m < D_fases({D_fases:.3f}m)")
        
        # Verificar en MÁXIMA
        if theta_max > 0:
            x_h2a_max = Lmen2 + Lk * math.sin(math.radians(theta_max))
            z_h2a_max = h2a - Lk * math.cos(math.radians(theta_max))
            for nombre_h1a, nodo_h1a in conductores_h1a:
                x_h1a, y_h1a, z_amarre_h1a = nodo_h1a.coordenadas
                x_h1a_max = x_h1a + Lk * math.sin(math.radians(theta_max))
                z_h1a_max = z_amarre_h1a - Lk * math.cos(math.radians(theta_max))
                dist_max = math.sqrt((x_h2a_max - x_h1a_max)**2 + (z_h2a_max - z_h1a_max)**2)
                if dist_max < D_fases:
                    print(f"   ⚠️  WARNING: Distancia D_fases {nombre_h1a}-h2a (máxima): {dist_max:.3f}m < D_fases({D_fases:.3f}m)")
    
    def _checkear_zonas_prohibicion_s(self, h2a, Lmen2, h1a, theta_max, theta_tormenta):
        """Checkear que conductor h2a no infringe zonas s de elementos fijos
        
        Verifica en 3 declinaciones: reposo, tormenta, máxima
        """
        Lk = self.geo.lk
        s_reposo = self.geo.dimensiones["s_estructura"]
        s_decmax = self.geo.dimensiones.get("s_decmax", s_reposo)
        s_tormenta = self.geo.dimensiones.get("s_tormenta", s_reposo)
        D_fases = self.geo.dimensiones["D_fases"]
        Lmen1 = self.geo.dimensiones["Lmen1"]
        
        # Construir estructura de nodos temporal
        nodos_temp = {}
        nodos_temp["BASE"] = Nodo("BASE", 0, 0, 0, "base")
        nodos_temp["CROSS_H1"] = Nodo("CROSS_H1", 0, 0, h1a, "cruce")
        nodos_temp["BASE"].agregar_conexion(nodos_temp["CROSS_H1"], "columna")
        
        # Nodos conductores h1a
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h1a) < 1e-3:
                x, y, z = nodo.coordenadas
                nodos_temp[nombre] = Nodo(nombre, x, y, z, "conductor")
                nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp[nombre], "mensula")
        
        parametros = {
            'Lk': Lk,
            'D_fases': D_fases,
            's_reposo': s_reposo,
            's_decmax': s_decmax,
            's_tormenta': s_tormenta,
            'Dhg': 0,
            'theta_max': theta_max,
            'theta_tormenta': theta_tormenta
        }
        
        # Verificar en REPOSO
        x_reposo = Lmen2
        z_reposo = h2a - Lk
        verificador = crear_verificador_desde_nodos(nodos_temp, parametros)
        resultado_reposo = verificador.verificar_punto(x_reposo, z_reposo)
        if resultado_reposo['infringe']:
            print(f"   ⚠️  WARNING: Conductor h2a (reposo) infringe: {', '.join(resultado_reposo['zonas_infringidas'])}")
        
        # Verificar en TORMENTA
        if theta_tormenta > 0:
            x_tormenta = Lmen2 + Lk * math.sin(math.radians(theta_tormenta))
            z_tormenta = h2a - Lk * math.cos(math.radians(theta_tormenta))
            resultado_tormenta = verificador.verificar_punto(x_tormenta, z_tormenta)
            if resultado_tormenta['infringe']:
                print(f"   ⚠️  WARNING: Conductor h2a (tormenta) infringe: {', '.join(resultado_tormenta['zonas_infringidas'])}")
        
        # Verificar en MÁXIMA
        if theta_max > 0:
            x_max = Lmen2 + Lk * math.sin(math.radians(theta_max))
            z_max = h2a - Lk * math.cos(math.radians(theta_max))
            resultado_max = verificador.verificar_punto(x_max, z_max)
            if resultado_max['infringe']:
                print(f"   ⚠️  WARNING: Conductor h2a (máxima) infringe: {', '.join(resultado_max['zonas_infringidas'])}")
            else:
                # Mostrar distancias mínimas solo si no hay infracción
                for tipo_zona, distancias in resultado_max['distancias'].items():
                    if distancias['minima'] < float('inf') and distancias['minima'] < 1.0:
                        print(f"   📊 Distancia a {tipo_zona}: {distancias['minima']:.3f}m")
    
    def _crear_nodos_conductores_h2a(self, h2a, Lmen2):
        """Crear nodos conductores en segunda altura según disposición/terna"""
        
        if self.geo.terna == "Simple" and self.geo.disposicion == "vertical":
            # Vertical simple: C2
            self.geo.nodos["C2"] = NodoEstructural(
                "C2", (Lmen2, 0.0, h2a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodo C2 creado en ({Lmen2:.2f}, 0, {h2a:.2f})")
        
        elif self.geo.terna == "Simple" and self.geo.disposicion == "triangular":
            # Triangular simple: C3 en (0, 0, h2a)
            self.geo.nodos["C3"] = NodoEstructural(
                "C3", (0.0, 0.0, h2a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodo C3 creado en (0, 0, {h2a:.2f})")
        
        elif self.geo.terna == "Doble" and self.geo.disposicion == "vertical":
            # Doble vertical: C2_R, C2_L
            self.geo.nodos["C2_R"] = NodoEstructural(
                "C2_R", (Lmen2, 0.0, h2a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C2_L"] = NodoEstructural(
                "C2_L", (-Lmen2, 0.0, h2a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodos C2_R, C2_L creados en (±{Lmen2:.2f}, 0, {h2a:.2f})")
        
        elif self.geo.terna == "Doble" and self.geo.disposicion == "triangular":
            # Doble triangular: C3_R, C3_L en h2a (usa Lmen2)
            self.geo.nodos["C3_R"] = NodoEstructural(
                "C3_R", (Lmen2, 0.0, h2a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C3_L"] = NodoEstructural(
                "C3_L", (-Lmen2, 0.0, h2a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodos C3_R, C3_L creados en (±{Lmen2:.2f}, 0, {h2a:.2f})")
        else:
            print(f"   ⚠️  Configuración no reconocida: terna={self.geo.terna}, disposicion={self.geo.disposicion}")
    
    def _ejecutar_conectador(self):
        """Ejecutar conectador de nodos al finalizar etapa"""
        print("   🔌 Ejecutando conectador de nodos...")
        
        if not hasattr(self.geo, 'conexiones'):
            self.geo.conexiones = []
        
        conexiones_anteriores = set(self.geo.conexiones)
        
        self.geo._generar_conexiones()
        
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        if conexiones_nuevas:
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      INFO: {origen} → {destino} ({tipo})")
