# utils/geometria_zonas.py
"""
Módulo de zonas prohibidas geométricas para DGE.

Recibe estructura de nodos con conexiones y genera zonas prohibidas automáticamente
basadas en tipos de conexión (columna, mensula) y tipos de nodo (conductor, guardia).
"""

import math
from typing import List, Tuple, Optional, Dict
from utils.offset_geometria import calcular_offset_columna, calcular_offset_mensula


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
    """Franja vertical (columna con offset variable según altura)"""
    
    def __init__(self, x_centro: float, z_min: float, z_max: float, ancho_base: float, 
                 offset_params: dict = None, descripcion: str = ""):
        super().__init__(descripcion or f"Columna x={x_centro:.2f}m", "columna")
        self.x_centro = x_centro
        self.z_min = z_min
        self.z_max = z_max
        self.ancho_base = ancho_base  # s_decmax sin offset
        self.offset_params = offset_params  # {'z_ref_min', 'z_ref_max', 'offset_inicio', 'offset_fin', 'tipo'}
    
    def _calcular_offset(self, z: float) -> float:
        """Calcular offset interpolado para altura z"""
        if not self.offset_params:
            return 0
        return calcular_offset_columna(
            z, 
            self.offset_params['z_ref_min'],
            self.offset_params['z_ref_max'],
            self.offset_params['offset_inicio'],
            self.offset_params['offset_fin'],
            self.offset_params['tipo']
        )
    
    def contiene_punto(self, x: float, z: float) -> bool:
        if not (self.z_min <= z <= self.z_max):
            return False
        offset = self._calcular_offset(z)
        ancho_total = self.ancho_base + offset
        x_min = self.x_centro - ancho_total
        x_max = self.x_centro + ancho_total
        return x_min <= x <= x_max
    
    def distancia_a_punto(self, x: float, z: float) -> Tuple[float, float, float]:
        # Distancia vertical
        if z < self.z_min:
            dz = self.z_min - z
        elif z > self.z_max:
            dz = z - self.z_max
        else:
            dz = 0
        
        # Distancia horizontal con offset interpolado
        offset = self._calcular_offset(z)
        ancho_total = self.ancho_base + offset
        x_min = self.x_centro - ancho_total
        x_max = self.x_centro + ancho_total
        
        if x < x_min:
            dx = x_min - x
        elif x > x_max:
            dx = x - x_max
        else:
            dx = 0
        
        dist_min = math.sqrt(dx**2 + dz**2)
        return (dx, dz, dist_min)


class FranjaHorizontal(ZonaProhibida):
    """Franja horizontal (mensula con offset variable según posición X)"""
    
    def __init__(self, x_min: float, x_max: float, z_centro: float, altura_base: float, 
                 offset_params: dict = None, descripcion: str = ""):
        super().__init__(descripcion or f"Ménsula z={z_centro:.2f}m", "mensula")
        self.x_min = x_min
        self.x_max = x_max
        self.z_centro = z_centro
        self.altura_base = altura_base
        self.offset_params = offset_params
    
    def _calcular_offset(self, x: float) -> float:
        if not self.offset_params:
            return 0
        return calcular_offset_mensula(
            abs(x), self.offset_params['x_min'], self.offset_params['x_max'],
            self.offset_params['offset_inicio'], self.offset_params['offset_fin'],
            self.offset_params['tipo']
        )
    
    def contiene_punto(self, x: float, z: float) -> bool:
        if not (self.x_min <= x <= self.x_max):
            return False
        offset = self._calcular_offset(x)
        z_max_local = self.z_centro + self.altura_base + offset
        return self.z_centro <= z <= z_max_local
    
    def distancia_a_punto(self, x: float, z: float) -> Tuple[float, float, float]:
        if x < self.x_min:
            dx = self.x_min - x
        elif x > self.x_max:
            dx = x - self.x_max
        else:
            dx = 0
        
        offset = self._calcular_offset(x)
        z_max_local = self.z_centro + self.altura_base + offset
        
        if z < self.z_centro:
            dz = self.z_centro - z
        elif z > z_max_local:
            dz = z - z_max_local
        else:
            dz = 0
        
        dist_min = math.sqrt(dx**2 + dz**2)
        return (dx, dz, dist_min)


class Circulo(ZonaProhibida):
    """Zona circular (D_fases, Dhg, s_reposo en nodos)"""
    
    def __init__(self, centro_x: float, centro_z: float, radio: float, tipo_zona: str, descripcion: str = "", z_min_corte: float = None):
        super().__init__(descripcion or f"Círculo r={radio:.2f}m", tipo_zona)
        self.centro_x = centro_x
        self.centro_z = centro_z
        self.radio = radio
        self.z_min_corte = z_min_corte  # Si se especifica, solo considera puntos con z >= z_min_corte
    
    def contiene_punto(self, x: float, z: float) -> bool:
        # Si hay corte inferior, ignorar puntos por debajo
        if self.z_min_corte is not None and z < self.z_min_corte:
            return False
        
        dist = math.sqrt((x - self.centro_x)**2 + (z - self.centro_z)**2)
        return dist < self.radio
    
    def distancia_a_punto(self, x: float, z: float) -> Tuple[float, float, float]:
        # Si hay corte inferior y el punto está por debajo, retornar distancia infinita
        if self.z_min_corte is not None and z < self.z_min_corte:
            return (float('inf'), float('inf'), float('inf'))
        
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
                'theta_max': float,
                'theta_tormenta': float,
                'd_fases_solo_reposo': bool,
                'z_min_corte': float,
                'offset_columna_base': bool,
                'offset_columna_inter': bool,
                'offset_mensula': bool,
                'offset_columna_base_tipo': str,
                'offset_columna_inter_tipo': str,
                'offset_mensula_tipo': str,
                'offset_columna_base_inicio': float,
                'offset_columna_base_fin': float,
                'offset_columna_inter_inicio': float,
                'offset_columna_inter_fin': float,
                'offset_mensula_inicio': float,
                'offset_mensula_fin': float,
                'h_cross_h1': float  # Altura de CROSS_H1 para separar base/inter
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
        self.d_fases_solo_reposo = parametros.get('d_fases_solo_reposo', False)
        self.z_min_corte = parametros.get('z_min_corte', None)
        
        # Parámetros de offset
        self.offset_columna_base = parametros.get('offset_columna_base', False)
        self.offset_columna_inter = parametros.get('offset_columna_inter', False)
        self.offset_mensula = parametros.get('offset_mensula', False)
        self.offset_columna_base_tipo = parametros.get('offset_columna_base_tipo', 'Trapezoidal')
        self.offset_columna_inter_tipo = parametros.get('offset_columna_inter_tipo', 'Recto')
        self.offset_mensula_tipo = parametros.get('offset_mensula_tipo', 'Triangular')
        self.offset_columna_base_inicio = parametros.get('offset_columna_base_inicio', 3.3)
        self.offset_columna_base_fin = parametros.get('offset_columna_base_fin', 0.65)
        self.offset_columna_inter_inicio = parametros.get('offset_columna_inter_inicio', 0.65)
        self.offset_columna_inter_fin = parametros.get('offset_columna_inter_fin', 0.65)
        self.offset_mensula_inicio = parametros.get('offset_mensula_inicio', 1.48)
        self.offset_mensula_fin = parametros.get('offset_mensula_fin', 0.0)
        self.h_cross_h1 = parametros.get('h_cross_h1', 0)
        
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
                    x_centro = (nodo.x + nodo_destino.x) / 2
                    z_min = min(nodo.z, nodo_destino.z)
                    z_max = max(nodo.z, nodo_destino.z)
                    
                    # Determinar si es columna base o inter
                    es_base = z_min < self.h_cross_h1 if self.h_cross_h1 > 0 else True
                    
                    # Preparar parámetros de offset para interpolación
                    offset_params = None
                    if es_base and self.offset_columna_base:
                        offset_params = {
                            'z_ref_min': 0,
                            'z_ref_max': self.h_cross_h1,
                            'offset_inicio': self.offset_columna_base_inicio,
                            'offset_fin': self.offset_columna_base_fin,
                            'tipo': self.offset_columna_base_tipo
                        }
                    elif not es_base and self.offset_columna_inter:
                        z_max_estructura = max(n.z for n in self.nodos.values())
                        offset_params = {
                            'z_ref_min': self.h_cross_h1,
                            'z_ref_max': z_max_estructura,
                            'offset_inicio': self.offset_columna_inter_inicio,
                            'offset_fin': self.offset_columna_inter_fin,
                            'tipo': self.offset_columna_inter_tipo
                        }
                    
                    self.zonas.append(FranjaVertical(
                        x_centro=x_centro,
                        z_min=z_min,
                        z_max=z_max,
                        ancho_base=self.s_decmax,
                        offset_params=offset_params,
                        descripcion=f"Columna {nodo.nombre}-{nodo_destino.nombre}"
                    ))
    
    def _generar_zonas_mensula(self):
        """Generar zonas prohibidas alrededor de ménsulas
        
        Para cada ménsula genera:
        1. Franja horizontal sobre la ménsula (offset s)
        2. Círculo en la punta del conductor (radio s)
        
        SOLO genera las zonas del parámetro s activo (> 0).
        """
        if self.Lk == 0.0:
            return  # Si Lk es 0, no se generan zonas de ménsula para s_*, los chequeos se dan por buenos.

        for nombre, nodo in self.nodos.items():
            for nodo_destino, tipo_conexion in nodo.conexiones:
                if tipo_conexion == "mensula":
                    x_min = min(nodo.x, nodo_destino.x)
                    x_max = max(nodo.x, nodo_destino.x)
                    z_mensula = max(nodo.z, nodo_destino.z)
                    
                    # Posición del conductor (Lk debajo del amarre)
                    x_conductor = nodo_destino.x
                    z_conductor = nodo_destino.z - self.Lk
                    
                    # Calcular offset ménsula si está activado
                    if self.offset_mensula:
                        offset_inicio = calcular_offset_mensula(
                            abs(x_min), abs(x_min), abs(x_max),
                            self.offset_mensula_inicio,
                            self.offset_mensula_fin,
                            self.offset_mensula_tipo
                        )
                        offset_fin = calcular_offset_mensula(
                            abs(x_max), abs(x_min), abs(x_max),
                            self.offset_mensula_inicio,
                            self.offset_mensula_fin,
                            self.offset_mensula_tipo
                        )
                        offset_conductor = calcular_offset_mensula(
                            abs(x_conductor), abs(x_min), abs(x_max),
                            self.offset_mensula_inicio,
                            self.offset_mensula_fin,
                            self.offset_mensula_tipo
                        )
                    else:
                        offset_inicio = 0
                        offset_fin = 0
                        offset_conductor = 0
                    
                    # Preparar parámetros de offset para interpolación
                    offset_params_franja = None
                    if self.offset_mensula:
                        offset_params_franja = {
                            'x_min': abs(x_min),
                            'x_max': abs(x_max),
                            'offset_inicio': self.offset_mensula_inicio,
                            'offset_fin': self.offset_mensula_fin,
                            'tipo': self.offset_mensula_tipo
                        }
                    
                    # Franja s_reposo
                    if self.s_reposo > 0:
                        self.zonas.append(FranjaHorizontal(
                            x_min=x_min,
                            x_max=x_max,
                            z_centro=z_mensula,
                            altura_base=self.s_reposo,
                            offset_params=offset_params_franja,
                            descripcion=f"Ménsula {nodo.nombre}-{nodo_destino.nombre} (s_reposo)"
                        ))
                        self.zonas.append(Circulo(
                            centro_x=x_conductor,
                            centro_z=z_mensula,
                            radio=self.s_reposo + offset_conductor,
                            tipo_zona="mensula",
                            descripcion=f"Ménsula {nodo.nombre}-{nodo_destino.nombre} punta (s_reposo)",
                            z_min_corte=z_mensula
                        ))
                    
                    # Franja s_tormenta
                    if self.s_tormenta > 0:
                        self.zonas.append(FranjaHorizontal(
                            x_min=x_min,
                            x_max=x_max,
                            z_centro=z_mensula,
                            altura_base=self.s_tormenta,
                            offset_params=offset_params_franja,
                            descripcion=f"Ménsula {nodo.nombre}-{nodo_destino.nombre} (s_tormenta)"
                        ))
                        self.zonas.append(Circulo(
                            centro_x=x_conductor,
                            centro_z=z_mensula,
                            radio=self.s_tormenta + offset_conductor,
                            tipo_zona="mensula",
                            descripcion=f"Ménsula {nodo.nombre}-{nodo_destino.nombre} punta (s_tormenta)",
                            z_min_corte=z_mensula
                        ))
                    
                    # Franja s_decmax
                    if self.s_decmax > 0:
                        self.zonas.append(FranjaHorizontal(
                            x_min=x_min,
                            x_max=x_max,
                            z_centro=z_mensula,
                            altura_base=self.s_decmax,
                            offset_params=offset_params_franja,
                            descripcion=f"Ménsula {nodo.nombre}-{nodo_destino.nombre} (s_decmax)"
                        ))
                        self.zonas.append(Circulo(
                            centro_x=x_conductor,
                            centro_z=z_mensula,
                            radio=self.s_decmax + offset_conductor,
                            tipo_zona="mensula",
                            descripcion=f"Ménsula {nodo.nombre}-{nodo_destino.nombre} punta (s_decmax)",
                            z_min_corte=z_mensula
                        ))
    
    def _generar_zonas_d_fases(self):
        """Generar círculos D_fases en posición -Lk de nodos conductor
        
        Si d_fases_solo_reposo=True, solo genera en reposo.
        Si False, genera 3 círculos por conductor: reposo, tormenta, máxima
        """
        for nombre, nodo in self.nodos.items():
            if nodo.tipo == "conductor":
                # Reposo (siempre)
                z_reposo = nodo.z - self.Lk
                self.zonas.append(Circulo(
                    centro_x=nodo.x,
                    centro_z=z_reposo,
                    radio=self.D_fases,
                    tipo_zona="d_fases",
                    descripcion=f"D_fases de {nombre} (reposo)"
                ))
                
                # Tormenta y Máxima solo si no es solo_reposo
                if not self.d_fases_solo_reposo:
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
        """Generar círculos s alrededor de NODOS AMARRE conductor
        
        Genera 3 círculos por conductor: s_reposo, s_tormenta, s_decmax
        Centrados en el NODO AMARRE (nodo.z), NO en el cable (nodo.z - Lk)
        """
        for nombre, nodo in self.nodos.items():
            if nodo.tipo == "conductor":
                # s_reposo (reposo) - centrado en NODO AMARRE
                self.zonas.append(Circulo(
                    centro_x=nodo.x,
                    centro_z=nodo.z,
                    radio=self.s_reposo,
                    tipo_zona="s_reposo",
                    descripcion=f"s_reposo de {nombre}"
                ))
                
                # s_tormenta (tormenta) - centrado en NODO AMARRE
                if self.s_tormenta > 0:
                    self.zonas.append(Circulo(
                        centro_x=nodo.x,
                        centro_z=nodo.z,
                        radio=self.s_tormenta,
                        tipo_zona="s_tormenta",
                        descripcion=f"s_tormenta de {nombre}"
                    ))
                
                # s_decmax (máxima) - centrado en NODO AMARRE
                if self.s_decmax > 0:
                    self.zonas.append(Circulo(
                        centro_x=nodo.x,
                        centro_z=nodo.z,
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
                # Para franjas horizontales con offset interpolado
                if zona.x_min <= x <= zona.x_max:
                    offset = zona._calcular_offset(x)
                    z_max_local = zona.z_centro + zona.altura_base + offset
                    if z_max_local > z_min:
                        z_min = z_max_local
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
