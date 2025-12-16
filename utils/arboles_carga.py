"""Generador de Árboles de Carga 2D"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pathlib import Path
import hashlib
import json
from config.app_config import CACHE_DIR


def calcular_hash_estructura(estructura_dict):
    """Calcular hash MD5 de la estructura"""
    estructura_str = json.dumps(estructura_dict, sort_keys=True)
    return hashlib.md5(estructura_str.encode()).hexdigest()


def generar_arboles_carga(estructura_mecanica, estructura_actual, zoom=0.5, escala_flecha=1.8, 
                          grosor_linea=3.5, mostrar_nodos=True, fontsize_nodos=8, fontsize_flechas=9, mostrar_sismo=False):
    """
    Genera árboles de carga 2D para todas las hipótesis
    
    Args:
        estructura_mecanica: Objeto EstructuraAEA_Mecanica
        estructura_actual: Dict con parámetros de estructura
    
    Returns:
        dict: {
            'exito': bool,
            'mensaje': str,
            'imagenes': [{'hipotesis': str, 'ruta': Path}]
        }
    """
    try:
        # Verificar que existan los datos necesarios
        if not hasattr(estructura_mecanica, 'resultados_reacciones'):
            return {
                'exito': False,
                'mensaje': 'No hay datos de reacciones. Ejecute primero el Diseño Mecánico de Estructura.'
            }
        
        if not hasattr(estructura_mecanica, 'cargas_key'):
            return {
                'exito': False,
                'mensaje': 'No hay datos de cargas. Ejecute primero el Cálculo Mecánico de Cables.'
            }
        
        # Obtener datos
        nodes_key = estructura_mecanica.geometria.nodes_key
        cargas_key = estructura_mecanica.cargas_key
        resultados_reacciones = estructura_mecanica.resultados_reacciones
        
        # Calcular hash
        hash_estructura = calcular_hash_estructura(estructura_actual)
        titulo = estructura_actual.get('TITULO', 'estructura')
        
        # Calcular rangos de ejes
        rangos = calcular_rangos_ejes_2d(nodes_key, zoom)
        
        imagenes_generadas = []
        
        # Generar imagen para cada hipótesis
        for hipotesis_nombre, cargas_hipotesis in cargas_key.items():
            # Filtrar hipótesis C2 si mostrar_sismo es False
            if not mostrar_sismo and '_C2_' in hipotesis_nombre:
                continue
            
            # Verificar si hay cargas
            nodos_con_cargas = [nombre for nombre, carga in cargas_hipotesis.items() 
                               if any(val != 0 for val in carga)]
            
            if not nodos_con_cargas:
                continue
            
            # Obtener reacciones
            if hipotesis_nombre not in resultados_reacciones:
                continue
            
            datos_reacciones = resultados_reacciones[hipotesis_nombre]
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Dibujar estructura (todos los elementos en negro)
            dibujar_estructura_2d(ax, nodes_key, grosor_linea)
            
            # Dibujar flechas de cargas
            dibujar_flechas_2d(ax, cargas_hipotesis, nodes_key, rangos, escala_flecha, fontsize_flechas)
            
            # Panel de reacciones
            dibujar_panel_reacciones_2d(ax, datos_reacciones, rangos)
            
            # Etiquetas de nodos si está activado
            if mostrar_nodos:
                dibujar_etiquetas_nodos_2d(ax, nodos_con_cargas, nodes_key, fontsize_nodos)
            
            # Configurar ejes
            ax.set_xlim(rangos['x_min'], rangos['x_max'])
            ax.set_ylim(rangos['z_min'], rangos['z_max'])
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Z (m)')
            
            # Título mejorado: Hip. XX / Descripción / Tipo estructura
            codigo_hip = hipotesis_nombre.split('_')[-2] if '_' in hipotesis_nombre else hipotesis_nombre
            descripcion_hip = hipotesis_nombre.split('_')[-1] if '_' in hipotesis_nombre else ''
            tipo_estructura = estructura_actual.get('TIPO_ESTRUCTURA', '')
            
            titulo_grafico = f"Hip. {codigo_hip}\n{descripcion_hip}\n{tipo_estructura}"
            ax.set_title(titulo_grafico, fontsize=12, fontweight='bold')
            
            # Leyenda
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='red', label='Fuerza X Transversal'),
                Patch(facecolor='blue', label='Fuerza Z Vertical'),
                Patch(facecolor='green', label='Fuerza Y Longitudinal')
            ]
            ax.legend(handles=legend_elements, loc='upper right')
            
            # Guardar imagen (sanitizar nombre de archivo)
            titulo_sanitizado = titulo.replace('\n', '_').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            nombre_archivo = f"{titulo_sanitizado}.arbolcarga.{hash_estructura}.{hipotesis_nombre.replace(' ', '_')}.png"
            ruta_imagen = CACHE_DIR / nombre_archivo
            
            fig.savefig(ruta_imagen, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            imagenes_generadas.append({
                'hipotesis': hipotesis_nombre,
                'ruta': ruta_imagen,
                'nombre': nombre_archivo
            })
        
        if not imagenes_generadas:
            return {
                'exito': False,
                'mensaje': 'No se generaron imágenes. Verifique que existan cargas aplicadas.'
            }
        
        return {
            'exito': True,
            'mensaje': f'Se generaron {len(imagenes_generadas)} árboles de carga',
            'imagenes': imagenes_generadas
        }
        
    except Exception as e:
        return {
            'exito': False,
            'mensaje': f'Error generando árboles de carga: {str(e)}'
        }


def calcular_rangos_ejes_2d(nodes_key, zoom_factor):
    """Calcula rangos de ejes para visualización 2D"""
    x_coords = [coord[0] for coord in nodes_key.values()]
    z_coords = [coord[2] for coord in nodes_key.values()]
    
    z_max = max(z_coords)
    z_min = 0
    z_range = max(z_max * 1.05 - z_min, 10)
    
    x_min, x_max = min(x_coords), max(x_coords)
    x_range = x_max - x_min
    
    max_range = max(x_range, z_range) * zoom_factor
    margin = max_range * 0.1
    
    x_center = (x_max + x_min) / 2
    z_center = (z_max + z_min) / 2
    
    return {
        'x_min': x_center - max_range/2 - margin,
        'x_max': x_center + max_range/2 + margin,
        'z_min': z_min,
        'z_max': max(z_max * 1.2, max_range/2 + z_center),
        'x_center': x_center,
        'z_center': z_center,
        'max_range': max_range,
        'z_max_original': z_max
    }


def dibujar_estructura_2d(ax, nodes_key, linewidth):
    """Dibuja la estructura en 2D (plano XZ) usando la misma lógica que EstructuraAEA_Graficos"""
    
    # 1. RECOLECTAR NODOS POR TIPO
    nodos_estructura = []
    conductores_por_altura = {}
    nodos_guardia = []
    
    for nombre, coordenadas in nodes_key.items():
        x, y, z = coordenadas
        
        # Solo plano XZ (y ≈ 0)
        if abs(y) > 0.001:
            continue
        
        # Nodos de estructura (x=0 y no son conductores ni guardias)
        if abs(x) < 0.001 and not nombre.startswith(('C1', 'C2', 'C3', 'HG')):
            nodos_estructura.append((z, nombre, coordenadas))
        
        # Nodos de conductor
        elif nombre.startswith(('C1', 'C2', 'C3')):
            if z not in conductores_por_altura:
                conductores_por_altura[z] = []
            conductores_por_altura[z].append((x, nombre, coordenadas))
        
        # Nodos de guardia
        elif nombre.startswith('HG'):
            nodos_guardia.append((x, nombre, coordenadas))
    
    # 2. DIBUJAR COLUMNAS DE ESTRUCTURA
    tiene_y = any('Y' in nombre for nombre in nodes_key.keys())
    
    if tiene_y:
        # Configuración horizontal: BASE-Y1, Y1-Y2-Y4, Y1-Y3-Y5, HG1-Y4, HG2-Y5
        if 'BASE' in nodes_key and 'Y1' in nodes_key:
            base_x, base_y, base_z = nodes_key['BASE']
            y1_x, y1_y, y1_z = nodes_key['Y1']
            ax.plot([base_x, y1_x], [base_z, y1_z], color='black', linewidth=linewidth, alpha=0.8)
        
        # Y1 → Y2 → Y4 (columna derecha)
        if 'Y1' in nodes_key and 'Y2' in nodes_key:
            y1_x, y1_y, y1_z = nodes_key['Y1']
            y2_x, y2_y, y2_z = nodes_key['Y2']
            ax.plot([y1_x, y2_x], [y1_z, y2_z], color='black', linewidth=linewidth, alpha=0.8)
            
            if 'Y4' in nodes_key:
                y4_x, y4_y, y4_z = nodes_key['Y4']
                ax.plot([y2_x, y4_x], [y2_z, y4_z], color='black', linewidth=linewidth, alpha=0.8)
        
        # Y1 → Y3 → Y5 (columna izquierda)
        if 'Y1' in nodes_key and 'Y3' in nodes_key:
            y1_x, y1_y, y1_z = nodes_key['Y1']
            y3_x, y3_y, y3_z = nodes_key['Y3']
            ax.plot([y1_x, y3_x], [y1_z, y3_z], color='black', linewidth=linewidth, alpha=0.8)
            
            if 'Y5' in nodes_key:
                y5_x, y5_y, y5_z = nodes_key['Y5']
                ax.plot([y3_x, y5_x], [y3_z, y5_z], color='black', linewidth=linewidth, alpha=0.8)
        
        # HG1 → Y4 (columna a guardia derecha)
        if 'HG1' in nodes_key and 'Y4' in nodes_key:
            hg1_x, hg1_y, hg1_z = nodes_key['HG1']
            y4_x, y4_y, y4_z = nodes_key['Y4']
            ax.plot([y4_x, hg1_x], [y4_z, hg1_z], color='black', linewidth=linewidth, alpha=0.8)
        
        # HG2 → Y5 (columna a guardia izquierda)
        if 'HG2' in nodes_key and 'Y5' in nodes_key:
            hg2_x, hg2_y, hg2_z = nodes_key['HG2']
            y5_x, y5_y, y5_z = nodes_key['Y5']
            ax.plot([y5_x, hg2_x], [y5_z, hg2_z], color='black', linewidth=linewidth, alpha=0.8)
    else:
        # Configuración estándar: línea vertical
        nodos_estructura.sort(key=lambda x: x[0])
        if len(nodos_estructura) >= 2:
            for i in range(len(nodos_estructura)-1):
                z1, nombre1, coord1 = nodos_estructura[i]
                z2, nombre2, coord2 = nodos_estructura[i+1]
                ax.plot([0, 0], [z1, z2], color='black', linewidth=linewidth, alpha=0.8)
    
    # 3. DIBUJAR MENSULAS/CRUCETAS DE CONDUCTORES
    for altura, conductores in conductores_por_altura.items():
        # Buscar nodo CROSS o Y correspondiente
        cross_node = None
        min_diff = float('inf')
        
        for nombre, coordenadas in nodes_key.items():
            if "CROSS" in nombre or nombre.startswith('Y'):
                x_cross, y_cross, z_cross = coordenadas
                diff = abs(z_cross - altura)
                if diff < min_diff:
                    min_diff = diff
                    cross_node = (nombre, coordenadas)
        
        if cross_node:
            cross_nombre, cross_coord = cross_node
            x_cross, y_cross, z_cross = cross_coord
            
            conductores_x = [c[0] for c in conductores]
            hay_izq = any(x < -0.01 for x in conductores_x)
            hay_der = any(x > 0.01 for x in conductores_x)
            
            if hay_izq and hay_der:
                # Cruceta: línea horizontal completa
                x_min = min(conductores_x)
                x_max = max(conductores_x)
                ax.plot([x_min, x_max], [altura, altura], 
                       color='black', linewidth=linewidth*0.85, alpha=0.8)
                
                # Conexión vertical desde nodo de cruce a cruceta si difieren
                if abs(z_cross - altura) > 0.01:
                    ax.plot([0, 0], [z_cross, altura], 
                           color='black', linewidth=linewidth*0.6, alpha=0.6, linestyle=':')
            else:
                # Ménsula: cada conductor se conecta individualmente
                for x_cond, nombre_cond, coord_cond in conductores:
                    ax.plot([x_cross, x_cond], [z_cross, altura], 
                           color='black', linewidth=linewidth*0.85, alpha=0.8)
    
    # 4. DIBUJAR MENSULAS/CRUCETAS DE GUARDIAS (solo si no es horizontal)
    if not tiene_y:
        if "TOP" in nodes_key:
            x_top, y_top, z_top = nodes_key["TOP"]
            
            if nodos_guardia:
                guardias_x = [g[0] for g in nodos_guardia]
                hay_izq = any(x < 0 for x in guardias_x)
                hay_der = any(x > 0 for x in guardias_x)
                
                if hay_izq and hay_der:
                    # Cruceta guardia: línea horizontal completa
                    x_min = min(guardias_x)
                    x_max = max(guardias_x)
                    ax.plot([x_min, x_max], [z_top, z_top], 
                           color='black', linewidth=linewidth*0.85, alpha=0.8)
                    
                    # Conexiones verticales a TOP
                    for x_hg, nombre_hg, coord_hg in nodos_guardia:
                        z_hg = coord_hg[2]
                        if abs(z_hg - z_top) > 0.01:
                            ax.plot([x_hg, x_hg], [z_top, z_hg], 
                                   color='black', linewidth=linewidth*0.6, alpha=0.6, linestyle=':')
                else:
                    # Ménsula guardia: cada guardia se conecta individualmente
                    for x_hg, nombre_hg, coord_hg in nodos_guardia:
                        z_hg = coord_hg[2]
                        ax.plot([x_top, x_hg], [z_top, z_hg], 
                               color='black', linewidth=linewidth*0.85, alpha=0.8)


def dibujar_flechas_2d(ax, cargas_hipotesis, nodes_key, rangos, escala, fontsize=9):
    """Dibuja flechas de cargas en 2D"""
    colores = {'x': 'red', 'y': 'green', 'z': 'blue'}
    longitud_base = 0.08 * rangos['max_range'] * escala
    
    for nombre_nodo, carga in cargas_hipotesis.items():
        if not any(val != 0 for val in carga):
            continue
        
        if nombre_nodo not in nodes_key:
            continue
        
        coords = nodes_key[nombre_nodo]
        x, z = coords[0], coords[2]
        
        for i, (componente, color) in enumerate(colores.items()):
            fuerza = carga[i]
            if fuerza == 0:
                continue
            
            fuerza_daN = abs(fuerza)
            direccion = 1 if fuerza > 0 else -1
            
            if componente == 'x':
                dx, dz = direccion * longitud_base, 0
                ax.arrow(x, z, dx, dz, head_width=longitud_base*0.12,
                        head_length=longitud_base*0.2, fc=color, ec=color, 
                        linewidth=1.2, alpha=0.95, length_includes_head=True, zorder=500)
                ax.text(x + dx/2, z + longitud_base*0.1, f"{fuerza_daN:.1f}", 
                       color='darkred', fontsize=fontsize, fontweight='bold', zorder=1000,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.95, 
                               edgecolor=color, linewidth=1.2), ha='center', va='center')
            
            elif componente == 'z':
                dx, dz = 0, direccion * longitud_base
                ax.arrow(x, z, dx, dz, head_width=longitud_base*0.12,
                        head_length=longitud_base*0.2, fc=color, ec=color,
                        linewidth=1.2, alpha=0.95, length_includes_head=True, zorder=500)
                ax.text(x + longitud_base*0.1, z + dz/2, f"{fuerza_daN:.1f}",
                       color='darkblue', fontsize=fontsize, fontweight='bold', zorder=1000,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.95,
                               edgecolor=color, linewidth=1.2), ha='center', va='center')
            
            elif componente == 'y':
                dx = direccion * longitud_base * 0.7
                dz = direccion * longitud_base * 0.7
                ax.arrow(x, z, dx, dz, head_width=longitud_base*0.12,
                        head_length=longitud_base*0.2, fc=color, ec=color,
                        linewidth=1.2, alpha=0.95, linestyle='--', 
                        length_includes_head=True, zorder=500)
                ax.text(x + dx/2, z + dz/2 + longitud_base*0.1, f"{fuerza_daN:.1f}",
                       color='darkgreen', fontsize=fontsize, fontweight='bold', zorder=1000,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.95,
                               edgecolor=color, linewidth=1.2), ha='center', va='center')


def dibujar_panel_reacciones_2d(ax, datos_reacciones, rangos):
    """Dibuja panel con información de reacciones"""
    x_pos = rangos['x_min'] + rangos['max_range'] * 0.02
    z_pos = rangos['z_min'] + rangos['max_range'] * 0.02
    
    texto = f"REACCIONES BASE:\n"
    texto += f"Fx: {datos_reacciones['Reaccion_Fx_daN']:.1f} daN\n"
    texto += f"Fy: {datos_reacciones['Reaccion_Fy_daN']:.1f} daN\n"
    texto += f"Fz: {datos_reacciones['Reaccion_Fz_daN']:.1f} daN\n"
    texto += f"Mx: {datos_reacciones['Reaccion_Mx_daN_m']:.1f} daN·m\n"
    texto += f"My: {datos_reacciones['Reaccion_My_daN_m']:.1f} daN·m\n"
    texto += f"Mz: {datos_reacciones['Reaccion_Mz_daN_m']:.1f} daN·m\n"
    texto += f"Fcima: {datos_reacciones['Tiro_resultante_daN']:.1f} daN"
    
    ax.text(x_pos, z_pos, texto, fontsize=8, fontweight='bold', zorder=1000, color='black',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor='black'),
            ha='left', va='bottom')


def dibujar_etiquetas_nodos_2d(ax, nodos_con_cargas, nodes_key, fontsize=8):
    """Dibuja etiquetas de nodos cargados"""
    for nombre_nodo in nodos_con_cargas:
        if nombre_nodo not in nodes_key:
            continue
        
        coords = nodes_key[nombre_nodo]
        x, z = coords[0], coords[2]
        
        ax.text(x - 0.3, z + 0.2, nombre_nodo, fontsize=fontsize, fontweight='bold',
               ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.7, edgecolor='black'))
