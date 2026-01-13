# EstructuraAEA_Geometria_Etapa3.py
import math
from NodoEstructural import NodoEstructural
from utils.geometria_zonas import Nodo, crear_verificador_desde_nodos


class GeometriaEtapa3:
    """Etapa 3: h3a (Tercer Amarre)"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def ejecutar(self):
        print("🔧 ETAPA 3: h3a (tercer amarre)")
        
        # Solo aplica para disposición vertical
        if self.geo.disposicion != "vertical":
            print("   ⏭️  No aplica h3a para esta disposición")
            return
        
        # Calcular theta_max y theta_tormenta
        vano = self.geo.dimensiones.get('vano', 400)
        theta_max = self.geo.calcular_theta_max(vano)
        if theta_max >= 99.0:
            theta_max = 0.0
        theta_tormenta = theta_max / 2.0
        
        # Calcular h3a_inicial
        h2a = self.geo.dimensiones["h2a"]
        D_fases = self.geo.dimensiones["D_fases"]
        s_reposo = self.geo.dimensiones.get("s_reposo", 0)
        Lk = self.geo.lk
        HADD_ENTRE_AMARRES = self.geo.hadd_entre_amarres
        
        if Lk > 0:
            h3a_inicial = max(
                h2a + D_fases + HADD_ENTRE_AMARRES,
                h2a + s_reposo + Lk + HADD_ENTRE_AMARRES
            )
        else:
            h3a_inicial = h2a + D_fases + HADD_ENTRE_AMARRES
        
        # Inicializar Lmen3 PRE hielo (siempre basado en Lmen1 PRE hielo)
        Lmen1_original = self.geo.dimensiones["Lmen1"]  # PRE hielo
        Lmen3 = max(Lmen1_original, self.geo.long_mensula_min_conductor)
        
        # Optimizar h3a si hay defasaje por hielo
        h3a_final = h3a_inicial
        
        if self.geo.defasaje_mensula_hielo and self.geo.lmen_extra_hielo > 0:
            mensula_defasar = self.geo.mensula_defasar
            
            # Si la defasada es "tercera" O "primera y tercera"
            if mensula_defasar == "tercera" or mensula_defasar == "primera y tercera":
                # Lmen3 será incrementada, buscar altura óptima
                Lmen3 = Lmen3 + self.geo.lmen_extra_hielo
                # Buscar altura óptima considerando zonas prohibidas de h2a
                zoptimo3 = self._buscar_altura_fuera_zonas_prohibidas_h2a(Lmen3, h2a, D_fases, s_reposo, theta_max, theta_tormenta)
                h3a_final = zoptimo3 + HADD_ENTRE_AMARRES
                print(f"   ❄️  Defasaje hielo '{mensula_defasar}': Lmen3 = {Lmen3:.2f}m, h3a = {h3a_final:.2f}m")
            
            elif mensula_defasar == "segunda":
                # Lmen2 fue incrementada en Etapa2, Lmen3 permanece normal (PRE hielo)
                # Recheckear altura considerando zonas prohibidas de h2a
                zoptimo3 = self._buscar_altura_fuera_zonas_prohibidas_h2a(Lmen3, h2a, D_fases, s_reposo, theta_max, theta_tormenta)
                h3a_final = zoptimo3 + HADD_ENTRE_AMARRES
                print(f"   🔵 Optimización por defasaje 'segunda': h3a reducida a {h3a_final:.2f}m")
        
        # Guardar resultados
        self.geo.dimensiones["h3a"] = h3a_final
        self.geo.dimensiones["Lmen3"] = Lmen3
        
        # Checkear zonas de prohibición D_fases entre conductores h2a y h3a
        self._checkear_zonas_dfases_entre_alturas(h3a_final, Lmen3, h2a, theta_max, theta_tormenta)
        
        # Checkear zonas de prohibición s antes de crear nodos
        self._checkear_zonas_prohibicion_s(h3a_final, Lmen3, h2a, theta_max, theta_tormenta)
        
        # Crear nodos conductores según disposición/terna
        self._crear_nodos_conductores_h3a(h3a_final, Lmen3)
        
        # Crear nodo CROSS en h3a (siempre, incluso si h3a = h2a)
        self.geo.nodos["CROSS_H3"] = NodoEstructural("CROSS_H3", (0.0, 0.0, h3a_final), "cruce")
        print(f"   🔵 Nodo CROSS_H3 creado en (0, 0, {h3a_final:.2f})")
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ h3a={h3a_final:.2f}m, Lmen3={Lmen3:.2f}m")
    
    def _buscar_altura_fuera_zonas_prohibidas_h2a(self, x_linea, h2a, D_fases, s_reposo, theta_max, theta_tormenta):
        """Buscar altura máxima en línea x=x_linea que no infringe zonas prohibidas de h2a
        
        Baja desde h3a_inicial de a 0.01m hasta encontrar infracción, retorna última altura sin infracción.
        Verifica D_fases en reposo y s en las 3 declinaciones (reposo, tormenta, máxima).
        """
        Lk = self.geo.lk
        s_decmax = self.geo.dimensiones.get("s_decmax", s_reposo)
        s_tormenta = self.geo.dimensiones.get("s_tormenta", s_reposo)
        h1a = self.geo.dimensiones["h1a"]
        HADD = self.geo.hadd_entre_amarres
        
        # Construir estructura de nodos temporal
        nodos_temp = {}
        nodos_temp["BASE"] = Nodo("BASE", 0, 0, 0, "base")
        nodos_temp["CROSS_H1"] = Nodo("CROSS_H1", 0, 0, h1a, "cruce")
        nodos_temp["BASE"].agregar_conexion(nodos_temp["CROSS_H1"], "columna")
        nodos_temp["CROSS_H2"] = Nodo("CROSS_H2", 0, 0, h2a, "cruce")
        nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp["CROSS_H2"], "columna")
        
        # Nodos conductores h1a
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h1a) < 1e-3:
                x, y, z = nodo.coordenadas
                nodos_temp[nombre] = Nodo(nombre, x, y, z, "conductor")
                nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp[nombre], "mensula")
        
        # Nodos conductores h2a
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h2a) < 1e-3:
                x, y, z = nodo.coordenadas
                nodos_temp[nombre] = Nodo(nombre, x, y, z, "conductor")
                nodos_temp["CROSS_H2"].agregar_conexion(nodos_temp[nombre], "mensula")
        
        # Crear 3 verificadores: cada uno genera SOLO su franja correspondiente
        print(f"   📊 DEBUG: s_reposo={s_reposo:.3f}, s_tormenta={s_tormenta:.3f}, s_decmax={s_decmax:.3f}")
        print(f"   📊 DEBUG: theta_max={theta_max:.2f}°, theta_tormenta={theta_tormenta:.2f}°")
        
        # 1. Verificador reposo: genera franjas s_reposo (las otras en 0)
        parametros_reposo = {
            'Lk': Lk,
            'D_fases': D_fases,
            's_reposo': s_reposo,
            's_decmax': 0,
            's_tormenta': 0,
            'Dhg': 0,
            'theta_max': 0,
            'theta_tormenta': 0,
            'd_fases_solo_reposo': True,
            'z_min_corte': h2a
        }
        verificador_reposo = crear_verificador_desde_nodos(nodos_temp, parametros_reposo)
        
        # 2. Verificador tormenta: genera SOLO franjas s_tormenta
        parametros_tormenta = {
            'Lk': Lk,
            'D_fases': 0,
            's_reposo': 0,
            's_decmax': 0,
            's_tormenta': s_tormenta,
            'Dhg': 0,
            'theta_max': 0,
            'theta_tormenta': theta_tormenta,
            'd_fases_solo_reposo': True,
            'z_min_corte': h2a
        }
        verificador_tormenta = crear_verificador_desde_nodos(nodos_temp, parametros_tormenta)
        
        # 3. Verificador máxima: genera SOLO franjas s_decmax
        parametros_max = {
            'Lk': Lk,
            'D_fases': 0,
            's_reposo': 0,
            's_decmax': s_decmax,
            's_tormenta': 0,
            'Dhg': 0,
            'theta_max': theta_max,
            'theta_tormenta': 0,
            'd_fases_solo_reposo': True,
            'z_min_corte': h2a
        }
        verificador_max = crear_verificador_desde_nodos(nodos_temp, parametros_max)
        
        # Calcular h3a_inicial
        if Lk > 0:
            h3a_inicial = max(
                h2a + D_fases + HADD,
                h2a + s_reposo + Lk + HADD
            )
        else:
            h3a_inicial = h2a + D_fases + HADD
        
        # Bajar desde h3a_inicial hasta encontrar infracción
        h3a = h3a_inicial
        incremento = 0.01
        max_iteraciones = 1000
        ultima_sin_infraccion = h3a_inicial
        razon_detencion = None
        
        for i in range(max_iteraciones):
            # Verificar cada declinación contra SU franja correspondiente
            # 1. Reposo (θ=0): verificar contra franja s_reposo + D_fases
            x_reposo = x_linea
            z_reposo = h3a - Lk
            resultado_reposo = verificador_reposo.verificar_punto(x_reposo, z_reposo)
            
            # 2. Tormenta (θ_tormenta): verificar contra franja s_tormenta
            x_tormenta = x_linea - Lk * math.sin(math.radians(theta_tormenta))
            z_tormenta = h3a - Lk * math.cos(math.radians(theta_tormenta))
            resultado_tormenta = verificador_tormenta.verificar_punto(x_tormenta, z_tormenta)
            
            if i == 0:  # Solo primera iteración
                print(f"   📍 h3a={h3a:.3f}: Reposo=({x_reposo:.3f},{z_reposo:.3f}), Tormenta=({x_tormenta:.3f},{z_tormenta:.3f})")
            
            # 3. Máxima (θ_max): verificar contra franja s_decmax
            x_max = x_linea - Lk * math.sin(math.radians(theta_max))
            z_max = h3a - Lk * math.cos(math.radians(theta_max))
            resultado_max = verificador_max.verificar_punto(x_max, z_max)
            
            # Detectar infracciones
            if resultado_reposo['infringe']:
                razon_detencion = f"Reposo (θ=0°): {', '.join(resultado_reposo['zonas_infringidas'])}"
            elif resultado_tormenta['infringe']:
                razon_detencion = f"Tormenta (θ={theta_tormenta:.1f}°): {', '.join(resultado_tormenta['zonas_infringidas'])}"
            elif resultado_max['infringe']:
                razon_detencion = f"Máxima (θ={theta_max:.1f}°): {', '.join(resultado_max['zonas_infringidas'])}"
            
            if razon_detencion:
                # Encontró infracción, retornar última altura sin infracción
                print(f"   🔍 Altura óptima en x={x_linea:.2f}m: z={ultima_sin_infraccion:.3f}m (bajó {h3a_inicial - ultima_sin_infraccion:.3f}m)")
                print(f"   🛑 Detenido por: {razon_detencion}")
                return ultima_sin_infraccion
            
            # Sin infracción, guardar y seguir bajando
            ultima_sin_infraccion = h3a
            h3a -= incremento
            
            # No bajar más allá de h2a
            if h3a <= h2a:
                print(f"   🔍 Altura óptima en x={x_linea:.2f}m: z={ultima_sin_infraccion:.3f}m (límite h2a alcanzado)")
                return ultima_sin_infraccion
        
        print(f"   🔍 Altura óptima en x={x_linea:.2f}m: z={ultima_sin_infraccion:.3f}m (sin infracciones)")
        return ultima_sin_infraccion
    
    def _checkear_zonas_dfases_entre_alturas(self, h3a, Lmen3, h2a, theta_max, theta_tormenta):
        """Checkear que conductores h3a no infringen zonas D_fases de conductores h2a
        
        Verifica en 3 declinaciones: reposo, tormenta, máxima (ambos conductores con misma declinación)
        """
        Lk = self.geo.lk
        D_fases = self.geo.dimensiones["D_fases"]
        
        # Posiciones conductores h2a
        conductores_h2a = [(n, nodo) for n, nodo in self.geo.nodos.items() 
                          if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h2a) < 1e-3]
        
        # Verificar en REPOSO
        z_conductor_h3a_reposo = h3a - Lk
        for nombre_h2a, nodo_h2a in conductores_h2a:
            x_h2a, y_h2a, z_amarre_h2a = nodo_h2a.coordenadas
            z_conductor_h2a_reposo = z_amarre_h2a - Lk
            dist_reposo = abs(z_conductor_h3a_reposo - z_conductor_h2a_reposo)
            if dist_reposo < D_fases:
                print(f"   ⚠️  WARNING: Distancia D_fases {nombre_h2a}-h3a (reposo): {dist_reposo:.3f}m < D_fases({D_fases:.3f}m)")
        
        # Verificar en TORMENTA
        if theta_tormenta > 0:
            x_h3a_tormenta = Lmen3 + Lk * math.sin(math.radians(theta_tormenta))
            z_h3a_tormenta = h3a - Lk * math.cos(math.radians(theta_tormenta))
            for nombre_h2a, nodo_h2a in conductores_h2a:
                x_h2a, y_h2a, z_amarre_h2a = nodo_h2a.coordenadas
                x_h2a_tormenta = x_h2a + Lk * math.sin(math.radians(theta_tormenta))
                z_h2a_tormenta = z_amarre_h2a - Lk * math.cos(math.radians(theta_tormenta))
                dist_tormenta = math.sqrt((x_h3a_tormenta - x_h2a_tormenta)**2 + (z_h3a_tormenta - z_h2a_tormenta)**2)
                if dist_tormenta < D_fases:
                    print(f"   ⚠️  WARNING: Distancia D_fases {nombre_h2a}-h3a (tormenta): {dist_tormenta:.3f}m < D_fases({D_fases:.3f}m)")
        
        # Verificar en MÁXIMA
        if theta_max > 0:
            x_h3a_max = Lmen3 + Lk * math.sin(math.radians(theta_max))
            z_h3a_max = h3a - Lk * math.cos(math.radians(theta_max))
            for nombre_h2a, nodo_h2a in conductores_h2a:
                x_h2a, y_h2a, z_amarre_h2a = nodo_h2a.coordenadas
                x_h2a_max = x_h2a + Lk * math.sin(math.radians(theta_max))
                z_h2a_max = z_amarre_h2a - Lk * math.cos(math.radians(theta_max))
                dist_max = math.sqrt((x_h3a_max - x_h2a_max)**2 + (z_h3a_max - z_h2a_max)**2)
                if dist_max < D_fases:
                    print(f"   ⚠️  WARNING: Distancia D_fases {nombre_h2a}-h3a (máxima): {dist_max:.3f}m < D_fases({D_fases:.3f}m)")
    
    def _checkear_zonas_prohibicion_s(self, h3a, Lmen3, h2a, theta_max, theta_tormenta):
        """Checkear que conductor h3a no infringe zonas s de elementos fijos
        
        Verifica en 3 declinaciones: reposo, tormenta, máxima
        """
        Lk = self.geo.lk
        s_reposo = self.geo.dimensiones.get("s_reposo", 0)
        s_decmax = self.geo.dimensiones.get("s_decmax", 0)
        s_tormenta = self.geo.dimensiones.get("s_tormenta", 0)
        D_fases = self.geo.dimensiones["D_fases"]
        h1a = self.geo.dimensiones["h1a"]
        Lmen1 = self.geo.dimensiones["Lmen1"]
        Lmen2 = self.geo.dimensiones["Lmen2"]
        
        # Construir estructura de nodos temporal
        nodos_temp = {}
        nodos_temp["BASE"] = Nodo("BASE", 0, 0, 0, "base")
        nodos_temp["CROSS_H1"] = Nodo("CROSS_H1", 0, 0, h1a, "cruce")
        nodos_temp["BASE"].agregar_conexion(nodos_temp["CROSS_H1"], "columna")
        nodos_temp["CROSS_H2"] = Nodo("CROSS_H2", 0, 0, h2a, "cruce")
        nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp["CROSS_H2"], "columna")
        
        # Nodos conductores h1a
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h1a) < 1e-3:
                x, y, z = nodo.coordenadas
                nodos_temp[nombre] = Nodo(nombre, x, y, z, "conductor")
                nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp[nombre], "mensula")
        
        # Nodos conductores h2a
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h2a) < 1e-3:
                x, y, z = nodo.coordenadas
                nodos_temp[nombre] = Nodo(nombre, x, y, z, "conductor")
                nodos_temp["CROSS_H2"].agregar_conexion(nodos_temp[nombre], "mensula")
        
        parametros = {
            'Lk': Lk,
            'D_fases': D_fases,
            's_reposo': s_reposo,
            's_decmax': s_decmax,
            's_tormenta': s_tormenta,
            'Dhg': 0,
            'theta_max': theta_max,
            'theta_tormenta': theta_tormenta,
            'z_min_corte': h2a
        }
        
        # Verificar en REPOSO
        x_reposo = Lmen3
        z_reposo = h3a - Lk
        verificador = crear_verificador_desde_nodos(nodos_temp, parametros)
        resultado_reposo = verificador.verificar_punto(x_reposo, z_reposo)
        if resultado_reposo['infringe']:
            print(f"   ⚠️  WARNING: Conductor h3a (reposo) infringe: {', '.join(resultado_reposo['zonas_infringidas'])}")
        
        # Verificar en TORMENTA
        if theta_tormenta > 0:
            x_tormenta = Lmen3 + Lk * math.sin(math.radians(theta_tormenta))
            z_tormenta = h3a - Lk * math.cos(math.radians(theta_tormenta))
            resultado_tormenta = verificador.verificar_punto(x_tormenta, z_tormenta)
            if resultado_tormenta['infringe']:
                print(f"   ⚠️  WARNING: Conductor h3a (tormenta) infringe: {', '.join(resultado_tormenta['zonas_infringidas'])}")
        
        # Verificar en MÁXIMA
        if theta_max > 0:
            x_max = Lmen3 + Lk * math.sin(math.radians(theta_max))
            z_max = h3a - Lk * math.cos(math.radians(theta_max))
            resultado_max = verificador.verificar_punto(x_max, z_max)
            if resultado_max['infringe']:
                print(f"   ⚠️  WARNING: Conductor h3a (máxima) infringe: {', '.join(resultado_max['zonas_infringidas'])}")
            else:
                # Mostrar distancias mínimas solo si no hay infracción
                for tipo_zona, distancias in resultado_max['distancias'].items():
                    if distancias['minima'] < float('inf') and distancias['minima'] < 1.0:
                        print(f"   📊 Distancia a {tipo_zona}: {distancias['minima']:.3f}m")
    
    def _crear_nodos_conductores_h3a(self, h3a, Lmen3):
        """Crear nodos conductores en tercera altura según disposición/terna"""
        
        if self.geo.terna == "Simple" and self.geo.disposicion == "vertical":
            # Vertical simple: C3
            self.geo.nodos["C3"] = NodoEstructural(
                "C3", (Lmen3, 0.0, h3a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodo C3 creado en ({Lmen3:.2f}, 0, {h3a:.2f})")
        
        elif self.geo.terna == "Doble" and self.geo.disposicion == "vertical":
            # Doble vertical: C3_R, C3_L
            self.geo.nodos["C3_R"] = NodoEstructural(
                "C3_R", (Lmen3, 0.0, h3a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            self.geo.nodos["C3_L"] = NodoEstructural(
                "C3_L", (-Lmen3, 0.0, h3a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodos C3_R, C3_L creados en (±{Lmen3:.2f}, 0, {h3a:.2f})")
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
