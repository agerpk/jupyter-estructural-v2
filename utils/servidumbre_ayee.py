"""Cálculo de franja de servidumbre según normativa AyEE"""

import math

# Tabla de distancias según tensión y zona
TABLA_DISTANCIAS_AYEE = {
    66: {"rural": 3.0, "urbana": 4.2},
    132: {"rural": 3.15, "urbana": 4.35},
    220: {"rural": 3.75, "urbana": 4.95}
}


class ServidumbreAyEE:
    """Calcula franja de servidumbre para estructuras de transmisión según AyEE"""
    
    def __init__(self, estructura_geometria, flecha_viento_max_conductor, tension_nominal, Lk, zona_estructura):
        """
        Args:
            estructura_geometria: Objeto EstructuraAEA_Geometria
            flecha_viento_max_conductor: Flecha total/absoluta en estado de viento máximo en m (de CMC)
            tension_nominal: Tensión nominal de línea en kV (Vn)
            Lk: Longitud de cadena en m
            zona_estructura: Zona de estructura ("urbana" o "rural")
        """
        self.estructura = estructura_geometria
        self.fi = flecha_viento_max_conductor
        self.Vn = tension_nominal
        self.Lk = Lk
        self.zona_estructura = zona_estructura
        self.theta_max = estructura_geometria.dimensiones['theta_max']
        
        # Determinar tensión de tabla
        if self.Vn <= 66:
            self.tension_tabla = 66
        elif self.Vn <= 132:
            self.tension_tabla = 132
        else:
            self.tension_tabla = 220
        
        # Determinar tipo de zona
        self.zona_tipo = "urbana" if zona_estructura.lower() == "urbana" else "rural"
        
        # Obtener distancia d de tabla
        self.d = TABLA_DISTANCIAS_AYEE[self.tension_tabla][self.zona_tipo]
        
        # Vs y dm no aplican en AyEE (se usa tabla directa)
        self.Vs = None
        self.dm = None
        
        # Calcular valores
        self.C = self._calcular_C()
        self.A = self._calcular_A()
    
    def _calcular_C(self):
        """Calcula distancia transversal entre conductores externos"""
        nodos_conductor = {n: coords for n, coords in self.estructura.nodes_key.items() 
                          if self.estructura.nodos[n].tipo_nodo == 'conductor'}
        if not nodos_conductor:
            return 0.0
        x_coords = [coords[0] for coords in nodos_conductor.values()]
        return max(x_coords) - min(x_coords)
    
    def _calcular_A(self):
        """Calcula ancho total de franja"""
        theta_rad = math.radians(self.theta_max)
        return self.C + 2 * (self.Lk + self.fi) * math.sin(theta_rad) + 2 * self.d
    
    def generar_memoria_calculo(self):
        """Genera memoria de cálculo detallada"""
        memoria = []
        memoria.append("=" * 80)
        memoria.append("MEMORIA DE CÁLCULO: FRANJA DE SERVIDUMBRE AyEE")
        memoria.append("=" * 80)
        memoria.append("")
        memoria.append("PARÁMETROS DE ENTRADA:")
        memoria.append(f"  Tensión nominal (Vn): {self.Vn:.1f} kV")
        memoria.append(f"  Zona estructura: {self.zona_estructura}")
        memoria.append(f"  Longitud cadena (Lk): {self.Lk:.3f} m")
        memoria.append(f"  Flecha viento máximo conductor (fi): {self.fi:.3f} m")
        memoria.append(f"  Ángulo declinación máxima (theta_max): {self.theta_max:.2f}°")
        memoria.append("")
        memoria.append("TABLA DE DISTANCIAS AyEE:")
        memoria.append("  Tensión (kV) | Rural (m) | Urbana (m)")
        memoria.append("  " + "-" * 40)
        for tension in [66, 132, 220]:
            memoria.append(f"       {tension:3d}     |   {TABLA_DISTANCIAS_AYEE[tension]['rural']:.2f}    |    {TABLA_DISTANCIAS_AYEE[tension]['urbana']:.2f}")
        memoria.append("")
        memoria.append("SELECCIÓN DE DISTANCIA:")
        memoria.append(f"  Tensión nominal: {self.Vn:.1f} kV → Usar tabla de {self.tension_tabla} kV")
        memoria.append(f"  Zona: {self.zona_estructura} → Usar tipo '{self.zona_tipo}'")
        memoria.append(f"  Distancia d (de tabla): {self.d:.3f} m")
        memoria.append("")
        memoria.append(f"  C = max(x_conductores) - min(x_conductores)")
        memoria.append(f"  C = {self.C:.3f} m")
        memoria.append("")
        memoria.append("CÁLCULO FINAL:")
        theta_rad = math.radians(self.theta_max)
        termino_proyeccion = (self.Lk + self.fi) * math.sin(theta_rad)
        memoria.append(f"  A = C + 2 * (Lk + fi) * sen(theta_max) + 2 * d")
        memoria.append(f"  A = {self.C:.3f} + 2 * ({self.Lk:.3f} + {self.fi:.3f}) * sen({self.theta_max:.2f}°) + 2 * {self.d:.3f}")
        memoria.append(f"  A = {self.C:.3f} + 2 * {termino_proyeccion:.3f} + {2*self.d:.3f}")
        memoria.append(f"  A = {self.A:.3f} m")
        memoria.append("")
        memoria.append("RESULTADOS:")
        memoria.append(f"  Ancho total franja (A): {self.A:.3f} m")
        memoria.append(f"  Distancia conductores externos (C): {self.C:.3f} m")
        memoria.append(f"  Distancia seguridad (d): {self.d:.3f} m")
        memoria.append(f"  Ancho zona proyección (cada lado): {termino_proyeccion:.3f} m")
        memoria.append("=" * 80)
        return "\n".join(memoria)
