# utils/geometria_zonas.py
"""
Módulo de zonas prohibidas geométricas para DGE.

Recibe estructura de nodos con conexiones y genera zonas prohibidas automáticamente
basadas en tipos de conexión (columna, mensula) y tipos de nodo (conductor, guardia).
"""

import math
from typing import List, Tuple, Optional, Dict


class Nodo:
    """Nodo estructural con coordenadas y tipo"""
    
    def __init__(self, nombre: str, x: float, y: float, z: float, tipo: str):
        self.nombre = nombre
        self.x = x
        self.y = y
        self.z = z
        self.tipo = tipo  # "base", "cruce", "conductor", "guardia"
        self.conexiones = []  # Lista de (nodo_destino, tipo_conexion)
    
    def agregar_conexion(self, nodo_destino: 'Nodo', tipo_conexion: str):
        """Agregar conexión a otro nodo
        
        Args:
            nodo_destino: Nodo destino
            tipo_conexion: "columna" o "mensula"
        """
        self.conexiones.append((nodo_destino, tipo_conexion))


class ZonaProhibida:
    """Clase base para zonas prohibidas"""
    
    def __init__(self, descripcion: str, tipo_zona: str):
        self.descripcion = descripcion
        self.tipo_zona = tipo_zona  # "columna", "mensula", "d_fases", "dhg"
    
    def contiene_punto(self, x: float, z: float) -> bool:
        """Verificar si punto (x, z) está dentro de la zona prohibida"""
        raise NotImplementedError
    
    def distancia_a_punto(self, x: float, z: float) -> Tuple[float, float, float]:
        """Calcular distancias horizontal, vertical y mínima desde punto a zona
        
        Returns:
            (dist_horizontal, dist_vertical, dist_minima)
        """
        raise NotImplementedError


class FranjaVertical(ZonaProhibida):
    """Franja vertical (columna con defasaje s_decmax)"""
    
    def __init__(self, x_centro: float, z_min: float, z_max: float, ancho: float, descripcion: str = ""):
        super().__init__(descripcion or f"Columna x={x_centro:.2f}m", "columna")
        self.x_centro = x_centro
        self.x_min = x_centro - ancho / 2
        self.x_max = x_centro + ancho / 2
        self.z_min = z_min
        self.z_max = z_max
    
    def contiene_punto(self, x: float, z: float) -> bool:
        return (self.x_min <= x <= self.x_max and self.z_min <= z <= self.z_max)
    
    def distancia_a_punto(self, x: float, z: float) -> Tuple[float, float, float]:
        # Distancia horizontal
        if x < self.x_min:
            dx = self.x_min - x
        elif x > self.x_max:
            dx = x - self.x_max
        else:
            dx = 0
        
        # Distancia vertical
        if z < self.z_min:
            dz = self.z_min - z
        elif z > self.z_max:
            dz = z - self.z_max
        else:
            dz = 0
        
        # Distancia mínima
        dist_min = math.sqrt(dx**2 + dz**2)
        
        return (dx, dz, dist_min)


class FranjaHorizontal(ZonaProhibida):
    """Franja horizontal (mensula con defasaje s_reposo)"""
    
    def __init__(self, x_min: float, x_max: float, z_centro: float, altura: float, descripcion: str = ""):
        super().__init__(descripcion or f"Ménsula z={z_centro:.2f}m", "mensula")
        self.x_min = x_min
        self.x_max = x_max
        self.z_centro = z_centro
        self.z_min = z_centro
        self.z_max = z_centro + altura
    
    def contiene_punto(self, x: float, z: float) -> bool:
        return (self.x_min <= x <= self.x_max and self.z_min <= z <= self.z_max)
    
    def distancia_a_punto(self, x: float, z: float) -> Tuple[float, float, float]:
        # Distancia horizontal
        if x < self.x_min:
            dx = self.x_min - x
        elif x > self.x_max:
            dx = x - self.x_max
        else:
            dx = 0
        
        # Distancia vertical
        if z < self.z_min:
            dz = self.z_min - z
        elif z > self.z_max:
            dz = z - self.z_max
        else:
            dz = 0
        
        # Distancia mínima
        dist_min = math.sqrt(dx**2 + dz**2)
        
        return (dx, dz, dist_min)


class Circulo(ZonaProhibida):
    """Zona circular (D_fases, Dhg, s_reposo en nodos)"""
    
    def __init__(self, centro_x: float, centro_z: float, radio: float, tipo_zona: str, descripcion: str = ""):
        super().__init__(descripcion or f"Círculo r={radio:.2f}m", tipo_zona)
        self.centro_x = centro_x
        self.centro_z = centro_z
        self.radio = radio
    
    def contiene_punto(self, x: float, z: float) -> bool:
        dist = math.sqrt((x - self.centro_x)**2 + (z - self.centro_z)**2)
        return dist < self.radio
    
    def distancia_a_punto(self, x: float, z: float) -> Tuple[float, float, float]:
        dx = x - self.centro_x
        dz = z - self.centro_z
        dist = math.sqrt(dx**2 + dz**2)
        
        # Si está dentro, distancia es negativa
        if dist < self.radio:
            return (0, 0, self.radio - dist)
        
        # Si está fuera, calcular distancia al borde
        dist_borde = dist - self.radio
        
        # Componentes horizontal y vertical
        if dist > 0:
            dx_borde = abs(dx) * dist_borde / dist
            dz_borde = abs(dz) * dist_borde / dist
        else:
            dx_borde = 0
            dz_borde = 0
        
        return (dx_borde, dz_borde, dist_borde)


class GeneradorZonasProhibidas:
    """Generador de zonas prohibidas a partir de estructura de nodos"""
    
    def __init__(self, nodos: Dict[str, Nodo], parametros: dict):
        """
        Args:
            nodos: Diccionario {nombre: Nodo}
            parametros: {
                'Lk': float,
                'D_fases': float,
                's_reposo': float,
                's_decmax': float,
                's_tormenta': float,
                'Dhg': float,
                'theta_max': float,  # Ángulo declinación máxima (grados)
                'theta_tormenta': float  # Ángulo declinación tormenta (grados)
            }
        """
        self.nodos = nodos
        self.Lk = parametros.get('Lk', 0)
        self.D_fases = parametros.get('D_fases', 0)
        self.s_reposo = parametros.get('s_reposo', 0)
        self.s_decmax = parametros.get('s_decmax', 0)
        self.s_tormenta = parametros.get('s_tormenta', 0)
        self.Dhg = parametros.get('Dhg', 0)
        self.theta_max = parametros.get('theta_max', 0)
        self.theta_tormenta = parametros.get('theta_tormenta', 0)
        self.zonas = []
    
    def generar_todas_zonas(self) -> List[ZonaProhibida]:
        """Generar todas las zonas prohibidas basadas en nodos y conexiones"""
        self.zonas = []
        
        # 1. Zonas de conexiones tipo "columna"
        self._generar_zonas_columna()
        
        # 2. Zonas de conexiones tipo "mensula"
        self._generar_zonas_mensula()
        
        # 3. Zonas D_fases alrededor de conductores (Lk debajo del nodo)
        self._generar_zonas_d_fases()
        
        # 4. Zonas Dhg alrededor de guardias (Lk debajo del nodo)
        self._generar_zonas_dhg()
        
        # 5. Zonas s_reposo en nodos conductor
        self._generar_zonas_s_reposo_nodos()
        
        return self.zonas
    
    def _generar_zonas_columna(self):
        """Generar franjas verticales defasadas s_decmax a ambos lados de columnas"""
        for nombre, nodo in self.nodos.items():
            for nodo_destino, tipo_conexion in nodo.conexiones:
                if tipo_conexion == "columna":
                    # Franja vertical entre nodo origen y destino
                    x_centro = (nodo.x + nodo_destino.x) / 2
                    z_min = min(nodo.z, nodo_destino.z)
                    z_max = max(nodo.z, nodo_destino.z)
                    ancho = 2 * self.s_decmax
                    
                    self.zonas.append(FranjaVertical(
                        x_centro=x_centro,
                        z_min=z_min,
                        z_max=z_max,
                        ancho=ancho,
                        descripcion=f"Columna {nodo.nombre}-{nodo_destino.nombre}"
                    ))
    
    def _generar_zonas_mensula(self):
        """Generar franjas horizontales defasadas s_reposo por encima de mensulas"""
        for nombre, nodo in self.nodos.items():
            for nodo_destino, tipo_conexion in nodo.conexiones:
                if tipo_conexion == "mensula":
                    # Franja horizontal entre nodo origen y destino
                    x_min = min(nodo.x, nodo_destino.x)
                    x_max = max(nodo.x, nodo_destino.x)
                    z_centro = max(nodo.z, nodo_destino.z)
                    altura = self.s_reposo
                    
                    self.zonas.append(FranjaHorizontal(
                        x_min=x_min,
                        x_max=x_max,
                        z_centro=z_centro,
                        altura=altura,
                        descripcion=f"Ménsula {nodo.nombre}-{nodo_destino.nombre}"
                    ))
    
    def _generar_zonas_d_fases(self):
        """Generar círculos D_fases en posición -Lk de nodos conductor
        
        Genera 3 círculos por conductor: reposo, tormenta, máxima
        """
        for nombre, nodo in self.nodos.items():
            if nodo.tipo == "conductor":
                # Reposo
                z_reposo = nodo.z - self.Lk
                self.zonas.append(Circulo(
                    centro_x=nodo.x,
                    centro_z=z_reposo,
                    radio=self.D_fases,
                    tipo_zona="d_fases",
                    descripcion=f"D_fases de {nombre} (reposo)"
                ))
                
                # Tormenta
                if self.theta_tormenta > 0:
                    x_tormenta = nodo.x + self.Lk * math.sin(math.radians(self.theta_tormenta))
                    z_tormenta = nodo.z - self.Lk * math.cos(math.radians(self.theta_tormenta))
                    self.zonas.append(Circulo(
                        centro_x=x_tormenta,
                        centro_z=z_tormenta,
                        radio=self.D_fases,
                        tipo_zona="d_fases",
                        descripcion=f"D_fases de {nombre} (tormenta)"
                    ))
                
                # Máxima
                if self.theta_max > 0:
                    x_max = nodo.x + self.Lk * math.sin(math.radians(self.theta_max))
                    z_max = nodo.z - self.Lk * math.cos(math.radians(self.theta_max))
                    self.zonas.append(Circulo(
                        centro_x=x_max,
                        centro_z=z_max,
                        radio=self.D_fases,
                        tipo_zona="d_fases",
                        descripcion=f"D_fases de {nombre} (máxima)"
                    ))
    
    def _generar_zonas_dhg(self):
        """Generar círculos Dhg en posición -Lk de nodos guardia"""
        for nombre, nodo in self.nodos.items():
            if nodo.tipo == "guardia":
                # Posición del guardia (Lk debajo del nodo)
                z_guardia = nodo.z - self.Lk
                
                self.zonas.append(Circulo(
                    centro_x=nodo.x,
                    centro_z=z_guardia,
                    radio=self.Dhg,
                    tipo_zona="dhg",
                    descripcion=f"Dhg de {nombre}"
                ))
    
    def _generar_zonas_s_reposo_nodos(self):
        """Generar círculos s alrededor de cables conductor
        
        Genera 3 círculos por conductor: s_reposo, s_tormenta, s_decmax
        """
        for nombre, nodo in self.nodos.items():
            if nodo.tipo == "conductor":
                # s_reposo (reposo)
                z_reposo = nodo.z - self.Lk
                self.zonas.append(Circulo(
                    centro_x=nodo.x,
                    centro_z=z_reposo,
                    radio=self.s_reposo,
                    tipo_zona="s_reposo",
                    descripcion=f"s_reposo de {nombre}"
                ))
                
                # s_tormenta (tormenta)
                if self.theta_tormenta > 0 and self.s_tormenta > 0:
                    x_tormenta = nodo.x + self.Lk * math.sin(math.radians(self.theta_tormenta))
                    z_tormenta = nodo.z - self.Lk * math.cos(math.radians(self.theta_tormenta))
                    self.zonas.append(Circulo(
                        centro_x=x_tormenta,
                        centro_z=z_tormenta,
                        radio=self.s_tormenta,
                        tipo_zona="s_tormenta",
                        descripcion=f"s_tormenta de {nombre}"
                    ))
                
                # s_decmax (máxima)
                if self.theta_max > 0 and self.s_decmax > 0:
                    x_max = nodo.x + self.Lk * math.sin(math.radians(self.theta_max))
                    z_max = nodo.z - self.Lk * math.cos(math.radians(self.theta_max))
                    self.zonas.append(Circulo(
                        centro_x=x_max,
                        centro_z=z_max,
                        radio=self.s_decmax,
                        tipo_zona="s_decmax",
                        descripcion=f"s_decmax de {nombre}"
                    ))


class VerificadorZonasProhibidas:
    """Verificador de infracciones y distancias a zonas prohibidas"""
    
    def __init__(self, zonas: List[ZonaProhibida]):
        self.zonas = zonas
    
    def verificar_punto(self, x: float, z: float) -> dict:
        """Verificar si punto infringe zonas y calcular distancias
        
        Args:
            x: Coordenada x del punto
            z: Coordenada z del punto (posición del conductor, ya con -Lk aplicado)
        
        Returns:
            {
                'infringe': bool,
                'zonas_infringidas': [str],  # Descripciones de zonas infringidas
                'distancias': {
                    'columna': {'horizontal': float, 'vertical': float, 'minima': float},
                    'mensula': {...},
                    'd_fases': {...},
                    'dhg': {...}
                }
            }
        """
        resultado = {
            'infringe': False,
            'zonas_infringidas': [],
            'distancias': {
                'columna': {'horizontal': float('inf'), 'vertical': float('inf'), 'minima': float('inf')},
                'mensula': {'horizontal': float('inf'), 'vertical': float('inf'), 'minima': float('inf')},
                'd_fases': {'horizontal': float('inf'), 'vertical': float('inf'), 'minima': float('inf')},
                'dhg': {'horizontal': float('inf'), 'vertical': float('inf'), 'minima': float('inf')},
                's_reposo': {'horizontal': float('inf'), 'vertical': float('inf'), 'minima': float('inf')},
                's_tormenta': {'horizontal': float('inf'), 'vertical': float('inf'), 'minima': float('inf')},
                's_decmax': {'horizontal': float('inf'), 'vertical': float('inf'), 'minima': float('inf')}
            }
        }
        
        for zona in self.zonas:
            # Verificar infracción
            if zona.contiene_punto(x, z):
                resultado['infringe'] = True
                resultado['zonas_infringidas'].append(zona.descripcion)
            
            # Calcular distancias
            dx, dz, dist_min = zona.distancia_a_punto(x, z)
            tipo = zona.tipo_zona
            
            if dist_min < resultado['distancias'][tipo]['minima']:
                resultado['distancias'][tipo]['horizontal'] = dx
                resultado['distancias'][tipo]['vertical'] = dz
                resultado['distancias'][tipo]['minima'] = dist_min
        
        return resultado
    
    def buscar_altura_minima(self, x: float) -> Tuple[float, str]:
        """Buscar altura mínima z para que punto (x, z) esté fuera de todas las zonas
        
        Args:
            x: Coordenada x del punto
        
        Returns:
            (z_minima, razon) - Altura mínima y descripción de la zona crítica
        """
        z_min = 0
        razon = "Sin restricciones"
        
        for zona in self.zonas:
            if isinstance(zona, Circulo):
                # Para círculos, calcular z necesaria
                dx = abs(x - zona.centro_x)
                if dx < zona.radio:
                    dz = math.sqrt(zona.radio**2 - dx**2)
                    z_necesaria = zona.centro_z + dz
                    if z_necesaria > z_min:
                        z_min = z_necesaria
                        razon = zona.descripcion
            
            elif isinstance(zona, FranjaVertical):
                # Para franjas verticales
                if zona.x_min <= x <= zona.x_max:
                    if zona.z_max > z_min:
                        z_min = zona.z_max
                        razon = zona.descripcion
            
            elif isinstance(zona, FranjaHorizontal):
                # Para franjas horizontales
                if zona.x_min <= x <= zona.x_max:
                    if zona.z_max > z_min:
                        z_min = zona.z_max
                        razon = zona.descripcion
        
        return z_min, razon


# Función de conveniencia para uso en DGE
def crear_verificador_desde_nodos(nodos: Dict[str, Nodo], parametros: dict) -> VerificadorZonasProhibidas:
    """Crear verificador de zonas prohibidas desde estructura de nodos
    
    Args:
        nodos: Diccionario {nombre: Nodo}
        parametros: {'Lk', 'D_fases', 's_reposo', 's_decmax', 's_tormenta', 'Dhg'}
    
    Returns:
        VerificadorZonasProhibidas listo para usar
    """
    generador = GeneradorZonasProhibidas(nodos, parametros)
    zonas = generador.generar_todas_zonas()
    return VerificadorZonasProhibidas(zonas)
