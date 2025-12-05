import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math

class Estructura3D:
    """
    Clase para generar visualizaciones 3D simplificadas de estructuras de líneas de transmisión
    """
    
    def __init__(self, estructura_poo, postes_obj):
        self.estructura = estructura_poo
        self.postes = postes_obj
        
        # Configuración de colores mejorada
        self.colores = {
            'poste': "#737373",        # Marrón madera
            'cruceta': "#000000",      # Gris oscuro
            'mensula': "#000000",      # Gris medio  
            'conductor': '#FF0000',    # Rojo
            'guardia': "#0C8D2A",      # Azul
            'vinculo': "#000000",      # Rojo naranja
            'suelo': "#BA5608",        # Verde lima
            'texto': '#000000',        # Negro
            'punto_amarre': "#0C57B4", # Magenta
            'top': '#FFA500'           # Naranja para TOP
        }
        
    def graficar_3d(self, figsize=(15, 12), elev=25, azim=45):
        """
        Genera el gráfico 3D simplificado con escala corregida
        """
        print("🎨 GENERANDO VISUALIZACIÓN 3D CON ESCALA CORREGIDA...")
        
        # Obtener geometría multiposte
        try:
            nodes_multiposte, tramos, geometria = self.postes.obtener_geometria_multiposte()
        except ValueError as e:
            print(f"❌ Error: {e}")
            # Crear datos mínimos para debugging
            nodes_multiposte = {
                'P1_BASE': [0, 0, 0], 
                'P1_CIMA': [0, 0, 20],
                'C1_L': [-1, 0, 15], 
                'HG1': [0, 0, 18],
                'TOP': [0, 0, 20]
            }
            tramos = {
                'POSTE_P1': {'tipo': 'poste', 'nodo_inicio': 'P1_BASE', 'nodo_fin': 'P1_CIMA'}
            }
            geometria = {'n_postes': 1, 'orientacion': 'Centrado', 'Ht': 20, 'Hl': 18, 'dc': 0.26}
        
        # Verificar y corregir unidades
        nodes_multiposte = self._verificar_unidades_nodos(nodes_multiposte)
        
        # Crear figura 3D
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        # 1. DIBUJAR POSTES (líneas simples)
        self._dibujar_postes_lineas(ax, nodes_multiposte, tramos)
        
        # 2. DIBUJAR VÍNCULOS
        self._dibujar_vinculos(ax, nodes_multiposte, tramos)
        
        # 3. DIBUJAR CRUCETAS Y MÉNSULAS
        self._dibujar_crucetas_mensulas(ax, nodes_multiposte, tramos)
        
        # 4. DIBUJAR PUNTOS DE AMARRE Y CABLES
        self._dibujar_puntos_amarre(ax, nodes_multiposte)
        
        # 5. CONFIGURAR VISUALIZACIÓN CON ESCALA CORREGIDA
        self._configurar_visualizacion_corregida(ax, nodes_multiposte, geometria, elev, azim)
        
        print("✅ Visualización 3D con escala corregida generada")
        return fig, ax
    
    def _verificar_unidades_nodos(self, nodes):
        """Verifica y corrige las unidades de los nodos"""
        nodes_corregidos = {}
        
        for nombre, coords in nodes.items():
            x, y, z = coords
            
            # Si las coordenadas son muy grandes (posible error de unidades), escalar
            if max(abs(x), abs(y), abs(z)) > 1000:  # Si hay valores > 1000, probablemente están en mm
                x, y, z = x/1000.0, y/1000.0, z/1000.0
                print(f"⚠️  Ajustando unidades de nodo {nombre}: dividiendo por 1000")
            
            nodes_corregidos[nombre] = [x, y, z]
        
        return nodes_corregidos
    
    def _dibujar_postes_lineas(self, ax, nodes, tramos):
        """Dibuja los postes como líneas simples"""
        postes_tramos = {k: v for k, v in tramos.items() if v['tipo'] == 'poste'}
        
        print(f"📏 Dibujando {len(postes_tramos)} postes...")
        
        for tramo_id, tramo in postes_tramos.items():
            if tramo['nodo_inicio'] in nodes and tramo['nodo_fin'] in nodes:
                inicio = nodes[tramo['nodo_inicio']]
                fin = nodes[tramo['nodo_fin']]
                
                # Dibujar línea del poste
                self._dibujar_linea(ax, inicio, fin, self.colores['poste'], linewidth=4)
                
                # Marcar base y cima
                ax.scatter(*inicio, color=self.colores['poste'], s=80, marker='s', alpha=0.8, label='Base' if tramo_id == 'POSTE_P1' else "")
                ax.scatter(*fin, color=self.colores['poste'], s=80, marker='^', alpha=0.8, label='Cima' if tramo_id == 'POSTE_P1' else "")
    
    def _dibujar_vinculos(self, ax, nodes, tramos):
        """Dibuja los vínculos entre postes"""
        vinculos_tramos = {k: v for k, v in tramos.items() if v['tipo'] == 'vinculo'}
        
        print(f"🔗 Dibujando {len(vinculos_tramos)} vínculos...")
        
        for tramo_id, tramo in vinculos_tramos.items():
            if tramo['nodo_inicio'] in nodes and tramo['nodo_fin'] in nodes:
                inicio = nodes[tramo['nodo_inicio']]
                fin = nodes[tramo['nodo_fin']]
                
                self._dibujar_linea(ax, inicio, fin, self.colores['vinculo'], linewidth=2, linestyle='--')
    
    def _dibujar_crucetas_mensulas(self, ax, nodes, tramos):
        """Dibuja crucetas y ménsulas"""
        elementos_tramos = {k: v for k, v in tramos.items() if v['tipo'] in ['cruceta', 'mensula']}
        
        print(f"📐 Dibujando {len(elementos_tramos)} crucetas/ménsulas...")
        
        for tramo_id, tramo in elementos_tramos.items():
            if tramo['nodo_inicio'] in nodes and tramo['nodo_fin'] in nodes:
                inicio = nodes[tramo['nodo_inicio']]
                fin = nodes[tramo['nodo_fin']]
                
                if tramo['tipo'] == 'cruceta':
                    color = self.colores['cruceta']
                    linewidth = 3
                    linestyle = '-'
                else:
                    color = self.colores['mensula'] 
                    linewidth = 2
                    linestyle = '-.'
                
                self._dibujar_linea(ax, inicio, fin, color, linewidth=linewidth, linestyle=linestyle)
    
    def _dibujar_puntos_amarre(self, ax, nodes):
        """Dibuja puntos de amarre y cables"""
        # Buscar nodos de conductores y guardia
        conductores = {k: v for k, v in nodes.items() if k.startswith(('C1_', 'C2_', 'C3_'))}
        guardias = {k: v for k, v in nodes.items() if k.startswith('HG')}
        tops = {k: v for k, v in nodes.items() if k.startswith('TOP')}
        
        print(f"🔌 Dibujando {len(conductores)} conductores, {len(guardias)} guardias, {len(tops)} tops...")
        
        # Dibujar puntos de amarre de conductores
        for nombre, coords in conductores.items():
            ax.scatter(*coords, color=self.colores['conductor'], s=120, marker='o', 
                      edgecolors='white', linewidth=2, 
                      label='Conductor' if nombre == 'C1_L' else "")
        
        # Dibujar puntos de amarre de guardia
        for nombre, coords in guardias.items():
            ax.scatter(*coords, color=self.colores['guardia'], s=120, marker='s',
                      edgecolors='white', linewidth=2, 
                      label='Guardia' if nombre == 'HG1' else "")
        
        # Dibujar puntos TOP
        for nombre, coords in tops.items():
            ax.scatter(*coords, color=self.colores['top'], s=100, marker='^',
                      edgecolors='white', linewidth=2, 
                      label='Top estructura' if nombre == 'TOP' else "")
        
        # Dibujar líneas de cables desde postes hasta puntos de amarre
        self._dibujar_cables_desde_postes(ax, nodes)
    
    def _dibujar_cables_desde_postes(self, ax, nodes):
        """Dibuja líneas representando cables desde postes hasta puntos de amarre"""
        # Obtener postes (nodos que terminan en _CIMA)
        postes_cima = {k: v for k, v in nodes.items() if k.endswith('_CIMA')}
        
        # Para cada punto de amarre de conductor o guardia, encontrar poste más cercano y dibujar línea
        for nombre, coords_amarre in nodes.items():
            if nombre.startswith(('C1_', 'C2_', 'C3_', 'HG')) and not nombre.endswith(('_INICIO', '_FIN')):
                # Encontrar poste más cercano en el plano XY
                poste_cercano = None
                min_dist = float('inf')
                
                for poste_nombre, coords_poste in postes_cima.items():
                    dist = math.sqrt((coords_amarre[0] - coords_poste[0])**2 + 
                                   (coords_amarre[1] - coords_poste[1])**2)
                    if dist < min_dist:
                        min_dist = dist
                        poste_cercano = coords_poste
                
                if poste_cercano is not None:
                    color = self.colores['conductor'] if nombre.startswith(('C1_', 'C2_', 'C3_')) else self.colores['guardia']
                    # Dibujar línea desde poste hasta punto de amarre
                    self._dibujar_linea(ax, poste_cercano, coords_amarre, color, linewidth=1.5, linestyle=':',
                                      alpha=0.6)
    
    def _dibujar_linea(self, ax, inicio, fin, color, linewidth=2, linestyle='-', alpha=1.0):
        """Dibuja una línea simple en 3D"""
        x = [inicio[0], fin[0]]
        y = [inicio[1], fin[1]] 
        z = [inicio[2], fin[2]]
        ax.plot(x, y, z, color=color, linewidth=linewidth, linestyle=linestyle, alpha=alpha)
    
    def _configurar_visualizacion_corregida(self, ax, nodes, geometria, elev, azim):
        """Configura la visualización con escala corregida y proporciones reales"""
        
        # Calcular límites de los datos
        coords = list(nodes.values())
        x_vals = [c[0] for c in coords]
        y_vals = [c[1] for c in coords]
        z_vals = [c[2] for c in coords]
        
        x_min, x_max = min(x_vals), max(x_vals)
        y_min, y_max = min(y_vals), max(y_vals)
        z_min, z_max = min(z_vals), max(z_vals)
        
        # Calcular dimensiones
        dx = x_max - x_min
        dy = y_max - y_min
        dz = z_max - z_min
        
        print(f"📐 Dimensiones de la estructura:")
        print(f"   X: {dx:.1f}m, Y: {dy:.1f}m, Z: {dz:.1f}m")
        print(f"   Rango X: [{x_min:.1f}, {x_max:.1f}]")
        print(f"   Rango Y: [{y_min:.1f}, {y_max:.1f}]") 
        print(f"   Rango Z: [{z_min:.1f}, {z_max:.1f}]")
        
        # Determinar límites de visualización
        if dx == 0 and dy == 0:
            # Estructura muy compacta, usar límites mínimos
            x_center, y_center = 0, 0
            max_horizontal = 5  # 5m mínimo
        else:
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            max_horizontal = max(dx, dy, 5)  # Al menos 5m
        
        # Añadir márgenes
        margen_horizontal = max_horizontal * 0.3
        margen_vertical = dz * 0.2
        
        # Establecer límites
        ax.set_xlim(x_center - max_horizontal/2 - margen_horizontal, 
                   x_center + max_horizontal/2 + margen_horizontal)
        ax.set_ylim(y_center - max_horizontal/2 - margen_horizontal, 
                   y_center + max_horizontal/2 + margen_horizontal)
        ax.set_zlim(0, z_max + margen_vertical)  # El suelo está en z=0
        
        # Configurar etiquetas
        ax.set_xlabel('X [m]', fontweight='bold', fontsize=10, labelpad=10)
        ax.set_ylabel('Y [m]', fontweight='bold', fontsize=10, labelpad=10)
        ax.set_zlabel('Z [m]', fontweight='bold', fontsize=10, labelpad=10)
        
        # Título principal
        titulo_principal = f"ESTRUCTURA 3D - {self.estructura.tension_nominal}kV"
        plt.title(titulo_principal, fontsize=14, fontweight='bold', pad=20)
        
        # Subtítulo con configuración
        config_text = f"{geometria['n_postes']} POSTE{'S' if geometria['n_postes'] > 1 else ''} - {geometria['orientacion']} - Altura: {geometria['Ht']:.1f}m"
        ax.text2D(0.5, 0.95, config_text, transform=ax.transAxes, fontsize=11, 
                 ha='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        # Leyenda
        self._crear_leyenda(ax)
        
        # Información técnica
        self._agregar_info_tecnica(ax, geometria)
        
        # Cuadrícula
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Configurar vista
        ax.view_init(elev=elev, azim=azim)
        
        # Forzar relación de aspecto igual
        self._forzar_proporcion_3d(ax)
        
        plt.tight_layout()
    
    def _crear_leyenda(self, ax):
        """Crea una leyenda clara y organizada"""
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color=self.colores['poste'], lw=4, label='Postes'),
            Line2D([0], [0], color=self.colores['vinculo'], lw=2, linestyle='--', label='Vínculos'),
            Line2D([0], [0], color=self.colores['cruceta'], lw=3, label='Crucetas'),
            Line2D([0], [0], color=self.colores['mensula'], lw=2, linestyle='-.', label='Ménsulas'),
            Line2D([0], [0], color=self.colores['conductor'], lw=1.5, linestyle=':', label='Cables conductor'),
            Line2D([0], [0], color=self.colores['guardia'], lw=1.5, linestyle=':', label='Cable guardia'),
        ]
        
        # Agregar marcadores para puntos
        from matplotlib.patches import Patch
        legend_elements.extend([
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colores['conductor'], 
                      markersize=8, label='Amarre conductor'),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=self.colores['guardia'], 
                      markersize=8, label='Amarre guardia'),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor=self.colores['top'], 
                      markersize=8, label='Top estructura'),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=self.colores['poste'], 
                      markersize=8, label='Base poste'),
        ])
        
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1),
                 framealpha=0.95, fontsize=9, ncol=2)
    
    def _agregar_info_tecnica(self, ax, geometria):
        """Agrega información técnica al gráfico"""
        info_text = f"""Configuración:
• Postes: {geometria['n_postes']} {geometria['orientacion']}
• Altura total: {geometria['Ht']:.1f}m
• Altura libre: {geometria['Hl']:.1f}m
• Diámetro cima: {geometria['dc']:.3f}m
• Inclinación: 5.5%"""

        ax.text2D(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.9),
                 verticalalignment='top')
    
    def _forzar_proporcion_3d(self, ax):
        """
        Fuerza una relación de aspecto igual en 3D
        """
        # Obtener límites actuales
        x_limits = ax.get_xlim3d()
        y_limits = ax.get_ylim3d()
        z_limits = ax.get_zlim3d()
        
        x_range = x_limits[1] - x_limits[0]
        y_range = y_limits[1] - y_limits[0]
        z_range = z_limits[1] - z_limits[0]
        
        # Usar el rango más grande para normalizar
        max_range = max(x_range, y_range, z_range)
        
        # Calcular nuevos límites centrados
        x_center = (x_limits[1] + x_limits[0]) / 2
        y_center = (y_limits[1] + y_limits[0]) / 2
        z_center = (z_limits[1] + z_limits[0]) / 2
        
        # Aplicar nuevos límites
        ax.set_xlim3d([x_center - max_range/2, x_center + max_range/2])
        ax.set_ylim3d([y_center - max_range/2, y_center + max_range/2])
        ax.set_zlim3d([z_center - max_range/2, z_center + max_range/2])