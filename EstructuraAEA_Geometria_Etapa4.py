# EstructuraAEA_Geometria_Etapa4.py
import math
from NodoEstructural import NodoEstructural


class GeometriaEtapa4:
    """Etapa 4: Cable de Guardia"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def ejecutar(self):
        print("🔧 ETAPA 4: Cable de Guardia")
        
        if self.geo.cant_hg == 0:
            print("   🚫 No hay cable guardia (CANT_HG = 0)")
            self.geo.dimensiones["hhg"] = 0.0
            self.geo.dimensiones["lmenhg"] = 0.0
            return
        
        # Obtener parámetros
        ang_apant = self.geo.ang_apantallamiento
        hadd_hg = self.geo.hadd_hg
        lmenhg_min = self.geo.long_mensula_min_guardia
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        
        # Obtener conductores y sus posiciones (Lk debajo del nodo)
        conductores = self._obtener_posiciones_conductores()
        
        if self.geo.cant_hg == 1 and self.geo.hg_centrado:
            self._crear_guardia_centrado(conductores, ang_apant, hadd_hg, defasaje_y)
        elif self.geo.cant_hg == 1 and not self.geo.hg_centrado:
            self._crear_guardia_no_centrado(conductores, ang_apant, hadd_hg, lmenhg_min, defasaje_y)
        elif self.geo.cant_hg == 2:
            self._crear_dos_guardias(conductores, ang_apant, hadd_hg, lmenhg_min, defasaje_y)
        
        # Crear nodo VIENTO
        self._crear_nodo_viento()
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ Cable guardia configurado: hhg={self.geo.dimensiones.get('hhg', 0):.2f}m")
    
    def _obtener_posiciones_conductores(self):
        """Obtener posiciones de conductores (Lk debajo del nodo)"""
        conductores = []
        Lk = self.geo.lk
        
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor":
                x, y, z_amarre = nodo.coordenadas
                z_conductor = z_amarre - Lk
                conductores.append((nombre, x, y, z_conductor))
        
        print(f"   📍 {len(conductores)} conductores encontrados")
        return conductores
    
    def _crear_guardia_centrado(self, conductores, ang_apant, hadd_hg, defasaje_y):
        """CANT_HG=1, HG_CENTRADO=True"""
        # Encontrar conductor más alto y más alejado del eje x=0
        z_max = max(c[3] for c in conductores)
        x_max = max(abs(c[1]) for c in conductores)
        
        # Calcular hhg
        hhg = z_max + x_max * math.tan(math.radians(ang_apant))
        
        # Obtener defasaje_y_guardia del objeto geometria
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        
        # Crear nodo HG1
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (0.0, defasaje_y, hhg), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        self.geo.dimensiones["hhg"] = hhg
        self.geo.dimensiones["lmenhg"] = 0.0
        
        print(f"   🛡️  Guardia centrado: HG1 en (0, {defasaje_y}, {hhg:.2f})")
    
    def _crear_guardia_no_centrado(self, conductores, ang_apant, hadd_hg, lmenhg_min, defasaje_y):
        """CANT_HG=1, HG_CENTRADO=False - Solo para disposición triangular terna simple"""
        # Validar que solo aplica para triangular simple
        if not (self.geo.disposicion == "triangular" and self.geo.terna == "Simple"):
            print(f"   ⚠️  Guardia no centrado solo aplica para triangular simple, usando centrado")
            self._crear_guardia_centrado(conductores, ang_apant, hadd_hg, defasaje_y)
            return
        
        # Calcular recta de apantallamiento para cada conductor
        # Pendiente: -tan(ang_apant) para x>0, +tan(ang_apant) para x<0
        pendiente_neg = -math.tan(math.radians(ang_apant))
        pendiente_pos = math.tan(math.radians(ang_apant))
        
        # Encontrar recta con mayor distancia al origen
        dist_max = 0
        x_opt = 0
        z_opt = 0
        
        for nombre, x_c, y_c, z_c in conductores:
            if x_c > 0:
                # Recta: z = z_c + pendiente_neg * (x - x_c)
                # En x=0: z_intercept = z_c - pendiente_neg * x_c
                z_intercept = z_c - pendiente_neg * x_c
                dist = abs(z_intercept)
                if dist > dist_max:
                    dist_max = dist
                    # Calcular punto en recta a distancia lmenhg_min
                    x_opt = lmenhg_min
                    z_opt = z_c + pendiente_neg * (x_opt - x_c)
            elif x_c < 0:
                # Recta: z = z_c + pendiente_pos * (x - x_c)
                z_intercept = z_c - pendiente_pos * x_c
                dist = abs(z_intercept)
                if dist > dist_max:
                    dist_max = dist
                    x_opt = -lmenhg_min
                    z_opt = z_c + pendiente_pos * (x_opt - x_c)
        
        # Iterar para evitar zonas Dhg
        lmenhg, hhg = self._iterar_posicion_guardia(x_opt, z_opt, lmenhg_min, hadd_hg, conductores)
        
        # Crear nodo HG1 PRIMERO
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (lmenhg, defasaje_y, hhg), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # Crear nodo TOP DESPUÉS y verificar solapamiento
        pos_top = (0.0, 0.0, hhg + hadd_hg)
        pos_hg1 = (lmenhg, defasaje_y, hhg)
        dist = math.sqrt(sum((a - b)**2 for a, b in zip(pos_top, pos_hg1)))
        
        if dist >= 0.01:
            self.geo.nodos["TOP"] = NodoEstructural("TOP", pos_top, "general")
            print(f"   🔵 Nodo TOP creado en (0, 0, {hhg + hadd_hg:.2f})")
        else:
            print(f"   ⚠️  Nodo TOP no creado (solapamiento con HG1, dist={dist:.4f}m < 0.01m)")
        
        self.geo.dimensiones["hhg"] = hhg
        self.geo.dimensiones["lmenhg"] = lmenhg
        
        print(f"   🛡️  Guardia no centrado: HG1 en ({lmenhg:.2f}, {defasaje_y}, {hhg:.2f})")
    
    def _crear_dos_guardias(self, conductores, ang_apant, hadd_hg, lmenhg_min, defasaje_y):
        """CANT_HG=2"""
        # Considerar solo conductores con x>0
        conductores_der = [c for c in conductores if c[1] > 0]
        
        if not conductores_der:
            print("   ⚠️  No hay conductores en x>0, usando todos")
            conductores_der = conductores
        
        # Calcular recta de apantallamiento (pendiente negativa)
        pendiente = -math.tan(math.radians(ang_apant))
        
        dist_max = 0
        x_opt = 0
        z_opt = 0
        
        for nombre, x_c, y_c, z_c in conductores_der:
            # Recta: z = z_c + pendiente * (x - x_c)
            z_intercept = z_c - pendiente * x_c
            dist = abs(z_intercept)
            if dist > dist_max:
                dist_max = dist
                x_opt = lmenhg_min
                z_opt = z_c + pendiente * (x_opt - x_c)
        
        # Iterar para evitar zonas Dhg
        lmenhg, hhg = self._iterar_posicion_guardia(x_opt, z_opt, lmenhg_min, hadd_hg, conductores)
        
        # Crear nodos HG1 y HG2 PRIMERO
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (lmenhg, defasaje_y, hhg), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        cable_hg2 = self.geo.cable_guardia2 if self.geo.cable_guardia2 else self.geo.cable_guardia1
        self.geo.nodos["HG2"] = NodoEstructural(
            "HG2", (-lmenhg, defasaje_y, hhg + hadd_hg), "guardia",
            cable_hg2, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # Crear nodos TOP1 y TOP2 DESPUÉS y verificar solapamiento
        pos_top1 = (lmenhg, 0.0, hhg + hadd_hg)
        pos_hg1 = (lmenhg, defasaje_y, hhg)
        dist1 = math.sqrt(sum((a - b)**2 for a, b in zip(pos_top1, pos_hg1)))
        
        if dist1 >= 0.01:
            self.geo.nodos["TOP1"] = NodoEstructural("TOP1", pos_top1, "general")
            print(f"   🔵 Nodo TOP1 creado en ({lmenhg:.2f}, 0, {hhg + hadd_hg:.2f})")
        else:
            print(f"   ⚠️  Nodo TOP1 no creado (solapamiento con HG1, dist={dist1:.4f}m < 0.01m)")
        
        pos_top2 = (-lmenhg, 0.0, hhg + hadd_hg)
        pos_hg2 = (-lmenhg, defasaje_y, hhg + hadd_hg)
        dist2 = math.sqrt(sum((a - b)**2 for a, b in zip(pos_top2, pos_hg2)))
        
        if dist2 >= 0.01:
            self.geo.nodos["TOP2"] = NodoEstructural("TOP2", pos_top2, "general")
            print(f"   🔵 Nodo TOP2 creado en ({-lmenhg:.2f}, 0, {hhg + hadd_hg:.2f})")
        else:
            print(f"   ⚠️  Nodo TOP2 no creado (solapamiento con HG2, dist={dist2:.4f}m < 0.01m)")
        
        self.geo.dimensiones["hhg"] = hhg
        self.geo.dimensiones["lmenhg"] = lmenhg
        
        print(f"   🛡️  Dos guardias: HG1 en ({lmenhg:.2f}, {defasaje_y}, {hhg:.2f}), HG2 en ({-lmenhg:.2f}, {defasaje_y}, {hhg + hadd_hg:.2f})")
    
    def _iterar_posicion_guardia(self, x_inicial, z_inicial, lmenhg_min, hadd_hg, conductores):
        """Iterar para encontrar posición que no infrinja zonas Dhg"""
        # Altura inicial
        h_max = max(self.geo.dimensiones.get("h1a", 0), 
                   self.geo.dimensiones.get("h2a", 0),
                   self.geo.dimensiones.get("h3a", 0))
        
        z_inicial = max(z_inicial, h_max + hadd_hg)
        
        # Parámetros
        Dhg = self.geo.dimensiones.get("Dhg", 0)
        Lk = self.geo.lk
        
        # Iterar en altura
        lmenhg = max(abs(x_inicial), lmenhg_min)
        hhg = z_inicial
        max_iter = 100
        incremento = 0.1
        
        for i in range(max_iter):
            # Verificar distancia a todos los conductores (EN REPOSO, sin declinar)
            infraccion = False
            for nombre, x_c, y_c, z_c in conductores:
                # Distancia 3D entre guardia y conductor
                dist = math.sqrt((lmenhg - x_c)**2 + (hhg - z_c)**2)
                
                if dist < Dhg:
                    infraccion = True
                    break
            
            if not infraccion:
                break
            
            hhg += incremento
        
        return lmenhg, hhg
    

    

    
    def _crear_nodo_viento(self):
        """Crear nodo VIENTO en z=2/3*max(z_todos)"""
        z_max = max(nodo.coordenadas[2] for nodo in self.geo.nodos.values())
        z_viento = (2/3) * z_max
        
        self.geo.nodos["V"] = NodoEstructural("V", (0.0, 0.0, z_viento), "viento")
        print(f"   🌬️  Nodo VIENTO creado en (0, 0, {z_viento:.2f})")
    
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
