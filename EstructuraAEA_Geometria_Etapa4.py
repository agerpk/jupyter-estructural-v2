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
        
        # Crear nodo TOP SIEMPRE en x=0, y=0, z=hhg_final
        self.geo.nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg_final), "general")
        print(f"   🔵 Nodo TOP creado en (0, 0, {hhg_final:.2f})")
        
        # Crear nodo HG1
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (0.0, defasaje_y, hhg_final), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # Eliminar TOP si coincide con HG1
        if abs(defasaje_y) < 0.01:
            del self.geo.nodos["TOP"]
            print(f"   ⚠️  Nodo TOP eliminado (coincide con HG1)")
        
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
        
        # Verificar apantallamiento de C2 (lado izquierdo) y ajustar si es necesario
        lmenhg, hhg = self._ajustar_apantallamiento_c2(
            lmenhg, hhg, conductores, pendiente_pos, ang_apant
        )
        
        # Altura final de nodos HG
        hhg_final = hhg + hadd_hg
        
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        
        # Crear nodo TOP SIEMPRE en x=0, y=0, z=hhg_final
        self.geo.nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg_final), "general")
        print(f"   🔵 Nodo TOP creado en (0, 0, {hhg_final:.2f})")
        
        # Crear nodo TOP1 en x=lmenhg, y=0, z=hhg_final
        self.geo.nodos["TOP1"] = NodoEstructural("TOP1", (lmenhg, 0.0, hhg_final), "general")
        print(f"   🔵 Nodo TOP1 creado en ({lmenhg:.2f}, 0, {hhg_final:.2f})")
        
        # Crear nodo HG1
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (lmenhg, defasaje_y, hhg_final), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # Eliminar TOP1 si coincide con HG1
        dist = math.sqrt((lmenhg - lmenhg)**2 + (0.0 - defasaje_y)**2 + (hhg_final - hhg_final)**2)
        if dist < 0.01:
            del self.geo.nodos["TOP1"]
            print(f"   ⚠️  Nodo TOP1 eliminado (coincide con HG1)")
        
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
        
        # Altura inicial: z más alto de estructura preexistente + hadd_hg
        h_max = max(self.geo.dimensiones.get("h1a", 0), 
                   self.geo.dimensiones.get("h2a", 0),
                   self.geo.dimensiones.get("h3a", 0))
        
        # Iterar para encontrar lmenhg y hhg que cumplan Dhg y apantallamiento
        # hhg_inicial ya incluye hadd_hg
        lmenhg, hhg = self._iterar_guardia_dhg_apantallamiento(
            lmenhg_min, h_max + hadd_hg, conductores, pendiente, ang_apant
        )
        
        # Altura final de nodos HG (ya incluye hadd_hg desde la iteración)
        hhg_final = hhg
        
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        
        # Crear nodo TOP SIEMPRE en x=0, y=0, z=hhg_final
        self.geo.nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg_final), "general")
        print(f"   🔵 Nodo TOP creado en (0, 0, {hhg_final:.2f})")
        
        # Crear nodo TOP1 en x=lmenhg, y=0, z=hhg_final
        self.geo.nodos["TOP1"] = NodoEstructural("TOP1", (lmenhg, 0.0, hhg_final), "general")
        print(f"   🔵 Nodo TOP1 creado en ({lmenhg:.2f}, 0, {hhg_final:.2f})")
        
        # Crear nodo TOP2 en x=-lmenhg, y=0, z=hhg_final
        self.geo.nodos["TOP2"] = NodoEstructural("TOP2", (-lmenhg, 0.0, hhg_final), "general")
        print(f"   🔵 Nodo TOP2 creado en ({-lmenhg:.2f}, 0, {hhg_final:.2f})")
        
        # Crear nodos HG1 y HG2
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (lmenhg, defasaje_y, hhg_final), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        cable_hg2 = self.geo.cable_guardia2 if self.geo.cable_guardia2 else self.geo.cable_guardia1
        self.geo.nodos["HG2"] = NodoEstructural(
            "HG2", (-lmenhg, defasaje_y, hhg_final), "guardia",
            cable_hg2, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # Eliminar TOP1 si coincide con HG1
        dist1 = math.sqrt((lmenhg - lmenhg)**2 + (0.0 - defasaje_y)**2 + (hhg_final - hhg_final)**2)
        if dist1 < 0.01:
            del self.geo.nodos["TOP1"]
            print(f"   ⚠️  Nodo TOP1 eliminado (coincide con HG1)")
        
        # Eliminar TOP2 si coincide con HG2
        dist2 = math.sqrt((-lmenhg - (-lmenhg))**2 + (0.0 - defasaje_y)**2 + (hhg_final - hhg_final)**2)
        if dist2 < 0.01:
            del self.geo.nodos["TOP2"]
            print(f"   ⚠️  Nodo TOP2 eliminado (coincide con HG2)")
        
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
    
    def _ajustar_apantallamiento_c2(self, lmenhg_inicial, hhg_inicial, conductores, pendiente_pos, ang_apant):
        """Ajustar hhg y lmenhg para apantallar conductor C2 (lado izquierdo, x<0)
        
        Verifica que la línea de apantallamiento desde HG1 con pendiente positiva
        cubra el conductor C2. Si no lo cubre:
        1. Sube hhg en 0.01m
        2. Verifica si C3 (conductor más alto) sigue apantallado
        3. Si C3 sigue apantallado, reduce lmenhg en 0.01m
        4. Repite hasta que C2 quede apantallado
        """
        # Identificar conductores C2 (x<0) y C3 (conductor más alto)
        Lk = self.geo.lk
        c2_conductor = None
        c3_conductor = None
        
        # Buscar C2 (lado izquierdo, x<0)
        for nombre, x_c, y_c, z_c in conductores:
            if x_c < 0:
                c2_conductor = (nombre, x_c, y_c, z_c)
                break
        
        # Buscar C3 (conductor más alto)
        z_max = max(c[3] for c in conductores)
        for nombre, x_c, y_c, z_c in conductores:
            if abs(z_c - z_max) < 0.01:
                c3_conductor = (nombre, x_c, y_c, z_c)
                break
        
        if not c2_conductor:
            print(f"   ℹ️  No hay conductor C2 (x<0), no se requiere ajuste")
            return lmenhg_inicial, hhg_inicial
        
        lmenhg = lmenhg_inicial
        hhg = hhg_inicial
        incremento = 0.01
        max_iter = 10000
        
        nombre_c2, x_c2, y_c2, z_c2 = c2_conductor
        
        for i in range(max_iter):
            # Verificar apantallamiento de C2
            # Línea desde HG1 (lmenhg, hhg) con pendiente positiva
            # z_recta = hhg + pendiente_pos * (x_c2 - lmenhg)
            z_recta_c2 = hhg + pendiente_pos * (x_c2 - lmenhg)
            
            if z_c2 <= z_recta_c2:
                # C2 está apantallado
                if i > 0:
                    print(f"   ✅ C2 apantallado después de {i} iteraciones: lmenhg={lmenhg:.3f}m, hhg={hhg:.3f}m")
                break
            
            # C2 no está apantallado, subir hhg
            hhg += incremento
            
            # Verificar si C3 sigue apantallado con el nuevo hhg
            if c3_conductor:
                nombre_c3, x_c3, y_c3, z_c3 = c3_conductor
                # Pendiente negativa para x>0
                pendiente_neg = -1.0 / math.tan(math.radians(ang_apant))
                z_recta_c3 = hhg + pendiente_neg * (x_c3 - lmenhg)
                
                if z_c3 <= z_recta_c3:
                    # C3 sigue apantallado, reducir lmenhg
                    lmenhg -= incremento
                    # Asegurar que no baje del mínimo
                    lmenhg = max(lmenhg, self.geo.long_mensula_min_guardia)
        
        if i == max_iter - 1:
            print(f"   ⚠️  Límite de iteraciones alcanzado ajustando C2")
        
        # Asegurar mínimos
        lmenhg = max(lmenhg, self.geo.long_mensula_min_guardia)
        hhg = max(hhg, self.geo.hadd_hg)
        
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
        
        # Encontrar CROSS_H* más alto
        cross_mas_alto = None
        z_max_cross = -float('inf')
        for nombre, nodo in self.geo.nodos.items():
            if 'CROSS_H' in nombre:
                z = nodo.coordenadas[2]
                if z > z_max_cross:
                    z_max_cross = z
                    cross_mas_alto = nombre
        
        # Encontrar nodo en x=0, y=0 a altura hhg_final (TOP o HG1)
        hhg_final = self.geo.dimensiones.get("hhg", 0)
        nodo_central = None
        for nombre, nodo in self.geo.nodos.items():
            x, y, z = nodo.coordenadas
            if abs(x) < 0.01 and abs(y) < 0.01 and abs(z - hhg_final) < 0.01:
                nodo_central = nombre
                break
        
        # Conectar CROSS_H* más alto al nodo central con tipo "columna"
        if cross_mas_alto and nodo_central:
            self.geo.conexiones.append((cross_mas_alto, nodo_central, 'columna'))
            print(f"      🔗 {cross_mas_alto} → {nodo_central} (columna)")
            
            # Conectar otros nodos a altura hhg_final al nodo central con tipo "mensula"
            for nombre, nodo in self.geo.nodos.items():
                x, y, z = nodo.coordenadas
                if abs(z - hhg_final) < 0.01 and nombre != nodo_central and nombre != cross_mas_alto:
                    if not (nombre.startswith('HG') or nombre.startswith('TOP')):
                        continue
                    self.geo.conexiones.append((nodo_central, nombre, 'mensula'))
                    print(f"      🔗 {nodo_central} → {nombre} (mensula)")
        
        # Ejecutar generador de conexiones estándar
        conexiones_anteriores = set(self.geo.conexiones)
        self.geo._generar_conexiones()
        
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        if conexiones_nuevas:
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      INFO: {origen} → {destino} ({tipo})")
