"""
Análisis Estático de Esfuerzos (AEE)
Calcula esfuerzos en barras de estructura sin propiedades E, I, A
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, List, Tuple, Optional

class AnalizadorEstatico:
    """Analizador estático de esfuerzos en estructuras"""
    
    def __init__(self, geometria, mecanica, parametros_aee):
        """
        Args:
            geometria: EstructuraAEA_Geometria con nodos y conexiones
            mecanica: EstructuraAEA_Mecanica con cargas por hipótesis
            parametros_aee: Dict con configuración AEE
        """
        self.geometria = geometria
        self.mecanica = mecanica
        self.parametros = parametros_aee
        
        # Extraer conexiones de geometría
        self.conexiones = self._extraer_conexiones()
        
        # Segmentar conexiones
        self.conexiones_segmentadas = self._segmentar_conexiones()
    
    def _extraer_conexiones(self) -> List[Tuple[str, str]]:
        """Extrae lista de conexiones (nodo_i, nodo_j) desde geometría"""
        conexiones = []
        
        # Recorrer todas las conexiones en geometría
        for nombre_nodo, nodo in self.geometria.nodos.items():
            # Las conexiones están en nodo.conexiones como lista de nombres
            if hasattr(nodo, 'conexiones'):
                for nodo_destino in nodo.conexiones:
                    # Evitar duplicados (A-B y B-A)
                    if (nombre_nodo, nodo_destino) not in conexiones and \
                       (nodo_destino, nombre_nodo) not in conexiones:
                        conexiones.append((nombre_nodo, nodo_destino))
        
        return conexiones
    
    def _segmentar_conexiones(self) -> Dict:
        """Segmenta conexiones en cortas/largas según percentil"""
        # Calcular longitudes
        longitudes = []
        for nodo_i, nodo_j in self.conexiones:
            coord_i = self.geometria.nodos[nodo_i].coordenadas
            coord_j = self.geometria.nodos[nodo_j].coordenadas
            longitud = np.linalg.norm(np.array(coord_j) - np.array(coord_i))
            longitudes.append(longitud)
        
        # Calcular percentil
        percentil = self.parametros.get('percentil_separacion_corta_larga', 50)
        umbral = np.percentile(longitudes, percentil)
        
        # Clasificar y segmentar
        segmentadas = {
            'cortas': [],
            'largas': []
        }
        
        n_corta = self.parametros.get('n_segmentar_conexion_corta', 10)
        n_larga = self.parametros.get('n_segmentar_conexion_larga', 30)
        
        for (nodo_i, nodo_j), longitud in zip(self.conexiones, longitudes):
            n_elementos = n_corta if longitud <= umbral else n_larga
            categoria = 'cortas' if longitud <= umbral else 'largas'
            
            segmentadas[categoria].append({
                'nodo_i': nodo_i,
                'nodo_j': nodo_j,
                'longitud': longitud,
                'n_elementos': n_elementos
            })
        
        return segmentadas
    
    def resolver_sistema(self, hipotesis_nombre: str) -> Dict:
        """
        Resuelve sistema de ecuaciones para obtener esfuerzos
        
        Args:
            hipotesis_nombre: Nombre de hipótesis de carga
            
        Returns:
            Dict con esfuerzos por conexión {(nodo_i, nodo_j): [N, Qy, Qz, Mx, My, Mz]}
        """
        # Obtener cargas de la hipótesis
        cargas = self._obtener_cargas_hipotesis(hipotesis_nombre)
        
        # Construir matriz de rigidez (solo geométrica, sin E/I/A)
        K = self._construir_matriz_rigidez()
        
        # Vector de cargas
        F = self._construir_vector_cargas(cargas)
        
        # Resolver sistema K * u = F
        try:
            u = np.linalg.solve(K, F)
        except np.linalg.LinAlgError:
            # Sistema singular, usar mínimos cuadrados
            u = np.linalg.lstsq(K, F, rcond=None)[0]
        
        # Calcular esfuerzos en cada conexión
        esfuerzos = self._calcular_esfuerzos_conexiones(u)
        
        return esfuerzos
    
    def _obtener_cargas_hipotesis(self, hipotesis_nombre: str) -> Dict:
        """Obtiene cargas de nodos para hipótesis"""
        cargas = {}
        
        for nombre_nodo, nodo in self.geometria.nodos.items():
            # Obtener cargas del nodo en coordenadas globales
            carga = nodo.obtener_cargas_hipotesis(hipotesis_nombre)
            if carga:
                cargas[nombre_nodo] = carga
        
        return cargas
    
    def _construir_matriz_rigidez(self) -> np.ndarray:
        """Construye matriz de rigidez geométrica (sin E/I/A)"""
        n_nodos = len(self.geometria.nodos)
        n_gdl = n_nodos * 6  # 6 grados de libertad por nodo
        
        K = np.zeros((n_gdl, n_gdl))
        
        # Agregar rigidez de cada conexión
        for conexion in self.conexiones:
            nodo_i, nodo_j = conexion
            k_local = self._matriz_rigidez_barra(nodo_i, nodo_j)
            
            # Ensamblar en matriz global
            idx_i = list(self.geometria.nodos.keys()).index(nodo_i)
            idx_j = list(self.geometria.nodos.keys()).index(nodo_j)
            
            gdl_i = slice(idx_i * 6, (idx_i + 1) * 6)
            gdl_j = slice(idx_j * 6, (idx_j + 1) * 6)
            
            K[gdl_i, gdl_i] += k_local[:6, :6]
            K[gdl_i, gdl_j] += k_local[:6, 6:]
            K[gdl_j, gdl_i] += k_local[6:, :6]
            K[gdl_j, gdl_j] += k_local[6:, 6:]
        
        return K
    
    def _matriz_rigidez_barra(self, nodo_i: str, nodo_j: str) -> np.ndarray:
        """Matriz de rigidez de barra (12x12) sin E/I/A"""
        coord_i = np.array(self.geometria.nodos[nodo_i].coordenadas)
        coord_j = np.array(self.geometria.nodos[nodo_j].coordenadas)
        
        L = np.linalg.norm(coord_j - coord_i)
        
        # Vector director
        v = (coord_j - coord_i) / L
        
        # Matriz de rigidez simplificada (solo geometría)
        k = np.zeros((12, 12))
        
        # Rigidez axial (normalizada)
        k[0, 0] = k[6, 6] = 1.0 / L
        k[0, 6] = k[6, 0] = -1.0 / L
        
        # Rigidez flexional (normalizada)
        k[1, 1] = k[7, 7] = 12.0 / L**3
        k[1, 7] = k[7, 1] = -12.0 / L**3
        
        k[2, 2] = k[8, 8] = 12.0 / L**3
        k[2, 8] = k[8, 2] = -12.0 / L**3
        
        return k
    
    def _construir_vector_cargas(self, cargas: Dict) -> np.ndarray:
        """Construye vector de cargas globales"""
        n_nodos = len(self.geometria.nodos)
        F = np.zeros(n_nodos * 6)
        
        for nombre_nodo, carga in cargas.items():
            idx = list(self.geometria.nodos.keys()).index(nombre_nodo)
            gdl = slice(idx * 6, (idx + 1) * 6)
            
            # carga = [Fx, Fy, Fz, Mx, My, Mz] en daN y daN.m
            F[gdl] = carga
        
        return F
    
    def _calcular_esfuerzos_conexiones(self, u: np.ndarray) -> Dict:
        """Calcula esfuerzos en conexiones desde desplazamientos"""
        esfuerzos = {}
        
        for conexion in self.conexiones:
            nodo_i, nodo_j = conexion
            
            idx_i = list(self.geometria.nodos.keys()).index(nodo_i)
            idx_j = list(self.geometria.nodos.keys()).index(nodo_j)
            
            u_i = u[idx_i * 6:(idx_i + 1) * 6]
            u_j = u[idx_j * 6:(idx_j + 1) * 6]
            
            # Calcular esfuerzos [N, Qy, Qz, Mx, My, Mz]
            k_local = self._matriz_rigidez_barra(nodo_i, nodo_j)
            u_local = np.concatenate([u_i, u_j])
            f_local = k_local @ u_local
            
            esfuerzos[conexion] = f_local[:6]  # Esfuerzos en nodo i
        
        return esfuerzos
    
    def calcular_momento_resultante_total(self, esfuerzos: Dict) -> Dict:
        """Calcula MRT = sqrt(Mx^2 + My^2 + Mz^2) para cada conexión"""
        mrt = {}
        
        for conexion, esf in esfuerzos.items():
            Mx, My, Mz = esf[3], esf[4], esf[5]
            mrt[conexion] = np.sqrt(Mx**2 + My**2 + Mz**2)
        
        return mrt
    
    def calcular_momento_flector_equivalente(self, esfuerzos: Dict) -> Dict:
        """Calcula MFE = sqrt(My^2 + Mz^2) para cada conexión"""
        mfe = {}
        
        for conexion, esf in esfuerzos.items():
            My, Mz = esf[4], esf[5]
            mfe[conexion] = np.sqrt(My**2 + Mz**2)
        
        return mfe
    
    def generar_diagrama_3d(self, valores: Dict, tipo: str, hipotesis: str) -> plt.Figure:
        """Genera diagrama 3D con escala de colores"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Extraer coordenadas y valores
        coords = []
        vals = []
        
        for (nodo_i, nodo_j), valor in valores.items():
            coord_i = self.geometria.nodos[nodo_i].coordenadas
            coord_j = self.geometria.nodos[nodo_j].coordenadas
            
            coords.append([coord_i, coord_j])
            vals.append(valor)
        
        # Normalizar valores para colormap
        vmin, vmax = min(vals), max(vals)
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.jet
        
        # Dibujar conexiones con colores
        for (coord_i, coord_j), valor in zip(coords, vals):
            color = cmap(norm(valor))
            ax.plot([coord_i[0], coord_j[0]], 
                   [coord_i[1], coord_j[1]], 
                   [coord_i[2], coord_j[2]], 
                   color=color, linewidth=2)
        
        # Colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, label=f'{tipo} [daN.m]')
        
        ax.set_xlabel('X [m]')
        ax.set_ylabel('Y [m]')
        ax.set_zlabel('Z [m]')
        ax.set_title(f'{tipo} - {hipotesis}')
        
        return fig
    
    def generar_diagrama_2d(self, valores: Dict, tipo: str, hipotesis: str) -> plt.Figure:
        """Genera diagrama 2D (vista XZ) con escala de colores"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Extraer coordenadas y valores
        coords = []
        vals = []
        
        for (nodo_i, nodo_j), valor in valores.items():
            coord_i = self.geometria.nodos[nodo_i].coordenadas
            coord_j = self.geometria.nodos[nodo_j].coordenadas
            
            coords.append([coord_i, coord_j])
            vals.append(valor)
        
        # Normalizar valores para colormap
        vmin, vmax = min(vals), max(vals)
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.jet
        
        # Dibujar conexiones con colores (vista XZ)
        for (coord_i, coord_j), valor in zip(coords, vals):
            color = cmap(norm(valor))
            ax.plot([coord_i[0], coord_j[0]], 
                   [coord_i[2], coord_j[2]], 
                   color=color, linewidth=2)
        
        # Colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, label=f'{tipo} [daN.m]')
        
        ax.set_xlabel('X [m]')
        ax.set_ylabel('Z [m]')
        ax.set_title(f'{tipo} - {hipotesis}')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        return fig
