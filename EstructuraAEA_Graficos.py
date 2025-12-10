# EstructuraAEA_Graficos.py
import matplotlib.pyplot as plt
import numpy as np
import math

class EstructuraAEA_Graficos:
    """
    Clase especializada en visualización de la estructura según norma AEA
    Incluye gráficos de estructura, cabezal, diagramas polares y de barras
    """
    
    # Configuración de colores para visualización
    COLORES = {
        'conductor': '#1f77b4', 'guardia': '#2ca02c', 'poste': '#000000', 
        'cadena': "#717170", 'conductor_end': 'red', 'circulo': 'gray',
        'apantallamiento': '#84FF6B', 'texto_verde': '#006400',
        'dhg_circulo': 'gray', 'terreno': '#8B4513'
    }
    
    def __init__(self, geometria, mecanica=None):
        """
        Inicializa el módulo de gráficos con referencia a geometría y mecánica
        
        Args:
            geometria (EstructuraAEA_Geometria): Instancia de la clase de geometría
            mecanica (EstructuraAEA_Mecanica, optional): Instancia de la clase de mecánica
        """
        self.geometria = geometria
        self.mecanica = mecanica
        
        print(f"✅ ESTRUCTURA_AEA GRÁFICOS CREADA")
    
    def graficar_estructura(self, zoom_cabezal=0.95, titulo_reemplazo=None):
        """Grafica la estructura completa con la nueva lógica de tramos"""
        print(f"\n🎨 GENERANDO GRÁFICO DE ESTRUCTURA...")
        
        plt.figure(figsize=(8, 12))
        
        # Determinar título
        tipo_estructura_titulo = titulo_reemplazo if titulo_reemplazo else self.geometria.tipo_estructura
        
        # 1. TERRA
        plt.axhline(y=0, color=self.COLORES['terreno'], linewidth=3, alpha=0.7, label='Nivel del terreno')
        
        # 2. RECOLECTAR NODOS PARA DIBUJO
        # Recolectar nodos de estructura (centrados en x=0)
        nodos_estructura = []
        # Recolectar nodos de conductor por altura
        conductores_por_altura = {}
        # Recolectar nodos de guardia
        nodos_guardia = []
        
        for nombre, coordenadas in self.geometria.nodes_key.items():
            x, y, z = coordenadas
            
            # Solo plano XZ (y ≈ 0)
            if abs(y) > 0.001:
                continue
                
            # 2.1 Nodos de estructura (x=0 y no son conductores ni guardias)
            if abs(x) < 0.001 and not nombre.startswith(('C1_', 'C2_', 'C3_', 'HG')):
                nodos_estructura.append((z, nombre, coordenadas))
            
            # 2.2 Nodos de conductor
            elif nombre.startswith(('C1_', 'C2_', 'C3_')):
                if z not in conductores_por_altura:
                    conductores_por_altura[z] = []
                conductores_por_altura[z].append((x, nombre, coordenadas))
            
            # 2.3 Nodos de guardia
            elif nombre.startswith('HG'):
                nodos_guardia.append((x, nombre, coordenadas))
        
        # 3. DIBUJAR LÍNEA VERTICAL DE ESTRUCTURA
        # Ordenar nodos de estructura por altura
        nodos_estructura.sort(key=lambda x: x[0])
        
        if len(nodos_estructura) >= 2:
            for i in range(len(nodos_estructura)-1):
                z1, nombre1, coord1 = nodos_estructura[i]
                z2, nombre2, coord2 = nodos_estructura[i+1]
                plt.plot([0, 0], [z1, z2], color=self.COLORES['poste'], linewidth=4, 
                        label='Estructura' if i == 0 else "")
        
        # 4. DIBUJAR MENSULAS/CRUCETAS DE CONDUCTORES
        for altura, conductores in conductores_por_altura.items():
            # Buscar nodo CROSS correspondiente (más cercano en altura)
            cross_node = None
            min_diff = float('inf')
            
            for nombre, coordenadas in self.geometria.nodes_key.items():
                if "CROSS" in nombre:
                    x_cross, y_cross, z_cross = coordenadas
                    diff = abs(z_cross - altura)
                    if diff < min_diff:
                        min_diff = diff
                        cross_node = (nombre, coordenadas)
            
            if cross_node:
                cross_nombre, cross_coord = cross_node
                x_cross, y_cross, z_cross = cross_coord
                
                # Agrupar conductores por lado (izquierdo/centro/derecho)
                conductores_x = [c[0] for c in conductores]
                
                # Determinar si es cruceta (conductores a ambos lados del poste)
                hay_izq = any(x < 0 for x in conductores_x)
                hay_der = any(x > 0 for x in conductores_x)
                
                if hay_izq and hay_der:
                    # Cruceta: línea horizontal completa entre el conductor más izquierdo y el más derecho
                    x_min = min(conductores_x)
                    x_max = max(conductores_x)
                    plt.plot([x_min, x_max], [altura, altura], 
                            color=self.COLORES['poste'], linewidth=3, alpha=0.8,
                            label='Cruceta' if altura == min(conductores_por_altura.keys()) else "")
                    
                    # También dibujar conexiones verticales al CROSS si no están en la misma altura
                    if abs(z_cross - altura) > 0.01:
                        for x_cond, nombre_cond, coord_cond in conductores:
                            plt.plot([x_cond, x_cond], [z_cross, altura], 
                                    color=self.COLORES['poste'], linewidth=2, alpha=0.6, linestyle=':')
                else:
                    # Ménsula: cada conductor se conecta individualmente al CROSS
                    for x_cond, nombre_cond, coord_cond in conductores:
                        plt.plot([x_cross, x_cond], [z_cross, altura], 
                                color=self.COLORES['poste'], linewidth=3, alpha=0.8,
                                label='Ménsula' if altura == min(conductores_por_altura.keys()) else "")
        
        # 5. DIBUJAR MENSULAS/CRUCETAS DE GUARDIAS
        # Verificar si existe TOP
        if "TOP" in self.geometria.nodes_key:
            x_top, y_top, z_top = self.geometria.nodes_key["TOP"]
            
            if nodos_guardia:
                # Determinar si es cruceta o ménsula de guardia
                guardias_x = [g[0] for g in nodos_guardia]
                hay_izq = any(x < 0 for x in guardias_x)
                hay_der = any(x > 0 for x in guardias_x)
                
                if hay_izq and hay_der:
                    # Cruceta guardia: línea horizontal completa
                    x_min = min(guardias_x)
                    x_max = max(guardias_x)
                    plt.plot([x_min, x_max], [z_top, z_top], 
                            color=self.COLORES['poste'], linewidth=3, alpha=0.8,
                            label='Cruceta guardia')
                    
                    # Conexiones verticales a TOP
                    for x_hg, nombre_hg, coord_hg in nodos_guardia:
                        z_hg = coord_hg[2]
                        if abs(z_hg - z_top) > 0.01:
                            plt.plot([x_hg, x_hg], [z_top, z_hg], 
                                    color=self.COLORES['poste'], linewidth=2, alpha=0.6, linestyle=':')
                else:
                    # Ménsula guardia: cada guardia se conecta individualmente
                    for x_hg, nombre_hg, coord_hg in nodos_guardia:
                        z_hg = coord_hg[2]
                        plt.plot([x_top, x_hg], [z_top, z_hg], 
                                color=self.COLORES['poste'], linewidth=3, alpha=0.8,
                                label='Ménsula guardia' if x_hg == nodos_guardia[0][0] else "")
        else:
            # No hay TOP (guardia centrado o no hay guardias)
            if nodos_guardia:
                # Verificar si hay guardia centrado
                for x_hg, nombre_hg, coord_hg in nodos_guardia:
                    if abs(x_hg) < 0.001:
                        print(f"   ℹ️  Guardia centrado en (0, {coord_hg[2]:.2f}) - sin línea horizontal")
        
        # 6. DIBUJAR PUNTOS DE NODOS
        for nombre, coordenadas in self.geometria.nodes_key.items():
            x, y, z = coordenadas
            
            if abs(y) > 0.001:  # Solo plano XZ
                continue
                
            # Nodos de conductor
            if nombre.startswith(('C1_', 'C2_', 'C3_')):
                plt.scatter(x, z, color=self.COLORES['conductor'], s=120, marker='o', 
                        edgecolors='white', linewidth=1.5, zorder=5,
                        label='Amarre de Conductores' if nombre == 'C1_L' else "")
            
            # Nodos de guardia
            elif nombre.startswith('HG'):
                plt.scatter(x, z, color=self.COLORES['guardia'], s=120, marker='o', 
                        edgecolors='white', linewidth=1.5, zorder=5,
                        label='Cable guardia' if nombre == 'HG1' and 'HG1' in self.geometria.nodes_key else "")
            
            # Nodo base
            elif "BASE" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=150, marker='s', zorder=5, label='Base')
            
            # Nodo top
            elif "TOP" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=120, marker='^', zorder=5, label='Top estructura')
            
            # Nodos de cruce
            elif "CROSS" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=80, marker='o', zorder=5,
                        label='Cruce poste-ménsula' if nombre == 'CROSS_H1' else "")
            
            # Nodos generales
            elif nombre in ["V", "MEDIO"]:
                plt.scatter(x, z, color='gray', s=60, marker='.', zorder=4, alpha=0.5)
        
        # 7. CONFIGURAR EJES
        x_coords = [x for x, y, z in self.geometria.nodes_key.values()]
        z_coords = [z for x, y, z in self.geometria.nodes_key.values()]
        
        if x_coords and z_coords:
            x_range = max(x_coords) - min(x_coords) if x_coords else 10
            z_range = max(z_coords) - min(z_coords) if z_coords else 15
            max_range = max(x_range, z_range)
            margin = max_range * 0.15
            
            x_center = (max(x_coords) + min(x_coords)) / 2 if x_coords else 0
            z_center = (max(z_coords) + min(z_coords)) / 2 if z_coords else 0
            
            plt.xlim(x_center - max_range/2 - margin, x_center + max_range/2 + margin)
            plt.ylim(-1, z_center + max_range/2 + margin)
        
        # 8. ETIQUETAS Y TÍTULO
        plt.xlabel('Distancia Horizontal X [m]', fontsize=11, fontweight='bold')
        plt.ylabel('Altura Z [m]', fontsize=11, fontweight='bold')
        plt.title(f'ESTRUCTURA {self.geometria.tension_nominal}kV - {self.geometria.zona_estructura.upper()} - {tipo_estructura_titulo.upper()} - {self.geometria.terna} Terna', 
                fontsize=12, fontweight='bold', pad=15)
        
        # 9. LEYENDA
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=self.COLORES['conductor'], edgecolor='white', linewidth=1.5, label='Amarre de Conductores'),
            Patch(facecolor=self.COLORES['guardia'], edgecolor='white', linewidth=1.5, label='Cable guardia'),
            Patch(facecolor=self.COLORES['poste'], label='Estructura'),
            plt.Line2D([0], [0], color=self.COLORES['poste'], linewidth=3, alpha=0.8, label='Ménsula/Cruceta'),
            plt.Line2D([0], [0], color=self.COLORES['poste'], linewidth=3, alpha=0.8, linestyle=':', label='Conexión vertical')
        ]
        
        # Filtrar elementos duplicados en la leyenda
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), loc='lower right', framealpha=0.95)
        
        # 10. CUADÍCULA Y ASPECTO
        plt.gca().set_aspect('equal', adjustable='box')
        plt.grid(True, alpha=0.15, linestyle='-', linewidth=0.5)
        
        # 11. INFORMACIÓN ADICIONAL
        altura_total = self.geometria.dimensiones.get('altura_total', 0)
        info_text = f'H Libre: {altura_total:.2f} m\nMénsula: {self.geometria.dimensiones.get("lmen", 0):.1f} m\nTipo: {tipo_estructura_titulo}\nTerna: {self.geometria.terna}\nCables guardia: {self.geometria.cant_hg}'
        plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, fontsize=9, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8), verticalalignment='top')
        
        plt.text(0.98, 0.85, f'Altura Libre Total: {altura_total:.2f} m', transform=plt.gca().transAxes, 
                fontsize=10, fontweight='bold', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.9), 
                horizontalalignment='right', verticalalignment='top')
        
        plt.tight_layout()
        plt.show()
        
        print(f"✅ Gráfico de estructura generado")
    
    def _dibujar_cadena(self, nodo_amarre, angulo=0, etiqueta=None, radio=None, color_circulo='gray'):
        """Dibuja una cadena de aisladores con declinación opcional y círculo de distancia"""
        if nodo_amarre not in self.geometria.nodes_key:
            return None, None

        x_amarre, y_amarre, z_amarre = self.geometria.nodes_key[nodo_amarre]
        ang_rad = math.radians(angulo)
        x_conductor = x_amarre + self.geometria.lk * math.sin(ang_rad)
        z_conductor = z_amarre - self.geometria.lk * math.cos(ang_rad)

        # Dibujar la cadena (línea)
        label_cadena = 'Cadena' if 'C1_L' in nodo_amarre and angulo > 0 else ""
        plt.plot([x_amarre, x_conductor], [z_amarre, z_conductor], color=self.COLORES['cadena'], 
                linewidth=2, label=label_cadena)

        # Dibujar el extremo del conductor
        label_conductor = 'Extremo conductor' if 'C1_L' in nodo_amarre and angulo > 0 else ""
        plt.scatter(x_conductor, z_conductor, color=self.COLORES['conductor_end'], s=80, marker='o', 
                edgecolors='white', linewidth=1.5, zorder=5, label=label_conductor)

        # Dibujar círculo de distancia si se especifica
        if radio and radio > 0:
            label_circulo = etiqueta if 'C1_L' in nodo_amarre and angulo > 0 else ""
            plt.gca().add_patch(plt.Circle((x_conductor, z_conductor), radio, color=color_circulo, 
                                        fill=False, linestyle='--', linewidth=1.5, alpha=0.7,
                                        label=label_circulo))

            # Etiquetas de distancia
            if etiqueta == 's (fase-estructura)':
                plt.annotate(etiqueta, xy=(x_conductor, z_conductor - radio), xytext=(0, -8),
                            textcoords='offset points', fontsize=8, fontweight='bold', color=color_circulo, 
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8), 
                            horizontalalignment='center', verticalalignment='top')
                plt.annotate(f'{radio:.2f} m', xy=(x_conductor, z_conductor - radio), xytext=(0, -23),
                            textcoords='offset points', fontsize=8, fontweight='bold', color=color_circulo,
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8),
                            horizontalalignment='center', verticalalignment='top')
            else:
                offset_vertical = 0.017
                plt.annotate(etiqueta, xy=(x_conductor + radio/2, z_conductor + offset_vertical), 
                            xytext=(5, 2), textcoords='offset points', fontsize=8, fontweight='bold', 
                            color=color_circulo, 
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8), 
                            verticalalignment='bottom')
                plt.annotate(f'{radio:.2f} m', xy=(x_conductor + radio/2, z_conductor - offset_vertical), 
                            xytext=(5, -2), textcoords='offset points', fontsize=8, fontweight='bold', 
                            color=color_circulo,
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8), 
                            verticalalignment='top')

        return x_conductor, z_conductor
    

    def graficar_cabezal(self, zoom_cabezal=0.7, titulo_reemplazo=None):
        """Grafica el cabezal usando los parámetros calculados durante el dimensionamiento"""
        print(f"\n🎨 GENERANDO GRÁFICO DE CABEZAL...")
        
        plt.figure(figsize=(12, 10))
        
        # Determinar título
        tipo_estructura_titulo = titulo_reemplazo if titulo_reemplazo else self.geometria.tipo_estructura
        
        # 1. OBTENER PARÁMETROS DEL CABEZAL
        if self.geometria.parametros_cabezal is None:
            print("❌ No se han calculado los parámetros del cabezal. Ejecutar dimensionar_unifilar primero.")
            return
        
        theta_max = self.geometria.dimensiones.get('theta_max', 0.0)
        D_fases = self.geometria.dimensiones.get('D_fases', 0.0)
        s_estructura = self.geometria.dimensiones.get('s_estructura', 0.0)
        Dhg = self.geometria.dimensiones.get('Dhg', 0.0)
        altura_total = self.geometria.dimensiones.get('altura_total', 0)
        
        # 2. DIBUJAR POSTE Y MENSULAS - NUEVA LÓGICA
        nodos_estructura = []
        conductores_por_altura = {}
        nodos_guardia = []
        
        for nombre, coordenadas in self.geometria.nodes_key.items():
            x, y, z = coordenadas
            
            if abs(y) > 0.001:
                continue
                
            if abs(x) < 0.001 and not nombre.startswith(('C1_', 'C2_', 'C3_', 'HG')):
                nodos_estructura.append((z, nombre, coordenadas))
            
            elif nombre.startswith(('C1_', 'C2_', 'C3_')):
                if z not in conductores_por_altura:
                    conductores_por_altura[z] = []
                conductores_por_altura[z].append((x, nombre, coordenadas))
            
            elif nombre.startswith('HG'):
                nodos_guardia.append((x, nombre, coordenadas))
        
        # 2.1 DIBUJAR LÍNEA VERTICAL DEL POSTE
        if nodos_estructura:
            nodos_estructura.sort(key=lambda x: x[0])
            z_min = min([n[0] for n in nodos_estructura])
            z_max = max([n[0] for n in nodos_estructura])
            plt.plot([0, 0], [z_min, z_max], color=self.COLORES['poste'], linewidth=4)
        
        # 2.2 DIBUJAR MENSULAS/CRUCETAS DE CONDUCTORES
        for altura, conductores in conductores_por_altura.items():
            cross_node = None
            min_diff = float('inf')
            
            for nombre, coordenadas in self.geometria.nodes_key.items():
                if "CROSS" in nombre:
                    x_cross, y_cross, z_cross = coordenadas
                    diff = abs(z_cross - altura)
                    if diff < min_diff:
                        min_diff = diff
                        cross_node = (nombre, coordenadas)
            
            if cross_node:
                cross_nombre, cross_coord = cross_node
                x_cross, y_cross, z_cross = cross_coord
                
                conductores_x = [c[0] for c in conductores]
                hay_izq = any(x < 0 for x in conductores_x)
                hay_der = any(x > 0 for x in conductores_x)
                
                if hay_izq and hay_der:
                    x_min = min(conductores_x)
                    x_max = max(conductores_x)
                    plt.plot([x_min, x_max], [altura, altura], 
                            color=self.COLORES['poste'], linewidth=3, alpha=0.8)
                    
                    if abs(z_cross - altura) > 0.01:
                        for x_cond, nombre_cond, coord_cond in conductores:
                            plt.plot([x_cond, x_cond], [z_cross, altura], 
                                    color=self.COLORES['poste'], linewidth=2, alpha=0.6, linestyle=':')
                else:
                    for x_cond, nombre_cond, coord_cond in conductores:
                        plt.plot([x_cross, x_cond], [z_cross, altura], 
                                color=self.COLORES['poste'], linewidth=3, alpha=0.8)
        
        # 2.3 DIBUJAR MENSULAS/CRUCETAS DE GUARDIAS
        if "TOP" in self.geometria.nodes_key:
            x_top, y_top, z_top = self.geometria.nodes_key["TOP"]
            
            if nodos_guardia:
                guardias_x = [g[0] for g in nodos_guardia]
                hay_izq = any(x < 0 for x in guardias_x)
                hay_der = any(x > 0 for x in guardias_x)
                
                if hay_izq and hay_der:
                    x_min = min(guardias_x)
                    x_max = max(guardias_x)
                    plt.plot([x_min, x_max], [z_top, z_top], 
                            color=self.COLORES['poste'], linewidth=3, alpha=0.8)
                    
                    for x_hg, nombre_hg, coord_hg in nodos_guardia:
                        z_hg = coord_hg[2]
                        if abs(z_hg - z_top) > 0.01:
                            plt.plot([x_hg, x_hg], [z_top, z_hg], 
                                    color=self.COLORES['poste'], linewidth=2, alpha=0.6, linestyle=':')
                else:
                    for x_hg, nombre_hg, coord_hg in nodos_guardia:
                        z_hg = coord_hg[2]
                        plt.plot([x_top, x_hg], [z_top, z_hg], 
                                color=self.COLORES['poste'], linewidth=3, alpha=0.8)
        
        # 3. APANTALLAMIENTO
        if nodos_guardia:
            h_guardia = self.geometria.dimensiones.get('hhg', 0)
            h1a = self.geometria.dimensiones.get('h1a', 0)
            h_terminacion = h1a - self.geometria.lk
            angulo_apant = self.geometria.ang_apantallamiento
            
            if len(nodos_guardia) == 1:
                x_hg = nodos_guardia[0][0]
                
                if abs(x_hg) > 0.001:
                    x_ext = x_hg - (h_guardia - h_terminacion) * math.tan(math.radians(angulo_apant))
                    
                    plt.plot([x_hg, x_ext], [h_guardia, h_terminacion], 
                            color=self.COLORES['apantallamiento'],
                            linestyle='--', alpha=0.7, linewidth=1.5)
            else:
                guardias_x = [g[0] for g in nodos_guardia]
                x_hg_izq = min(guardias_x)
                x_hg_der = max(guardias_x)
                
                x_izq_extremo = x_hg_izq - (h_guardia - h_terminacion) * math.tan(math.radians(angulo_apant))
                x_der_extremo = x_hg_der + (h_guardia - h_terminacion) * math.tan(math.radians(angulo_apant))
                
                for x_hg, x_ext in [(x_hg_izq, x_izq_extremo), (x_hg_der, x_der_extremo)]:
                    plt.plot([x_hg, x_ext], [h_guardia, h_terminacion], 
                            color=self.COLORES['apantallamiento'],
                            linestyle='--', alpha=0.7, linewidth=1.5)
                
                # Rellenar zona protegida
                x_fill = [x_izq_extremo, x_hg_izq, x_hg_der, x_der_extremo]
                z_fill = [h_terminacion, h_guardia, h_guardia, h_terminacion]
                plt.fill(x_fill, z_fill, color=self.COLORES['apantallamiento'], alpha=0.1)
        
        # 4. DIBUJAR CADENAS CON DECLINACIÓN
        puntos_conductor = {}
        
        for altura, conductores in conductores_por_altura.items():
            for x_cond, nombre_cond, coord_cond in conductores:
                angulo_cadena = theta_max if (nombre_cond.endswith('_L') and "C1" in nombre_cond) else 0.0
                
                if nombre_cond in self.geometria.nodes_key:
                    x_amarre, y_amarre, z_amarre = coord_cond
                    ang_rad = math.radians(angulo_cadena)
                    x_conductor = x_amarre + self.geometria.lk * math.sin(ang_rad)
                    z_conductor = z_amarre - self.geometria.lk * math.cos(ang_rad)
                    
                    # Dibujar cadena
                    plt.plot([x_amarre, x_conductor], [z_amarre, z_conductor], 
                            color=self.COLORES['cadena'], linewidth=2)
                    
                    # Dibujar extremo del conductor
                    plt.scatter(x_conductor, z_conductor, color=self.COLORES['conductor_end'], 
                            s=80, marker='o', edgecolors='white', linewidth=1.5, zorder=5)
                    
                    puntos_conductor[nombre_cond] = (x_conductor, z_conductor)
                    
                    # Dibujar círculos de distancia
                    if nombre_cond.endswith('_L') and "C1" in nombre_cond:
                        plt.gca().add_patch(plt.Circle((x_conductor, z_conductor), s_estructura, 
                                                    color=self.COLORES['circulo'], fill=False, 
                                                    linestyle='--', linewidth=1.5, alpha=0.7))
                        
                        plt.annotate('s (fase-estructura)', xy=(x_conductor, z_conductor - s_estructura), 
                                    xytext=(0, -8), textcoords='offset points', fontsize=8, fontweight='bold',
                                    color=self.COLORES['circulo'], 
                                    bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8), 
                                    horizontalalignment='center', verticalalignment='top')
                        plt.annotate(f'{s_estructura:.2f} m', xy=(x_conductor, z_conductor - s_estructura), 
                                    xytext=(0, -23), textcoords='offset points', fontsize=8, fontweight='bold',
                                    color=self.COLORES['circulo'],
                                    bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8),
                                    horizontalalignment='center', verticalalignment='top')
                    
                    elif nombre_cond.endswith('_R') and "C2" in nombre_cond:
                        plt.gca().add_patch(plt.Circle((x_conductor, z_conductor), D_fases, 
                                                    color=self.COLORES['circulo'], fill=False, 
                                                    linestyle='--', linewidth=1.5, alpha=0.7))
                    
                    elif nombre_cond.endswith('_L') and "C3" in nombre_cond:
                        plt.gca().add_patch(plt.Circle((x_conductor, z_conductor), Dhg, 
                                                    color=self.COLORES['dhg_circulo'], fill=False, 
                                                    linestyle='--', linewidth=1.5, alpha=0.7))
        
        # 5. DIBUJAR NODOS - CON CÍRCULOS AZULES EN CONDUCTORES
        for nombre, coordenadas in self.geometria.nodes_key.items():
            x, y, z = coordenadas
            
            if abs(y) > 0.001:
                continue
                
            # Nodos de cruce - SIN ETIQUETA
            if "CROSS" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=80, marker='o', zorder=5)
            
            # Nodos de conductor - CON CÍRCULO AZUL
            elif nombre.startswith(('C1_', 'C2_', 'C3_')):
                plt.scatter(x, z, color=self.COLORES['conductor'], s=100, marker='o', 
                        edgecolors='white', linewidth=1.5, zorder=5)
            
            # Nodos de guardia
            elif nombre.startswith('HG'):
                plt.scatter(x, z, color=self.COLORES['guardia'], s=100, marker='o', 
                        edgecolors='white', linewidth=1.5, zorder=5)
            
            # Nodo top - SIN ETIQUETA
            elif "TOP" in nombre:
                plt.scatter(x, z, color=self.COLORES['poste'], s=120, marker='^', zorder=5)
        
        # 6. CONFIGURACIÓN DE EJES
        h1a = self.geometria.dimensiones.get('h1a', 0)
        hhg = self.geometria.dimensiones.get('hhg', 0)
        
        z_min_cabezal = h1a - self.geometria.lk - D_fases
        z_max_cabezal = hhg + D_fases
        
        x_center = 0
        x_range_cabezal = 3 * D_fases
        
        zoom_factor = zoom_cabezal if zoom_cabezal > 0 else 0.7
        plt.xlim(x_center - x_range_cabezal/2 * zoom_factor, x_center + x_range_cabezal/2 * zoom_factor)
        plt.ylim(z_min_cabezal, z_max_cabezal)
        
        # 7. CUADRÍCULA
        x_min, x_max = plt.xlim()
        z_min, z_max = plt.ylim()
        x_ticks = np.arange(np.floor(x_min * 10) / 10, np.ceil(x_max * 10) / 10 + 0.1, 0.1)
        z_ticks = np.arange(np.floor(z_min * 10) / 10, np.ceil(z_max * 10) / 10 + 0.1, 0.1)
        plt.gca().set_xticks(x_ticks, minor=True)
        plt.gca().set_yticks(z_ticks, minor=True)
        plt.grid(which='minor', color='lightgray', linestyle='-', linewidth=0.4, alpha=0.5)
        plt.grid(which='major', alpha=0.2, linestyle='-', linewidth=0.7)
        
        # 8. TÍTULOS Y ETIQUETAS
        plt.xlabel('Distancia Horizontal X [m]', fontsize=11, fontweight='bold')
        plt.ylabel('Altura Z [m]', fontsize=11, fontweight='bold')
        plt.title(f'CABEZAL DE ESTRUCTURA - DETALLE CADENAS Y DISTANCIAS', 
                fontsize=12, fontweight='bold', pad=15)
        
        terna_formato = "Doble Terna" if self.geometria.terna == "Doble" else "Simple Terna"
        plt.title(f'{self.geometria.tension_nominal}kV - {tipo_estructura_titulo.upper()} - {self.geometria.disposicion.upper()} - {terna_formato}', 
                fontsize=10, pad=10)
        
        # 9. LEYENDA SIMPLIFICADA - ABAJO DERECHA
        from matplotlib.patches import Patch
        leyenda = [
            Patch(facecolor=self.COLORES['conductor'], edgecolor='white', linewidth=1.5, label='Punto amarre'),
            Patch(facecolor=self.COLORES['conductor_end'], edgecolor='white', linewidth=1.5, label='Extremo conductor'),
            Patch(facecolor=self.COLORES['guardia'], edgecolor='white', linewidth=1.5, label='Cable guardia'),
            plt.Line2D([0], [0], color=self.COLORES['cadena'], linewidth=2, label='Cadena'),
            plt.Line2D([0], [0], color=self.COLORES['circulo'], linestyle='--', linewidth=1.5, label='D (entre fases)'),
            plt.Line2D([0], [0], color=self.COLORES['circulo'], linestyle='--', linewidth=1.5, label='s (fase-estructura)'),
            plt.Line2D([0], [0], color=self.COLORES['dhg_circulo'], linestyle='--', linewidth=1.5, label='Dhg (guardia-conductor)'),
        ]
        
        if nodos_guardia and (len(nodos_guardia) > 1 or (len(nodos_guardia) == 1 and abs(nodos_guardia[0][0]) > 0.001)):
            leyenda.append(
                plt.Line2D([0], [0], color=self.COLORES['apantallamiento'], linestyle='--', linewidth=1.5, 
                        label=f'Apantallamiento {self.geometria.ang_apantallamiento}°')
            )
        
        plt.legend(handles=leyenda, loc='lower right', framealpha=0.95)
        
        # 10. INFORMACIÓN TÉCNICA
        info_text = f'H libre: {altura_total:.2f} m\nMénsula: {self.geometria.dimensiones.get("lmen", 0):.2f} m\nTipo: {tipo_estructura_titulo}\nTerna: {self.geometria.terna}\nCables guardia: {self.geometria.cant_hg}'
        plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8), verticalalignment='top')
        
        plt.text(0.98, 0.85, f'Altura Libre: {altura_total:.2f} m', transform=plt.gca().transAxes, 
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.9), 
                horizontalalignment='right', verticalalignment='top')
        
        # Etiqueta theta
        if theta_max > 0 and 'C1_L' in puntos_conductor:
            x_med = (self.geometria.nodes_key['C1_L'][0] + puntos_conductor['C1_L'][0]) / 2
            z_med = (self.geometria.nodes_key['C1_L'][2] + puntos_conductor['C1_L'][1]) / 2
            plt.annotate(f'θ = {theta_max:.1f}°', xy=(x_med, z_med), xytext=(-20, 0), 
                        textcoords='offset points', fontsize=9, fontweight='bold', 
                        color=self.COLORES['cadena'],
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8), 
                        horizontalalignment='right', verticalalignment='center')
        
        plt.gca().set_aspect('equal', adjustable='box')
        plt.tight_layout()
        plt.show()
        
        print(f"✅ Gráfico de cabezal generado (theta_max: {theta_max:.1f}°)")


    def diagrama_polar_tiros(self, titulo=None):
        """
        Genera diagrama polar de tiros en cima
        """
        if self.mecanica is None or self.mecanica.df_reacciones is None:
            print("❌ No hay datos de reacciones. Ejecutar calcular_reacciones_tiros_cima primero.")
            return
        
        print(f"\n🎨 GENERANDO DIAGRAMA POLAR DE TIROS EN CIMA...")
        
        plt.figure(figsize=(10, 10))
        ax = plt.subplot(111, projection='polar')
        
        # Colores para hipótesis
        colores_hipotesis = {
            'A1': '#FF0000', 'A2': '#00FF00', 'A3': '#0000FF', 'A4': "#7A7A7A",
            'A5': '#FF00FF', 'B1': '#00FFFF', 'B2': '#FF8000', 'C1': '#8000FF', 'C2': '#008000'
        }
        
        # Plotear cada hipótesis
        max_tiro = 0
        for hipotesis, datos in self.mecanica.df_reacciones.iterrows():
            # Extraer código corto
            codigo = hipotesis.split('_')[-2] if len(hipotesis.split('_')) >= 2 else hipotesis
            
            angulo_rad = math.radians(datos['Angulo_grados'])
            magnitud = datos['Tiro_resultante_daN']
            color = colores_hipotesis.get(codigo, '#000000')
            
            # Plotear vector
            ax.plot([0, angulo_rad], [0, magnitud], linewidth=2, color=color, 
                   label=f"{codigo}: {magnitud:.1f} daN", alpha=0.7)
            ax.plot(angulo_rad, magnitud, 'o', color=color, markersize=6)
            
            max_tiro = max(max_tiro, magnitud)
        
        # Configurar gráfico polar: 0° arriba (Norte), sentido horario
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        
        # Ajustar límites
        ax.set_ylim(0, max_tiro * 1.2)
        ax.grid(True, alpha=0.3)
        
        # Título
        titulo_grafico = titulo if titulo else f'DIAGRAMA POLAR DE TIROS EN LA CIMA\n{self.geometria.tension_nominal}kV - {self.geometria.tipo_estructura.upper()}'
        ax.set_title(titulo_grafico, fontsize=12, fontweight='bold', pad=20)
        
        # Leyenda arriba a la derecha
        ax.legend(loc='upper right', title="Hipótesis")
        
        plt.tight_layout()
        
        print(f"✅ Diagrama polar generado")
    
    def diagrama_barras_tiros(self, titulo=None, mostrar_c2=False):
        """
        Genera diagrama de barras comparativo de tiros en cima
        """
        if self.mecanica is None or self.mecanica.df_reacciones is None:
            print("❌ No hay datos de reacciones. Ejecutar calcular_reacciones_tiros_cima primero.")
            return
        
        print(f"\n📊 GENERANDO DIAGRAMA DE BARRAS DE TIROS...")
        
        plt.figure(figsize=(12, 6))
        
        # Preparar datos
        hipotesis_barras = []
        tiros_barras = []
        angulos_barras = []
        colores_barras = []
        
        colores_hipotesis = {
            'A1': '#FF0000', 'A2': '#00FF00', 'A3': '#0000FF', 'A4': "#7A7A7A",
            'A5': '#FF00FF', 'B1': '#00FFFF', 'B2': '#FF8000', 'C1': '#8000FF', 'C2': '#008000'
        }
        
        for hipotesis, datos in self.mecanica.df_reacciones.iterrows():
            codigo = hipotesis.split('_')[-2] if len(hipotesis.split('_')) >= 2 else hipotesis
            
            if codigo == 'C2' and not mostrar_c2:
                continue
            
            hipotesis_barras.append(codigo)
            tiros_barras.append(datos['Tiro_resultante_daN'])
            angulos_barras.append(datos['Angulo_grados'])
            colores_barras.append(colores_hipotesis.get(codigo, 'black'))
        
        # Crear gráfico de barras sin borde
        barras = plt.bar(hipotesis_barras, tiros_barras, color=colores_barras, alpha=0.7, edgecolor='none')
        
        # Configurar ejes y título primero
        plt.ylabel('Tiro Resultante [daN]', fontweight='bold', fontsize=11)
        plt.xlabel('Hipótesis de Carga', fontweight='bold', fontsize=11)
        
        titulo_grafico = titulo if titulo else f'COMPARACIÓN DE TIROS EN LA CIMA\n{self.geometria.tension_nominal}kV - {self.geometria.tipo_estructura.upper()}'
        plt.title(titulo_grafico, fontsize=12, fontweight='bold', pad=10)
        
        plt.ylim(0, max(tiros_barras) * 1.15)
        plt.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        
        # Añadir valores en la cima de las barras DESPUÉS de configurar ejes
        for barra, valor, angulo in zip(barras, tiros_barras, angulos_barras):
            height = barra.get_height()
            plt.text(barra.get_x() + barra.get_width()/2., height,
                    f'{valor:.1f} daN\n({angulo:.0f}°)', 
                    ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        plt.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.12)
        
        print(f"✅ Diagrama de barras generado")