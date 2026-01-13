# EstructuraAEA_Geometria_Etapa6.py
import math
from utils.geometria_zonas import Nodo, crear_verificador_desde_nodos


class GeometriaEtapa6:
    """Etapa 6: Checkeos Finales"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def ejecutar(self):
        print("🔧 ETAPA 6: Checkeos Finales")
        
        errores = []
        advertencias = []
        
        # 1. Checkear zonas de prohibición
        errores_zonas = self._checkear_zonas_prohibicion()
        errores.extend(errores_zonas)
        
        # 2. Checkear apantallamiento
        errores_apant = self._checkear_apantallamiento()
        errores.extend(errores_apant)
        
        # 3. Checkear conexiones
        errores_conex = self._checkear_conexiones()
        errores.extend(errores_conex)
        
        # 4. Checkear sub-optimización
        adv_subopt = self._checkear_suboptimizacion()
        advertencias.extend(adv_subopt)
        
        # Imprimir resultados
        if errores:
            print(f"   ❌ {len(errores)} ERRORES encontrados:")
            for error in errores:
                print(f"      ERROR: {error}")
        
        if advertencias:
            print(f"   ⚠️  {len(advertencias)} ADVERTENCIAS:")
            for adv in advertencias:
                print(f"      ADVERTENCIA: {adv}")
        
        if not errores and not advertencias:
            print("   ✅ Todos los checkeos pasaron correctamente")
        
        print(f"   ✅ Checkeos finales completados")
    
    def _checkear_apantallamiento(self):
        """Verificar que todos los conductores estén bajo apantallamiento"""
        errores = []
        
        if self.geo.cant_hg == 0:
            return errores
        
        # Obtener guardias
        guardias = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "guardia"]
        
        if not guardias:
            errores.append("No hay nodos guardia pero CANT_HG > 0")
            return errores
        
        # Obtener conductores
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        Lk = self.geo.lk
        ang_apant = self.geo.ang_apantallamiento
        
        for nombre_c, nodo_c in conductores:
            x_c, y_c, z_amarre_c = nodo_c.coordenadas
            z_conductor = z_amarre_c - Lk
            
            # Verificar si está cubierto por algún guardia
            cubierto = False
            dist_fuera_min = float('inf')
            
            for nombre_g, nodo_g in guardias:
                x_g, y_g, z_g = nodo_g.coordenadas
                
                # Distancia horizontal
                dist_horizontal = math.sqrt((x_c - x_g)**2 + (y_c - y_g)**2)
                
                # Altura de apantallamiento en posición del conductor
                z_apant = z_g - dist_horizontal * math.tan(math.radians(ang_apant))
                
                if z_conductor <= z_apant:
                    cubierto = True
                    break
                else:
                    dist_fuera = z_conductor - z_apant
                    dist_fuera_min = min(dist_fuera_min, dist_fuera)
            
            if not cubierto:
                errores.append(
                    f"Conductor {nombre_c} fuera de apantallamiento: {dist_fuera_min:.3f}m"
                )
        
        return errores
    
    def _checkear_conexiones(self):
        """Verificar que conexiones estén correctamente definidas"""
        errores = []
        
        if not hasattr(self.geo, 'conexiones') or not self.geo.conexiones:
            errores.append("No hay conexiones generadas")
            return errores
        
        # 1. Verificar duplicados
        conexiones_set = set()
        for origen, destino, tipo in self.geo.conexiones:
            conexion_norm = tuple(sorted([origen, destino]) + [tipo])
            if conexion_norm in conexiones_set:
                errores.append(f"Conexión duplicada: {origen}-{destino} ({tipo})")
            else:
                conexiones_set.add(conexion_norm)
        
        # 2. Verificar nodos inexistentes
        for origen, destino, tipo in self.geo.conexiones:
            if origen not in self.geo.nodos:
                errores.append(f"Nodo origen '{origen}' no existe en conexión {origen}-{destino}")
            if destino not in self.geo.nodos:
                errores.append(f"Nodo destino '{destino}' no existe en conexión {origen}-{destino}")
        
        if errores:
            print(f"   ❌ {len(errores)} errores en conexiones")
        else:
            print("   ✅ Todas las conexiones son válidas")
        
        return errores
    
    def _checkear_suboptimizacion(self):
        """Verificar que no haya nodos a mayor altura de la necesaria"""
        advertencias = []
        
        # Obtener theta_max y theta_tormenta
        vano = self.geo.dimensiones.get('vano', 400)
        theta_max = self.geo.calcular_theta_max(vano)
        if theta_max >= 99.0:
            theta_max = 0.0
        theta_tormenta = theta_max / 2.0
        
        # Parámetros
        Lk = self.geo.lk
        D_fases = self.geo.dimensiones.get('D_fases', 0)
        s_reposo = self.geo.dimensiones.get('s_reposo', 0)
        s_decmax = self.geo.dimensiones.get('s_decmax', s_reposo)
        s_tormenta = self.geo.dimensiones.get('s_tormenta', s_reposo)
        
        # Verificar cada conductor
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        for nombre, nodo in conductores:
            x, y, z_amarre = nodo.coordenadas
            
            # Construir estructura temporal sin este conductor
            nodos_temp = {}
            for n, nd in self.geo.nodos.items():
                if n == nombre:
                    continue
                if nd.tipo_nodo in ["base", "cruce", "conductor", "guardia"]:
                    nodos_temp[n] = Nodo(n, nd.coordenadas[0], nd.coordenadas[1], nd.coordenadas[2], nd.tipo_nodo)
            
            # Agregar conexiones (simplificado)
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
                'h_cross_h1': self.geo.dimensiones.get('h1a', 0)
            }
            
            # Buscar altura mínima posible
            verificador = crear_verificador_desde_nodos(nodos_temp, parametros)
            z_minima, razon = verificador.buscar_altura_minima(x)
            
            # Comparar con altura actual
            margen = 0.5  # 50cm de margen
            if z_amarre > z_minima + margen:
                ahorro = z_amarre - z_minima
                advertencias.append(
                    f"Nodo {nombre} podría estar {ahorro:.2f}m más bajo (z_actual={z_amarre:.2f}m, z_min={z_minima:.2f}m)"
                )
        
        return advertencias
    
    def _checkear_zonas_prohibicion(self):
        """Verificar infracciones de zonas de prohibición"""
        errores = []
        
        # Obtener parámetros
        Lk = self.geo.lk
        s_reposo = self.geo.dimensiones.get('s_reposo', 0)
        s_tormenta = self.geo.dimensiones.get('s_tormenta', s_reposo)
        s_decmax = self.geo.dimensiones.get('s_decmax', s_tormenta)
        D_fases = self.geo.dimensiones.get('D_fases', 0)
        Dhg = self.geo.dimensiones.get('Dhg', 0)
        theta_max = self.geo.dimensiones.get('theta_max', 0)
        theta_tormenta = theta_max / 2.0 if theta_max < 99 else 0
        
        # Obtener conductores y elementos fijos
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        elementos_fijos = [(n, nodo) for n, nodo in self.geo.nodos.items() 
                          if nodo.tipo_nodo in ["base", "cruce", "general"]]
        
        # Verificar cada conductor contra elementos fijos
        for nombre_c, nodo_c in conductores:
            x_amarre, y_amarre, z_amarre = nodo_c.coordenadas
            
            # Posiciones del conductor (reposo, tormenta, decmax)
            import math
            posiciones = [
                (x_amarre, z_amarre - Lk, "reposo", s_reposo),
                (x_amarre + Lk * math.sin(math.radians(theta_tormenta)), 
                 z_amarre - Lk * math.cos(math.radians(theta_tormenta)), "tormenta", s_tormenta),
                (x_amarre + Lk * math.sin(math.radians(theta_max)), 
                 z_amarre - Lk * math.cos(math.radians(theta_max)), "decmax", s_decmax)
            ]
            
            for x_cond, z_cond, estado, s_min in posiciones:
                for nombre_fijo, nodo_fijo in elementos_fijos:
                    x_fijo, y_fijo, z_fijo = nodo_fijo.coordenadas
                    
                    # Distancia 2D en plano XZ
                    dist = math.sqrt((x_cond - x_fijo)**2 + (z_cond - z_fijo)**2)
                    
                    if dist < s_min:
                        infraccion = s_min - dist
                        errores.append(
                            f"Conductor {nombre_c} ({estado}) infringe zona s={s_min:.3f}m con {nombre_fijo}: dist={dist:.3f}m, infracción={infraccion:.3f}m"
                        )
        
        # Verificar D_fases entre conductores
        for i, (nombre_c1, nodo_c1) in enumerate(conductores):
            for nombre_c2, nodo_c2 in conductores[i+1:]:
                x1, y1, z1_amarre = nodo_c1.coordenadas
                x2, y2, z2_amarre = nodo_c2.coordenadas
                
                # Comparar en misma declinación
                z1_cond = z1_amarre - Lk
                z2_cond = z2_amarre - Lk
                
                dist = math.sqrt((x1 - x2)**2 + (z1_cond - z2_cond)**2)
                
                if dist < D_fases:
                    infraccion = D_fases - dist
                    errores.append(
                        f"Conductores {nombre_c1}-{nombre_c2} infringen D_fases={D_fases:.3f}m: dist={dist:.3f}m, infracción={infraccion:.3f}m"
                    )
        
        # Verificar Dhg entre conductores y guardias
        guardias = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "guardia"]
        
        for nombre_c, nodo_c in conductores:
            x_c, y_c, z_c_amarre = nodo_c.coordenadas
            z_c = z_c_amarre - Lk
            
            for nombre_g, nodo_g in guardias:
                x_g, y_g, z_g = nodo_g.coordenadas
                
                dist = math.sqrt((x_c - x_g)**2 + (z_c - z_g)**2)
                
                if dist < Dhg:
                    infraccion = Dhg - dist
                    errores.append(
                        f"Conductor {nombre_c} infringe Dhg={Dhg:.3f}m con guardia {nombre_g}: dist={dist:.3f}m, infracción={infraccion:.3f}m"
                    )
        
        if errores:
            print(f"   ❌ {len(errores)} infracciones de zonas de prohibición encontradas")
        else:
            print("   ✅ No hay infracciones de zonas de prohibición")
        
        return errores
