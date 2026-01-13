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
        
        print(f"   ✅ Cable guardia configurado: hhg={self.geo.dimensiones.get('hhg', 0):.2f}m, lmenhg={self.geo.dimensiones.get('lmenhg', 0):.2f}m")
    
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
        
        # Altura final de nodos HG
        hhg_final = hhg + hadd_hg
        
        # Obtener defasaje_y_guardia del objeto geometria
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        
        # Crear nodo HG1
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (0.0, defasaje_y, hhg_final), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        self.geo.dimensiones["hhg"] = hhg_final
        self.geo.dimensiones["lmenhg"] = 0.0
        
        print(f"   🛡️  Guardia centrado: HG1 en (0, {defasaje_y}, {hhg_final:.2f})")
    
    def _crear_guardia_no_centrado(self, conductores, ang_apant, hadd_hg, lmenhg_min, defasaje_y):
        """CANT_HG=1, HG_CENTRADO=False - Solo para disposición triangular terna simple"""
        # Validar que solo aplica para triangular simple
        if not (self.geo.disposicion == "triangular" and self.geo.terna == "Simple"):
            print(f"   ⚠️  Guardia no centrado solo aplica para triangular simple, usando centrado")
            self._crear_guardia_centrado(conductores, ang_apant, hadd_hg, defasaje_y)
            return
        
        # Calcular recta de apantallamiento para cada conductor
        # Pendiente: ang_apant es respecto a la VERTICAL, convertir a pendiente respecto a horizontal
        # Para x>0: pendiente negativa (recta baja hacia derecha)
        # Para x<0: pendiente positiva (recta baja hacia izquierda)
        pendiente_neg = -1.0 / math.tan(math.radians(ang_apant))
        pendiente_pos = 1.0 / math.tan(math.radians(ang_apant))
        
        # Altura inicial: z más alto de estructura preexistente
        h_max = max(self.geo.dimensiones.get("h1a", 0), 
                   self.geo.dimensiones.get("h2a", 0),
                   self.geo.dimensiones.get("h3a", 0))
        
        # Iterar para encontrar lmenhg y hhg que cumplan Dhg y apantallamiento
        # Usar pendiente negativa (para x>0)
        lmenhg, hhg = self._iterar_guardia_dhg_apantallamiento(
            lmenhg_min, h_max, conductores, pendiente_neg, ang_apant
        )
        
        # Altura final de nodos HG
        hhg_final = hhg + hadd_hg
        
        # Crear nodo HG1 PRIMERO
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (lmenhg, defasaje_y, hhg_final), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # Crear nodo TOP DESPUÉS y verificar solapamiento
        pos_top = (0.0, 0.0, hhg_final)
        pos_hg1 = (lmenhg, defasaje_y, hhg_final)
        dist = math.sqrt(sum((a - b)**2 for a, b in zip(pos_top, pos_hg1)))
        
        if dist >= 0.01:
            self.geo.nodos["TOP"] = NodoEstructural("TOP", pos_top, "general")
            print(f"   🔵 Nodo TOP creado en (0, 0, {hhg_final:.2f})")
        else:
            print(f"   ⚠️  Nodo TOP no creado (solapamiento con HG1, dist={dist:.4f}m < 0.01m)")
        
        self.geo.dimensiones["hhg"] = hhg_final
        self.geo.dimensiones["lmenhg"] = lmenhg
        
        print(f"   🛡️  Guardia no centrado: HG1 en ({lmenhg:.2f}, {defasaje_y}, {hhg_final:.2f})")
    
    def _crear_dos_guardias(self, conductores, ang_apant, hadd_hg, lmenhg_min, defasaje_y):
        """CANT_HG=2"""
        # Considerar solo conductores con x>0
        conductores_der = [c for c in conductores if c[1] > 0]
        
        if not conductores_der:
            print("   ⚠️  No hay conductores en x>0, usando todos")
            conductores_der = conductores
        
        # Calcular recta de apantallamiento (pendiente negativa)
        # ang_apant es respecto a la VERTICAL, convertir a pendiente respecto a horizontal
        pendiente = -1.0 / math.tan(math.radians(ang_apant))
        
        # Altura inicial: z más alto de estructura preexistente
        h_max = max(self.geo.dimensiones.get("h1a", 0), 
                   self.geo.dimensiones.get("h2a", 0),
                   self.geo.dimensiones.get("h3a", 0))
        
        # Iterar para encontrar lmenhg y hhg que cumplan Dhg y apantallamiento
        lmenhg, hhg = self._iterar_guardia_dhg_apantallamiento(
            lmenhg_min, h_max, conductores, pendiente, ang_apant
        )
        
        # Altura final de nodos HG
        hhg_final = hhg + hadd_hg
        
        # Crear nodos HG1 y HG2 PRIMERO
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (lmenhg, defasaje_y, hhg_final), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        cable_hg2 = self.geo.cable_guardia2 if self.geo.cable_guardia2 else self.geo.cable_guardia1
        self.geo.nodos["HG2"] = NodoEstructural(
            "HG2", (-lmenhg, defasaje_y, hhg_final), "guardia",
            cable_hg2, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # Crear nodos TOP1 y TOP2 DESPUÉS y verificar solapamiento
        pos_top1 = (lmenhg, 0.0, hhg_final)
        pos_top2 = (-lmenhg, 0.0, hhg_final)
        pos_hg1 = (lmenhg, defasaje_y, hhg_final)
        pos_hg2 = (-lmenhg, defasaje_y, hhg_final)
        
        dist1 = math.sqrt(sum((a - b)**2 for a, b in zip(pos_top1, pos_hg1)))
        dist2 = math.sqrt(sum((a - b)**2 for a, b in zip(pos_top2, pos_hg2)))
        
        if dist1 >= 0.01:
            self.geo.nodos["TOP1"] = NodoEstructural("TOP1", pos_top1, "general")
            print(f"   🔵 Nodo TOP1 creado en ({lmenhg:.2f}, 0, {hhg_final:.2f})")
        else:
            print(f"   ⚠️  Nodo TOP1 no creado (solapamiento con HG1, dist={dist1:.4f}m < 0.01m)")
        
        if dist2 >= 0.01:
            self.geo.nodos["TOP2"] = NodoEstructural("TOP2", pos_top2, "general")
            print(f"   🔵 Nodo TOP2 creado en ({-lmenhg:.2f}, 0, {hhg_final:.2f})")
        else:
            print(f"   ⚠️  Nodo TOP2 no creado (solapamiento con HG2, dist={dist2:.4f}m < 0.01m)")
        
        self.geo.dimensiones["hhg"] = hhg_final
        self.geo.dimensiones["lmenhg"] = lmenhg
        
        print(f"   🛡️  Dos guardias: HG1 en ({lmenhg:.2f}, {defasaje_y}, {hhg_final:.2f}), HG2 en ({-lmenhg:.2f}, {defasaje_y}, {hhg_final:.2f})")
    
    def _iterar_posicion_guardia_simple(self, x_inicial, z_inicial, lmenhg_min, hadd_hg, conductores):
        """Iterar para encontrar posición que no infrinja zonas Dhg (solo sube hhg)"""
        h_max = max(self.geo.dimensiones.get("h1a", 0), 
                   self.geo.dimensiones.get("h2a", 0),
                   self.geo.dimensiones.get("h3a", 0))
        
        z_inicial = max(z_inicial, h_max + hadd_hg)
        
        Dhg = self.geo.dimensiones.get("Dhg", 0)
        
        lmenhg = max(abs(x_inicial), lmenhg_min)
        hhg = z_inicial
        max_iter = 10000
        incremento = 0.01
        
        for i in range(max_iter):
            infraccion = False
            for nombre, x_c, y_c, z_c in conductores:
                dist = math.sqrt((lmenhg - x_c)**2 + (hhg - z_c)**2)
                if dist < Dhg:
                    infraccion = True
                    break
            
            if not infraccion:
                break
            
            hhg += incremento
        
        return lmenhg, hhg
    
    def _iterar_guardia_dhg_apantallamiento(self, lmenhg_inicial, hhg_inicial, conductores, pendiente, ang_apant):
        """Iterar para encontrar lmenhg y hhg que cumplan Dhg y apantallamiento
        
        - Si infringe solo Dhg: sube hhg
        - Si infringe solo apantallamiento: aumenta lmenhg
        - Si infringe ambos: aumenta ambos
        """
        Dhg = self.geo.dimensiones.get("Dhg", 0)
        
        lmenhg = lmenhg_inicial
        hhg = hhg_inicial
        max_iter = 10000
        incremento = 0.01
        
        for i in range(max_iter):
            # Verificar Dhg: distancia entre guardia y conductores
            infringe_dhg = False
            for nombre, x_c, y_c, z_c in conductores:
                dist = math.sqrt((lmenhg - x_c)**2 + (hhg - z_c)**2)
                if dist < Dhg:
                    infringe_dhg = True
                    break
            
            # Verificar apantallamiento: todos los conductores bajo la recta
            infringe_apant = False
            for nombre, x_c, y_c, z_c in conductores:
                # Recta de apantallamiento desde (lmenhg, hhg) con pendiente
                # z_recta = hhg + pendiente * (x_c - lmenhg)
                z_recta = hhg + pendiente * (x_c - lmenhg)
                if z_c > z_recta:
                    infringe_apant = True
                    break
            
            # Decidir qué incrementar
            if not infringe_dhg and not infringe_apant:
                break
            elif infringe_dhg and infringe_apant:
                hhg += incremento
                lmenhg += incremento
            elif infringe_dhg:
                hhg += incremento
            elif infringe_apant:
                lmenhg += incremento
        
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
