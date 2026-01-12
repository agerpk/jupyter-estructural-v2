# EstructuraAEA_Geometria_Etapa5.py


class GeometriaEtapa5:
    """Etapa 5: Checkeo de Conexiones entre Nodos"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def ejecutar(self):
        print("🔧 ETAPA 5: Checkeo de Conexiones")
        
        # Verificar que existan conexiones
        if not hasattr(self.geo, 'conexiones') or not self.geo.conexiones:
            print("   ⚠️  WARNING: No hay conexiones generadas")
            return
        
        # 1. Verificar conexiones duplicadas
        self._verificar_duplicados()
        
        # 2. Verificar conexiones a nodos inexistentes
        self._verificar_nodos_inexistentes()
        
        # 3. Verificar que no haya conexiones que "pasen por encima"
        self._verificar_conexiones_intermedias()
        
        # 4. Listar resumen de conexiones
        self._listar_resumen_conexiones()
        
        print(f"   ✅ Checkeo de conexiones completado: {len(self.geo.conexiones)} conexiones verificadas")
    
    def _verificar_duplicados(self):
        """Verificar que no haya conexiones duplicadas"""
        conexiones_set = set()
        duplicados = []
        
        for origen, destino, tipo in self.geo.conexiones:
            # Normalizar (orden alfabético para detectar duplicados bidireccionales)
            conexion_norm = tuple(sorted([origen, destino]) + [tipo])
            
            if conexion_norm in conexiones_set:
                duplicados.append((origen, destino, tipo))
            else:
                conexiones_set.add(conexion_norm)
        
        if duplicados:
            print(f"   ⚠️  WARNING: {len(duplicados)} conexiones duplicadas encontradas:")
            for origen, destino, tipo in duplicados:
                print(f"      {origen} → {destino} ({tipo})")
    
    def _verificar_nodos_inexistentes(self):
        """Verificar que todas las conexiones apunten a nodos existentes"""
        errores = []
        
        for origen, destino, tipo in self.geo.conexiones:
            if origen not in self.geo.nodos:
                errores.append(f"Nodo origen '{origen}' no existe")
            if destino not in self.geo.nodos:
                errores.append(f"Nodo destino '{destino}' no existe")
        
        if errores:
            print(f"   ❌ ERROR: {len(errores)} conexiones a nodos inexistentes:")
            for error in errores:
                print(f"      {error}")
    
    def _verificar_conexiones_intermedias(self):
        """Verificar que no haya conexiones que pasen por encima de otros nodos"""
        advertencias = []
        tol_z = 1e-3
        
        for origen, destino, tipo in self.geo.conexiones:
            if origen not in self.geo.nodos or destino not in self.geo.nodos:
                continue
            
            nodo_origen = self.geo.nodos[origen]
            nodo_destino = self.geo.nodos[destino]
            
            x1, y1, z1 = nodo_origen.coordenadas
            x2, y2, z2 = nodo_destino.coordenadas
            
            # Verificar si hay nodos intermedios
            if tipo == "mensula":
                # Mensula: verificar nodos en misma altura entre x1 y x2
                for nombre, nodo in self.geo.nodos.items():
                    if nombre in [origen, destino]:
                        continue
                    
                    x, y, z = nodo.coordenadas
                    
                    # Mismo nivel vertical
                    if abs(z - z1) < tol_z and abs(z - z2) < tol_z:
                        # Entre x1 y x2
                        if min(x1, x2) < x < max(x1, x2):
                            advertencias.append(
                                f"Conexión {origen}-{destino} (mensula) pasa por encima de {nombre}"
                            )
            
            elif tipo == "columna":
                # Columna: verificar nodos en misma x entre z1 y z2
                for nombre, nodo in self.geo.nodos.items():
                    if nombre in [origen, destino]:
                        continue
                    
                    x, y, z = nodo.coordenadas
                    
                    # Misma posición horizontal
                    if abs(x - x1) < tol_z and abs(x - x2) < tol_z:
                        # Entre z1 y z2
                        if min(z1, z2) < z < max(z1, z2):
                            advertencias.append(
                                f"Conexión {origen}-{destino} (columna) pasa por encima de {nombre}"
                            )
        
        if advertencias:
            print(f"   ⚠️  WARNING: {len(advertencias)} conexiones que pasan por encima de nodos:")
            for adv in advertencias:
                print(f"      {adv}")
    
    def _listar_resumen_conexiones(self):
        """Listar resumen de conexiones por tipo"""
        columnas = [c for c in self.geo.conexiones if c[2] == "columna"]
        mensulas = [c for c in self.geo.conexiones if c[2] == "mensula"]
        
        print(f"   📊 Resumen: {len(columnas)} columnas, {len(mensulas)} ménsulas")
