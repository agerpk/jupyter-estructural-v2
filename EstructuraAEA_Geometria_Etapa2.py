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
        
        # Calcular theta_max y obtener theta_tormenta
        vano = self.geo.dimensiones.get('vano', 400)
        theta_max = self.geo.calcular_theta_max(vano)
        theta_tormenta = self.geo.dimensiones.get('theta_tormenta', theta_max / 2.0)
        
        # Calcular h2a_inicial
        h1a = self.geo.dimensiones["h1a"]
        D_fases = self.geo.dimensiones["D_fases"]
        s_reposo = self.geo.dimensiones.get("s_reposo", 0)
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
        
        # Optimizar h2a considerando zonas prohibidas
        h2a_final = h2a_inicial
        
        # SIEMPRE buscar altura óptima considerando zonas prohibidas
        zoptimo2 = self._buscar_altura_fuera_zonas_prohibidas_h1a(Lmen2, h1a, D_fases, s_reposo, theta_max, theta_tormenta)
        h2a_final = zoptimo2 + HADD_ENTRE_AMARRES
        
        # Aplicar defasaje por hielo si está activado
        if self.geo.defasaje_mensula_hielo and self.geo.lmen_extra_hielo > 0:
            mensula_defasar = self.geo.mensula_defasar
            
            if mensula_defasar == "segunda":
                # Lmen2 será incrementada, recalcular altura óptima
                Lmen2 = Lmen2 + self.geo.lmen_extra_hielo
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
        """Buscar altura máxima en línea x=x_linea que no infringe zonas prohibidas de h1a
        
        Baja desde h2a_inicial de a 0.01m hasta encontrar infracción, retorna última altura sin infracción.
        Verifica D_fases en reposo y s en las 3 declinaciones (reposo, tormenta, máxima).
        """
        Lk = self.geo.lk
        s_decmax = self.geo.dimensiones.get("s_decmax", s_reposo)
        s_tormenta = self.geo.dimensiones.get("s_tormenta", s_reposo)
        HADD = self.geo.hadd_entre_amarres
        
        # Construir estructura de nodos temporal
        nodos_temp = {}
        nodos_temp["BASE"] = Nodo("BASE", 0, 0, 0, "base")
        nodos_temp["CROSS_H1"] = Nodo("CROSS_H1", 0, 0, h1a, "cruce")
        nodos_temp["BASE"].agregar_conexion(nodos_temp["CROSS_H1"], "columna")
        
        # Nodos conductores h1a (coordenadas finales)
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor" and abs(nodo.coordenadas[2] - h1a) < 1e-3:
                x, y, z = nodo.coordenadas
                nodos_temp[nombre] = Nodo(nombre, x, y, z, "conductor")
                nodos_temp["CROSS_H1"].agregar_conexion(nodos_temp[nombre], "mensula")
        
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
            'offset_columna_base': self.geo.offset_columna_base,
            'offset_columna_base_tipo': self.geo.offset_columna_base_tipo,
            'offset_columna_base_inicio': self.geo.offset_columna_base_inicio,
            'offset_columna_base_fin': self.geo.offset_columna_base_fin,
            'offset_columna_inter': self.geo.offset_columna_inter,
            'offset_columna_inter_tipo': self.geo.offset_columna_inter_tipo,
            'offset_columna_inter_inicio': self.geo.offset_columna_inter_inicio,
            'offset_columna_inter_fin': self.geo.offset_columna_inter_fin,
            'offset_mensula': self.geo.offset_mensula,
            'offset_mensula_tipo': self.geo.offset_mensula_tipo,
            'offset_mensula_inicio': self.geo.offset_mensula_inicio,
            'offset_mensula_fin': self.geo.offset_mensula_fin,
            'h_cross_h1': h1a
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
            'offset_columna_base': self.geo.offset_columna_base,
            'offset_columna_base_tipo': self.geo.offset_columna_base_tipo,
            'offset_columna_base_inicio': self.geo.offset_columna_base_inicio,
            'offset_columna_base_fin': self.geo.offset_columna_base_fin,
            'offset_columna_inter': self.geo.offset_columna_inter,
            'offset_columna_inter_tipo': self.geo.offset_columna_inter_tipo,
            'offset_columna_inter_inicio': self.geo.offset_columna_inter_inicio,
            'offset_columna_inter_fin': self.geo.offset_columna_inter_fin,
            'offset_mensula': self.geo.offset_mensula,
            'offset_mensula_tipo': self.geo.offset_mensula_tipo,
            'offset_mensula_inicio': self.geo.offset_mensula_inicio,
            'offset_mensula_fin': self.geo.offset_mensula_fin,
            'h_cross_h1': h1a
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
            'offset_columna_base': self.geo.offset_columna_base,
            'offset_columna_base_tipo': self.geo.offset_columna_base_tipo,
            'offset_columna_base_inicio': self.geo.offset_columna_base_inicio,
            'offset_columna_base_fin': self.geo.offset_columna_base_fin,
            'offset_columna_inter': self.geo.offset_columna_inter,
            'offset_columna_inter_tipo': self.geo.offset_columna_inter_tipo,
            'offset_columna_inter_inicio': self.geo.offset_columna_inter_inicio,
            'offset_columna_inter_fin': self.geo.offset_columna_inter_fin,
            'offset_mensula': self.geo.offset_mensula,
            'offset_mensula_tipo': self.geo.offset_mensula_tipo,
            'offset_mensula_inicio': self.geo.offset_mensula_inicio,
            'offset_mensula_fin': self.geo.offset_mensula_fin,
            'h_cross_h1': h1a
        }
        verificador_max = crear_verificador_desde_nodos(nodos_temp, parametros_max)
        
        # Calcular h2a_inicial
        if Lk > 0:
            h2a_inicial = max(
                h1a + D_fases + HADD,
                h1a + s_reposo + Lk + HADD
            )
        else:
            h2a_inicial = h1a + D_fases + HADD
        
        # Subir desde h2a_inicial hasta que NO haya infracciones
        h2a = h2a_inicial
        incremento = 0.01
        max_iteraciones = 10000
        
        for i in range(max_iteraciones):
            # Verificar cada declinación contra SU franja correspondiente
            # 1. Reposo (θ=0): verificar contra franja s_reposo + D_fases
            x_reposo = x_linea
            z_reposo = h2a - Lk
            resultado_reposo = verificador_reposo.verificar_punto(x_reposo, z_reposo)
            
            # 2. Tormenta (θ_tormenta): verificar contra franja s_tormenta
            x_tormenta = x_linea - Lk * math.sin(math.radians(theta_tormenta))
            z_tormenta = h2a - Lk * math.cos(math.radians(theta_tormenta))
            resultado_tormenta = verificador_tormenta.verificar_punto(x_tormenta, z_tormenta)
            
            # 3. Máxima (θ_max): verificar contra franja s_decmax
            x_max = x_linea - Lk * math.sin(math.radians(theta_max))
            z_max = h2a - Lk * math.cos(math.radians(theta_max))
            resultado_max = verificador_max.verificar_punto(x_max, z_max)
            
            # Detectar infracciones
            hay_infraccion = False
            razon_infraccion = None
            
            if resultado_reposo['infringe']:
                hay_infraccion = True
                razon_infraccion = f"Reposo (θ=0°): {', '.join(resultado_reposo['zonas_infringidas'])}"
            elif resultado_tormenta['infringe']:
                hay_infraccion = True
                razon_infraccion = f"Tormenta (θ={theta_tormenta:.1f}°): {', '.join(resultado_tormenta['zonas_infringidas'])}"
            elif resultado_max['infringe']:
                hay_infraccion = True
                razon_infraccion = f"Máxima (θ={theta_max:.1f}°): {', '.join(resultado_max['zonas_infringidas'])}"
            
            if not hay_infraccion:
                # No hay infracciones, esta es la altura válida
                if h2a > h2a_inicial:
                    print(f"   🔍 Altura ajustada en x={x_linea:.2f}m: z={h2a:.3f}m (subió {h2a - h2a_inicial:.3f}m)")
                else:
                    print(f"   🔍 Altura inicial válida en x={x_linea:.2f}m: z={h2a:.3f}m")
                return h2a
            
            # Hay infracción, subir y continuar
            if i == 0:
                print(f"   ⚠️  h2a={h2a:.3f}m infringe: {razon_infraccion}")
            
            h2a += incremento
        
        print(f"   ⚠️  Límite de iteraciones alcanzado en x={x_linea:.2f}m: z={h2a:.3f}m")
        return h2a
    
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
        s_reposo = self.geo.dimensiones.get("s_reposo", 0)
        s_decmax = self.geo.dimensiones.get("s_decmax", 0)
        s_tormenta = self.geo.dimensiones.get("s_tormenta", 0)
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
            'theta_tormenta': theta_tormenta,
            'offset_columna_base': self.geo.offset_columna_base,
            'offset_columna_base_tipo': self.geo.offset_columna_base_tipo,
            'offset_columna_base_inicio': self.geo.offset_columna_base_inicio,
            'offset_columna_base_fin': self.geo.offset_columna_base_fin,
            'offset_columna_inter': self.geo.offset_columna_inter,
            'offset_columna_inter_tipo': self.geo.offset_columna_inter_tipo,
            'offset_columna_inter_inicio': self.geo.offset_columna_inter_inicio,
            'offset_columna_inter_fin': self.geo.offset_columna_inter_fin,
            'offset_mensula': self.geo.offset_mensula,
            'offset_mensula_tipo': self.geo.offset_mensula_tipo,
            'offset_mensula_inicio': self.geo.offset_mensula_inicio,
            'offset_mensula_fin': self.geo.offset_mensula_fin,
            'h_cross_h1': h1a
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
            # Triangular simple: C2_R en ménsula derecha (NO en centro)
            self.geo.nodos["C2_R"] = NodoEstructural(
                "C2_R", (Lmen2, 0.0, h2a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodo C2_R creado en ({Lmen2:.2f}, 0, {h2a:.2f})")
        
        elif self.geo.terna == "Simple" and self.geo.disposicion == "triangular-mensulas":
            # Triangular-mensulas simple: C3 en ménsula derecha, luego reposicionar C2
            self.geo.nodos["C3"] = NodoEstructural(
                "C3", (Lmen2, 0.0, h2a), "conductor",
                self.geo.cable_conductor, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
            )
            print(f"   🔵 Nodo C3 creado en ({Lmen2:.2f}, 0, {h2a:.2f})")
            
            # Reposicionar C2 a altura intermedia entre h1a y h2a
            h1a = self.geo.dimensiones["h1a"]
            h1ab = (h1a + h2a) / 2.0
            if "C2" in self.geo.nodos:
                # Actualizar coordenadas de C2 existente
                x_c2, y_c2, z_c2 = self.geo.nodos["C2"].coordenadas
                self.geo.nodos["C2"].coordenadas = (x_c2, y_c2, h1ab)
                print(f"   🔄 Nodo C2 reposicionado a ({x_c2:.2f}, 0, {h1ab:.2f})")
            
            # Crear CROSS_H3 en h1ab
            self.geo.nodos["CROSS_H3"] = NodoEstructural("CROSS_H3", (0.0, 0.0, h1ab), "cruce")
            print(f"   🔵 Nodo CROSS_H3 creado en (0, 0, {h1ab:.2f})")
            
            # Guardar h1ab en dimensiones
            self.geo.dimensiones["h1ab"] = h1ab
        
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
