"""Cálculo de franja de servidumbre según AEA-95301-2007 9.2-1"""

import math


class ServidumbreAEA:
    """Calcula franja de servidumbre para estructuras de transmisión"""
    
    def __init__(self, estructura_geometria, flecha_viento_max_conductor, tension_nominal, Lk):
        """
        Args:
            estructura_geometria: Objeto EstructuraAEA_Geometria
            flecha_viento_max_conductor: Flecha total/absoluta en estado de viento máximo en m (de CMC)
            tension_nominal: Tensión nominal de línea en kV (Vn)
            Lk: Longitud de cadena en m
        """
        self.estructura = estructura_geometria
        self.fi = flecha_viento_max_conductor
        self.Vn = tension_nominal
        self.Lk = Lk
        self.theta_max = estructura_geometria.dimensiones['theta_max']
        
        # Constantes AEA
        self.mu = 1.1
        self.factor_enrarecimiento = 1.2
        self.factor_cresta = 0.82
        
        # Calcular valores intermedios
        self.Vs = self.mu * self.factor_enrarecimiento * self.factor_cresta * self.Vn
        self.dm = self.Vs / 150
        self.d = 1.5 * self.dm + 2
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
        """Calcula ancho total de franja según AEA-95301-2007 9.2-1"""
        theta_rad = math.radians(self.theta_max)
        return self.C + 2 * (self.Lk + self.fi) * math.sin(theta_rad) + 2 * self.d
    
    def generar_memoria_calculo(self):
        """Genera memoria de cálculo detallada"""
        memoria = []
        memoria.append("=" * 80)
        memoria.append("MEMORIA DE CÁLCULO: FRANJA DE SERVIDUMBRE AEA-95301-2007 9.2-1")
        memoria.append("=" * 80)
        memoria.append("")
        memoria.append("PARÁMETROS DE ENTRADA:")
        memoria.append(f"  Tensión nominal (Vn): {self.Vn:.1f} kV")
        memoria.append(f"  Longitud cadena (Lk): {self.Lk:.3f} m")
        memoria.append(f"  Flecha viento máximo conductor (fi): {self.fi:.3f} m")
        memoria.append(f"  Ángulo declinación máxima (theta_max): {self.theta_max:.2f}°")
        memoria.append("")
        memoria.append("CONSTANTES:")
        memoria.append(f"  Coeficiente sobretensión (μ): {self.mu}")
        memoria.append(f"  Factor enrarecimiento aire: {self.factor_enrarecimiento}")
        memoria.append(f"  Factor cresta tensión: {self.factor_cresta}")
        memoria.append("")
        memoria.append("CÁLCULOS INTERMEDIOS:")
        memoria.append(f"  Vs = μ * 1.2 * 0.82 * Vn")
        memoria.append(f"  Vs = {self.mu} * {self.factor_enrarecimiento} * {self.factor_cresta} * {self.Vn:.1f}")
        memoria.append(f"  Vs = {self.Vs:.2f} kV")
        memoria.append("")
        memoria.append(f"  dm = Vs / 150")
        memoria.append(f"  dm = {self.Vs:.2f} / 150")
        memoria.append(f"  dm = {self.dm:.3f} m")
        memoria.append("")
        memoria.append(f"  d = 1.5 * dm + 2")
        memoria.append(f"  d = 1.5 * {self.dm:.3f} + 2")
        memoria.append(f"  d = {self.d:.3f} m")
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
