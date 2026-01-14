"""Generador de Árboles de Carga 2D y 3D"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pathlib import Path
import hashlib
import json
from config.app_config import CACHE_DIR
import plotly.graph_objects as go


def calcular_hash_estructura(estructura_dict):
    """Calcular hash MD5 de la estructura"""
    estructura_str = json.dumps(estructura_dict, sort_keys=True)
    return hashlib.md5(estructura_str.encode()).hexdigest()


def generar_arboles_carga(estructura_mecanica, estructura_actual, zoom=0.5, escala_flecha=1.8, 
                          grosor_linea=3.5, mostrar_nodos=True, fontsize_nodos=8, fontsize_flechas=9, mostrar_sismo=False, usar_3d=True, estructura_geometria=None):
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
        
        # Verificar que haya cargas en nodos
        nodos_con_cargas = sum(1 for nodo in estructura_mecanica.geometria.nodos.values() 
                              if (hasattr(nodo, 'cargas_dict') and nodo.cargas_dict) or nodo.cargas)
        if nodos_con_cargas == 0:
            return {
                'exito': False,
                'mensaje': 'No hay datos de cargas. Ejecute primero el Cálculo Mecánico de Cables.'
            }
        
        # Obtener datos - usar nodes_key que incluye nodos editados
        nodes_key = estructura_mecanica.geometria.nodes_key
        resultados_reacciones = estructura_mecanica.resultados_reacciones
        
        # Obtener lista de hipótesis desde nodos
        todas_hipotesis = estructura_mecanica._obtener_lista_hipotesis()
        
        # Calcular hash
        hash_estructura = calcular_hash_estructura(estructura_actual)
        titulo = estructura_actual.get('TITULO', 'estructura')
        
        # Calcular rangos de ejes
        rangos = calcular_rangos_ejes_2d(nodes_key, zoom)
        
        imagenes_generadas = []
        
        # Si es 3D, generar un solo gráfico interactivo con todas las hipótesis
        if usar_3d:
            # Obtener dataframe de cargas desde estructura_mecanica
            df_cargas = None
            if hasattr(estructura_mecanica, 'df_cargas_completo') and estructura_mecanica.df_cargas_completo is not None:
                df_cargas = estructura_mecanica.df_cargas_completo
            
            # Recolectar todas las cargas por hipótesis desde el dataframe
            todas_cargas_hipotesis = {}
            for hipotesis_nombre in todas_hipotesis:
                if not mostrar_sismo and '_C2_' in hipotesis_nombre:
                    continue
                
                cargas_hipotesis = {}
                if df_cargas is not None:
                    # Usar datos del dataframe directamente
                    print(f"🔍 DEBUG: Buscando {hipotesis_nombre} en columnas: {list(df_cargas.columns.get_level_values(0).unique())}")
                    for nodo_nombre in df_cargas.index:
                        if hipotesis_nombre in df_cargas.columns.get_level_values(0):
                            try:
                                fx = df_cargas.loc[nodo_nombre, (hipotesis_nombre, 'x')]
                                fy = df_cargas.loc[nodo_nombre, (hipotesis_nombre, 'y')]
                                fz = df_cargas.loc[nodo_nombre, (hipotesis_nombre, 'z')]
                                if any(abs(val) > 0.01 for val in [fx, fy, fz]):
                                    cargas_hipotesis[nodo_nombre] = [fx, fy, fz]
                            except (KeyError, IndexError):
                                continue
                        else:
                            print(f"⚠️  DEBUG: {hipotesis_nombre} no encontrada en columnas DataFrame")
                # Siempre usar método de nodos como fallback
                print(f"🔄 DEBUG: Usando método de nodos para {hipotesis_nombre}")
                for nombre_nodo, nodo in estructura_mecanica.geometria.nodos.items():
                    if not hasattr(nodo, 'cargas_dict') or not nodo.cargas_dict:
                        continue
                    
                    # Para visualización 3D, siempre usar coordenadas globales
                    cargas = nodo.obtener_cargas_hipotesis(hipotesis_nombre)
                    carga_lista = [cargas["fx"], cargas["fy"], cargas["fz"]]
                    if any(abs(val) > 0.01 for val in carga_lista):
                        cargas_hipotesis[nombre_nodo] = carga_lista
                        print(f"✅ DEBUG: Cargas encontradas en {nombre_nodo}: {carga_lista}")
                
                # Agregar hipótesis si tiene cargas
                if cargas_hipotesis:
                    todas_cargas_hipotesis[hipotesis_nombre] = cargas_hipotesis
                    print(f"✅ DEBUG: Hipótesis {hipotesis_nombre} agregada con {len(cargas_hipotesis)} nodos")
                else:
                    print(f"⚠️  DEBUG: No se encontraron cargas para {hipotesis_nombre}")
            
            if todas_cargas_hipotesis:
                fig = generar_arbol_3d_interactivo(nodes_key, todas_cargas_hipotesis, 
                                                   resultados_reacciones, estructura_actual, estructura_geometria)
                
                titulo_sanitizado = titulo.replace('\n', '_').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                nombre_archivo = f"{titulo_sanitizado}.arbolcarga.{hash_estructura}.3D_interactivo.png"
                ruta_imagen = CACHE_DIR / nombre_archivo
                
                fig.write_image(str(ruta_imagen), width=1200, height=900)
                nombre_json = nombre_archivo.replace('.png', '.json')
                ruta_json = CACHE_DIR / nombre_json
                fig.write_json(str(ruta_json))
                
                imagenes_generadas.append({
                    'hipotesis': 'Interactivo 3D',
                    'ruta': ruta_imagen,
                    'nombre': nombre_archivo
                })
            
            if not imagenes_generadas:
                print(f"❌ DEBUG: No se generaron imágenes 3D")
                print(f"   todas_cargas_hipotesis: {len(todas_cargas_hipotesis)} hipótesis")
                print(f"   df_cargas disponible: {df_cargas is not None}")
                if df_cargas is not None:
                    print(f"   df_cargas shape: {df_cargas.shape}")
                    print(f"   df_cargas columns: {list(df_cargas.columns.get_level_values(0).unique())}")
                print(f"   todas_hipotesis: {todas_hipotesis}")
                return {'exito': False, 'mensaje': 'No se generaron imágenes 3D'}
            
            return {
                'exito': True,
                'mensaje': f'Se generó árbol de carga 3D interactivo',
                'imagenes': imagenes_generadas
            }
        
        # Generar imagen para cada hipótesis (solo 2D)
        for hipotesis_nombre in todas_hipotesis:
            # Filtrar hipótesis C2 si mostrar_sismo es False
            if not mostrar_sismo and '_C2_' in hipotesis_nombre:
                continue
            
            # Construir dict de cargas para esta hipótesis desde nodos
            cargas_hipotesis = {}
            nodos_con_cargas_lista = []
            
            for nombre_nodo, nodo in estructura_mecanica.geometria.nodos.items():
                # Aplicar rotaciones si el nodo tiene rotación
                if nodo.rotacion_eje_x != 0 or nodo.rotacion_eje_y != 0 or nodo.rotacion_eje_z != 0:
                    cargas = nodo.obtener_cargas_hipotesis_rotadas(hipotesis_nombre, "global")
                else:
                    cargas = nodo.obtener_cargas_hipotesis(hipotesis_nombre)
                carga_lista = [cargas["fx"], cargas["fy"], cargas["fz"]]
                cargas_hipotesis[nombre_nodo] = carga_lista
                
                if any(val != 0 for val in carga_lista):
                    nodos_con_cargas_lista.append(nombre_nodo)
            
            if not nodos_con_cargas_lista:
                continue
            
            # Obtener reacciones
            if hipotesis_nombre not in resultados_reacciones:
                continue
            
            datos_reacciones = resultados_reacciones[hipotesis_nombre]
            
            # Crear figura 2D o 3D según configuración
            if usar_3d:
                fig = generar_arbol_3d(nodes_key, cargas_hipotesis, datos_reacciones, 
                                      hipotesis_nombre, estructura_actual, escala_flecha)
            else:
                fig, ax = plt.subplots(figsize=(12, 10))
            
            if not usar_3d:
                # Dibujar estructura (todos los elementos en negro)
                dibujar_estructura_2d(ax, nodes_key, grosor_linea)
                
                # Dibujar flechas de cargas
                dibujar_flechas_2d(ax, cargas_hipotesis, nodes_key, rangos, escala_flecha, fontsize_flechas)
                
                # Panel de reacciones
                dibujar_panel_reacciones_2d(ax, datos_reacciones, rangos)
                
                # Etiquetas de nodos si está activado
                if mostrar_nodos:
                    dibujar_etiquetas_nodos_2d(ax, nodos_con_cargas_lista, nodes_key, fontsize_nodos)
                
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
            
            if usar_3d:
                fig.write_image(str(ruta_imagen), width=1200, height=900)
                # Guardar también JSON para interactividad
                nombre_json = nombre_archivo.replace('.png', '.json')
                ruta_json = CACHE_DIR / nombre_json
                fig.write_json(str(ruta_json))
            else:
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
        
        # CASO ESPECIAL: HG1 centrado en doble terna vertical
        if ('CROSS_H3' in nodes_key and 'HG1' in nodes_key and 
            abs(nodes_key['HG1'][0]) < 0.001):  # HG1 centrado
            x_cross, y_cross, z_cross = nodes_key['CROSS_H3']
            x_hg, y_hg, z_hg = nodes_key['HG1']
            ax.plot([0, 0], [z_cross, z_hg], color='black', linewidth=linewidth, alpha=0.8)
    
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
    
    # 5. DIBUJAR NODOS COMO CÍRCULOS
    for nombre, coordenadas in nodes_key.items():
        x, y, z = coordenadas
        
        if abs(y) > 0.001:  # Solo plano XZ
            continue
        
        # Determinar color y tamaño según tipo de nodo
        if nombre.startswith(('C1', 'C2', 'C3')):
            color = '#1f77b4'  # Azul conductor
            size = 0.08
        elif nombre.startswith('HG'):
            color = '#2ca02c' if nombre == 'HG1' else '#228B22'  # Verde guardia
            size = 0.08
        elif "BASE" in nombre:
            color = '#000000'  # Negro estructura
            size = 0.1
        elif "TOP" in nombre or "CROSS" in nombre or nombre.startswith('Y'):
            color = '#000000'  # Negro estructura
            size = 0.06
        else:
            color = 'gray'
            size = 0.05
        
        # Dibujar círculo
        circle = plt.Circle((x, z), size, color=color, alpha=0.8, zorder=5)
        ax.add_patch(circle)


def dibujar_flechas_2d(ax, cargas_hipotesis, nodes_key, rangos, escala, fontsize=9):
    """Dibuja flechas de cargas en 2D con desplazamiento solo para posiciones exactamente iguales"""
    colores = {'x': 'red', 'y': 'green', 'z': 'blue'}
    longitud_base = 0.08 * rangos['max_range'] * escala
    posiciones_etiquetas = []
    
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
                
                # Posición inicial de etiqueta
                x_etiq = x + dx/2
                z_etiq = z + longitud_base*0.1
                
                # Desplazar solo si posición exactamente igual
                desplazamiento = 0
                while any(abs(x_etiq - pos[0]) < 0.01 and abs(z_etiq - pos[1]) < 0.01 
                         for pos in posiciones_etiquetas):
                    desplazamiento += longitud_base*0.6
                    x_etiq = x + dx/2 + desplazamiento
                
                posiciones_etiquetas.append((x_etiq, z_etiq))
                
                ax.text(x_etiq, z_etiq, f"{fuerza_daN:.1f}", 
                       color='darkred', fontsize=fontsize, fontweight='bold', zorder=1000,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.95, 
                               edgecolor=color, linewidth=1.2), ha='center', va='center')
            
            elif componente == 'z':
                dx, dz = 0, direccion * longitud_base
                ax.arrow(x, z, dx, dz, head_width=longitud_base*0.12,
                        head_length=longitud_base*0.2, fc=color, ec=color,
                        linewidth=1.2, alpha=0.95, length_includes_head=True, zorder=500)
                
                # Posición inicial de etiqueta
                x_etiq = x + longitud_base*0.1
                z_etiq = z + dz/2
                
                # Desplazar solo si posición exactamente igual
                desplazamiento = 0
                while any(abs(x_etiq - pos[0]) < 0.01 and abs(z_etiq - pos[1]) < 0.01 
                         for pos in posiciones_etiquetas):
                    desplazamiento += longitud_base*0.6
                    x_etiq = x + longitud_base*0.1 + desplazamiento
                
                posiciones_etiquetas.append((x_etiq, z_etiq))
                
                ax.text(x_etiq, z_etiq, f"{fuerza_daN:.1f}",
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
                
                # Posición inicial de etiqueta
                x_etiq = x + dx/2
                z_etiq = z + dz/2 + longitud_base*0.1
                
                # Desplazar solo si posición exactamente igual
                desplazamiento = 0
                while any(abs(x_etiq - pos[0]) < 0.01 and abs(z_etiq - pos[1]) < 0.01 
                         for pos in posiciones_etiquetas):
                    desplazamiento += longitud_base*0.6
                    x_etiq = x + dx/2 + desplazamiento
                
                posiciones_etiquetas.append((x_etiq, z_etiq))
                
                ax.text(x_etiq, z_etiq, f"{fuerza_daN:.1f}",
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
    """Dibuja etiquetas de nodos cargados con desplazamiento solo para posiciones exactamente iguales"""
    posiciones_usadas = []
    
    for nombre_nodo in nodos_con_cargas:
        if nombre_nodo not in nodes_key:
            continue
        
        coords = nodes_key[nombre_nodo]
        x, z = coords[0], coords[2]
        
        # Posición inicial de etiqueta
        x_etiqueta = x - 0.3
        z_etiqueta = z + 0.2
        
        # Verificar posición exactamente igual
        desplazamiento = 0
        while any(abs(x_etiqueta - pos[0]) < 0.01 and abs(z_etiqueta - pos[1]) < 0.01 
                 for pos in posiciones_usadas):
            desplazamiento += 1.4
            x_etiqueta = x - 0.3 + desplazamiento
        
        posiciones_usadas.append((x_etiqueta, z_etiqueta))
        
        ax.text(x_etiqueta, z_etiqueta, nombre_nodo, fontsize=fontsize, fontweight='bold',
               ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.7, edgecolor='black'))


def generar_arbol_3d_interactivo(nodes_key, todas_cargas_hipotesis, resultados_reacciones, estructura_actual, estructura_geometria=None):
    """Genera gráfico 3D interactivo con selector de hipótesis usando datos del dataframe"""
    fig = go.Figure()
    
    COLORES = {
        'conductor': '#1f77b4', 'guardia': '#2ca02c', 'poste': '#000000',
        'terreno': '#8B4513', 'otros': '#FF8C00'
    }
    
    # Agrupar TODOS los nodos por tipo (incluyendo editados)
    nodos_conductor = []
    nodos_guardia = []
    nodos_estructura = []
    nodos_otros = []
    
    for nombre, coords in nodes_key.items():
        x, y, z = coords
        if nombre.startswith(('C1', 'C2', 'C3')):
            nodos_conductor.append((x, y, z, nombre))
        elif nombre.startswith('HG'):
            nodos_guardia.append((x, y, z, nombre))
        elif 'BASE' in nombre or 'TOP' in nombre or 'CROSS' in nombre or nombre.startswith('Y'):
            nodos_estructura.append((x, y, z, nombre))
        else:
            nodos_otros.append((x, y, z, nombre))
    
    # Dibujar nodos
    if nodos_conductor:
        x_vals, y_vals, z_vals, nombres = zip(*nodos_conductor)
        fig.add_trace(go.Scatter3d(
            x=list(x_vals), y=list(y_vals), z=list(z_vals),
            mode='markers+text',
            marker=dict(size=8, color=COLORES['conductor'], line=dict(color='white', width=2)),
            text=list(nombres), textposition='top center', textfont=dict(size=9),
            name='Conductores',
            hovertemplate='<b>%{text}</b><br>X: %{x:.3f} m<br>Y: %{y:.3f} m<br>Z: %{z:.3f} m<extra></extra>'
        ))
    
    if nodos_guardia:
        x_vals, y_vals, z_vals, nombres = zip(*nodos_guardia)
        fig.add_trace(go.Scatter3d(
            x=list(x_vals), y=list(y_vals), z=list(z_vals),
            mode='markers+text',
            marker=dict(size=8, color=COLORES['guardia'], line=dict(color='white', width=2)),
            text=list(nombres), textposition='top center', textfont=dict(size=9),
            name='Guardias',
            hovertemplate='<b>%{text}</b><br>X: %{x:.3f} m<br>Y: %{y:.3f} m<br>Z: %{z:.3f} m<extra></extra>'
        ))
    
    if nodos_estructura:
        x_vals, y_vals, z_vals, nombres = zip(*nodos_estructura)
        fig.add_trace(go.Scatter3d(
            x=list(x_vals), y=list(y_vals), z=list(z_vals),
            mode='markers+text',
            marker=dict(size=8, color=COLORES['poste'], line=dict(color='white', width=2)),
            text=list(nombres), textposition='top center', textfont=dict(size=9),
            name='Estructura',
            hovertemplate='<b>%{text}</b><br>X: %{x:.3f} m<br>Y: %{y:.3f} m<br>Z: %{z:.3f} m<extra></extra>'
        ))
    
    if nodos_otros:
        x_vals, y_vals, z_vals, nombres = zip(*nodos_otros)
        fig.add_trace(go.Scatter3d(
            x=list(x_vals), y=list(y_vals), z=list(z_vals),
            mode='markers+text',
            marker=dict(size=8, color=COLORES['otros'], line=dict(color='white', width=2)),
            text=list(nombres), textposition='top center', textfont=dict(size=9),
            name='Otros',
            hovertemplate='<b>%{text}</b><br>X: %{x:.3f} m<br>Y: %{y:.3f} m<br>Z: %{z:.3f} m<extra></extra>'
        ))
    
    dibujar_lineas_estructura_3d(fig, nodes_key, estructura_geometria)
    
    # Plano de terreno
    x_coords = [coords[0] for coords in nodes_key.values()]
    y_coords = [coords[1] for coords in nodes_key.values()]
    if x_coords and y_coords:
        x_range = [min(x_coords) - 1, max(x_coords) + 1]
        y_range = [min(y_coords) - 1, max(y_coords) + 1]
        fig.add_trace(go.Mesh3d(
            x=[x_range[0], x_range[1], x_range[1], x_range[0]],
            y=[y_range[0], y_range[0], y_range[1], y_range[1]],
            z=[0, 0, 0, 0],
            color=COLORES['terreno'], opacity=0.3,
            name='Terreno', showlegend=True, hoverinfo='skip'
        ))
    
    # Agregar flechas para cada hipótesis usando datos del dataframe
    lista_hipotesis = list(todas_cargas_hipotesis.keys())
    for idx, hipotesis_nombre in enumerate(lista_hipotesis):
        visible = (idx == 0)  # Solo la primera hipótesis visible inicialmente
        dibujar_flechas_desde_dataframe(fig, todas_cargas_hipotesis[hipotesis_nombre], nodes_key, hipotesis_nombre, visible)
    
    # Crear botones para selector de hipótesis
    buttons = []
    tipo_estructura = estructura_actual.get('TIPO_ESTRUCTURA', '')
    
    # Separar traces fijos de traces de flechas
    traces_fijos = []
    traces_flechas = []
    
    for i, trace in enumerate(fig.data):
        if (hasattr(trace, 'name') and 
            (trace.name in ['Conductores', 'Guardias', 'Estructura', 'Otros', 'Terreno'] or
             (hasattr(trace, 'showlegend') and trace.showlegend == False and hasattr(trace, 'mode') and trace.mode == 'lines'))):
            traces_fijos.append(i)
        elif hasattr(trace, 'name') and trace.name and trace.name.startswith('flecha_'):
            traces_flechas.append(i)
    
    for idx, hipotesis_nombre in enumerate(lista_hipotesis):
        visibility = [False] * len(fig.data)  # Inicializar todo como oculto
        
        # Traces fijos siempre visibles
        for trace_idx in traces_fijos:
            visibility[trace_idx] = True
        
        # Solo mostrar flechas de la hipótesis seleccionada
        for trace_idx in traces_flechas:
            trace = fig.data[trace_idx]
            if hasattr(trace, 'name') and f'flecha_{hipotesis_nombre}_' in trace.name:
                visibility[trace_idx] = True
        
        codigo_hip = hipotesis_nombre.split('_')[-2] if '_' in hipotesis_nombre else hipotesis_nombre
        descripcion_hip = hipotesis_nombre.split('_')[-1] if '_' in hipotesis_nombre else ''
        
        buttons.append(dict(
            label=f"{codigo_hip} - {descripcion_hip}",
            method="restyle",
            args=[{"visible": visibility}]
        ))
    
    titulo_inicial = f"ÁRBOL DE CARGA 3D - {tipo_estructura.upper()}"
    
    fig.update_layout(
        title=dict(text=titulo_inicial, font=dict(size=16, family='Arial Black')),
        updatemenus=[dict(
            type="dropdown",
            direction="down",
            x=0.5, xanchor="center",
            y=1.15, yanchor="top",
            buttons=buttons,
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        )],
        scene=dict(
            xaxis=dict(title='X [m]', gridcolor='lightgray', showbackground=True,
                      backgroundcolor='white', type='linear', dtick=1),
            yaxis=dict(title='Y [m]', gridcolor='lightgray', showbackground=True,
                      backgroundcolor='white', type='linear', dtick=1),
            zaxis=dict(title='Z [m]', gridcolor='lightgray', showbackground=True,
                      backgroundcolor='white', type='linear', dtick=1),
            aspectmode='data',
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1))
        ),
        showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.9)', bordercolor='black', borderwidth=1),
        width=1200, height=900,
        margin=dict(l=0, r=0, t=100, b=0)
    )
    
    return fig


def generar_arbol_3d(nodes_key, cargas_hipotesis, datos_reacciones, hipotesis_nombre, estructura_actual, escala_flecha=1.8):
    """Genera gráfico 3D interactivo de árbol de carga usando Plotly (estilo DGE)"""
    fig = go.Figure()
    
    # Colores (mismo esquema que EstructuraAEA_Graficos)
    COLORES = {
        'conductor': '#1f77b4', 'guardia': '#2ca02c', 'poste': '#000000',
        'terreno': '#8B4513'
    }
    
    # Agrupar nodos por tipo
    nodos_conductor = []
    nodos_guardia = []
    nodos_estructura = []
    
    for nombre, coords in nodes_key.items():
        x, y, z = coords
        if nombre.startswith(('C1', 'C2', 'C3')):
            nodos_conductor.append((x, y, z, nombre))
        elif nombre.startswith('HG'):
            nodos_guardia.append((x, y, z, nombre))
        elif 'BASE' in nombre or 'TOP' in nombre or 'CROSS' in nombre or nombre.startswith('Y'):
            nodos_estructura.append((x, y, z, nombre))
    
    # Dibujar nodos por tipo
    if nodos_conductor:
        x_vals, y_vals, z_vals, nombres = zip(*nodos_conductor)
        fig.add_trace(go.Scatter3d(
            x=list(x_vals), y=list(y_vals), z=list(z_vals),
            mode='markers+text',
            marker=dict(size=8, color=COLORES['conductor'], line=dict(color='white', width=2)),
            text=list(nombres),
            textposition='top center',
            textfont=dict(size=9),
            name='Conductores',
            hovertemplate='<b>%{text}</b><br>X: %{x:.3f} m<br>Y: %{y:.3f} m<br>Z: %{z:.3f} m<extra></extra>'
        ))
    
    if nodos_guardia:
        x_vals, y_vals, z_vals, nombres = zip(*nodos_guardia)
        fig.add_trace(go.Scatter3d(
            x=list(x_vals), y=list(y_vals), z=list(z_vals),
            mode='markers+text',
            marker=dict(size=8, color=COLORES['guardia'], line=dict(color='white', width=2)),
            text=list(nombres),
            textposition='top center',
            textfont=dict(size=9),
            name='Guardias',
            hovertemplate='<b>%{text}</b><br>X: %{x:.3f} m<br>Y: %{y:.3f} m<br>Z: %{z:.3f} m<extra></extra>'
        ))
    
    if nodos_estructura:
        x_vals, y_vals, z_vals, nombres = zip(*nodos_estructura)
        fig.add_trace(go.Scatter3d(
            x=list(x_vals), y=list(y_vals), z=list(z_vals),
            mode='markers+text',
            marker=dict(size=8, color=COLORES['poste'], line=dict(color='white', width=2)),
            text=list(nombres),
            textposition='top center',
            textfont=dict(size=9),
            name='Estructura',
            hovertemplate='<b>%{text}</b><br>X: %{x:.3f} m<br>Y: %{y:.3f} m<br>Z: %{z:.3f} m<extra></extra>'
        ))
    
    # Dibujar líneas de estructura
    dibujar_lineas_estructura_3d(fig, nodes_key)
    
    # Dibujar flechas de cargas
    dibujar_flechas_3d(fig, cargas_hipotesis, nodes_key, escala_flecha)
    
    # Plano de terreno
    x_coords = [coords[0] for coords in nodes_key.values()]
    y_coords = [coords[1] for coords in nodes_key.values()]
    if x_coords and y_coords:
        x_range = [min(x_coords) - 1, max(x_coords) + 1]
        y_range = [min(y_coords) - 1, max(y_coords) + 1]
        
        fig.add_trace(go.Mesh3d(
            x=[x_range[0], x_range[1], x_range[1], x_range[0]],
            y=[y_range[0], y_range[0], y_range[1], y_range[1]],
            z=[0, 0, 0, 0],
            color=COLORES['terreno'],
            opacity=0.3,
            name='Terreno',
            showlegend=True,
            hoverinfo='skip'
        ))
    
    # Título
    codigo_hip = hipotesis_nombre.split('_')[-2] if '_' in hipotesis_nombre else hipotesis_nombre
    descripcion_hip = hipotesis_nombre.split('_')[-1] if '_' in hipotesis_nombre else ''
    tipo_estructura = estructura_actual.get('TIPO_ESTRUCTURA', '')
    titulo = f'ÁRBOL DE CARGA 3D - Hip. {codigo_hip} - {descripcion_hip} - {tipo_estructura.upper()}'
    
    # Configuración de layout (mismo estilo que DGE)
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=16, family='Arial Black')),
        scene=dict(
            xaxis=dict(
                title='X [m]',
                gridcolor='lightgray',
                showbackground=True,
                backgroundcolor='white',
                type='linear',
                dtick=1
            ),
            yaxis=dict(
                title='Y [m]',
                gridcolor='lightgray',
                showbackground=True,
                backgroundcolor='white',
                type='linear',
                dtick=1
            ),
            zaxis=dict(
                title='Z [m]',
                gridcolor='lightgray',
                showbackground=True,
                backgroundcolor='white',
                type='linear',
                dtick=1
            ),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=-1.5, z=1.2),
                center=dict(x=0, y=0, z=0),
                up=dict(x=0, y=0, z=1)
            )
        ),
        showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.9)', bordercolor='black', borderwidth=1),
        width=1200,
        height=800,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig


def dibujar_lineas_estructura_3d(fig, nodes_key, estructura_geometria=None):
    """Dibuja líneas de estructura en 3D usando la misma lógica que EstructuraAEA_Graficos"""
    # Si hay estructura_geometria, usar sus conexiones
    if estructura_geometria and hasattr(estructura_geometria, 'nodos'):
        for nombre_nodo, nodo in estructura_geometria.nodos.items():
            if hasattr(nodo, 'conectado_a') and nodo.conectado_a:
                for nodo_destino in nodo.conectado_a:
                    if nombre_nodo in nodes_key and nodo_destino in nodes_key:
                        x1, y1, z1 = nodes_key[nombre_nodo]
                        x2, y2, z2 = nodes_key[nodo_destino]
                        fig.add_trace(go.Scatter3d(
                            x=[x1, x2], y=[y1, y2], z=[z1, z2],
                            mode='lines',
                            line=dict(color='black', width=4),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
        return
    
    # Fallback: usar EXACTAMENTE la misma lógica que EstructuraAEA_Graficos
    # 1. RECOLECTAR NODOS POR TIPO
    nodos_estructura = []
    conductores_por_altura = {}
    nodos_guardia = []
    
    for nombre, coordenadas in nodes_key.items():
        x, y, z = coordenadas
        
        # Solo plano XZ (y ≈ 0) para estructura 2D, pero incluir todos para 3D
        if abs(x) < 0.001 and abs(y) < 0.001 and not nombre.startswith(('C1', 'C2', 'C3', 'HG')):
            nodos_estructura.append((z, nombre, coordenadas))
        elif nombre.startswith(('C1', 'C2', 'C3')):
            if z not in conductores_por_altura:
                conductores_por_altura[z] = []
            conductores_por_altura[z].append((x, nombre, coordenadas))
        elif nombre.startswith('HG'):
            nodos_guardia.append((x, nombre, coordenadas))
    
    # 2. DIBUJAR COLUMNAS DE ESTRUCTURA
    tiene_y = any('Y' in nombre for nombre in nodes_key.keys())
    
    if tiene_y:
        # Configuración horizontal: BASE-Y1, Y1-Y2-Y4, Y1-Y3-Y5, HG1-Y4, HG2-Y5
        conexiones_horizontales = [
            ('BASE', 'Y1'), ('Y1', 'Y2'), ('Y2', 'Y4'),
            ('Y1', 'Y3'), ('Y3', 'Y5'), ('Y4', 'HG1'), ('Y5', 'HG2')
        ]
        for nodo1, nodo2 in conexiones_horizontales:
            if nodo1 in nodes_key and nodo2 in nodes_key:
                x1, y1, z1 = nodes_key[nodo1]
                x2, y2, z2 = nodes_key[nodo2]
                fig.add_trace(go.Scatter3d(
                    x=[x1, x2], y=[y1, y2], z=[z1, z2],
                    mode='lines',
                    line=dict(color='black', width=4),
                    showlegend=False,
                    hoverinfo='skip'
                ))
    else:
        # Configuración estándar: línea vertical
        nodos_estructura.sort(key=lambda x: x[0])
        if len(nodos_estructura) >= 2:
            for i in range(len(nodos_estructura)-1):
                z1, nombre1, coord1 = nodos_estructura[i]
                z2, nombre2, coord2 = nodos_estructura[i+1]
                fig.add_trace(go.Scatter3d(
                    x=[0, 0], y=[0, 0], z=[z1, z2],
                    mode='lines',
                    line=dict(color='black', width=4),
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        # CASO ESPECIAL: Guardia centrado en doble terna vertical
        if ('CROSS_H3' in nodes_key and 'HG1' in nodes_key and 
            abs(nodes_key['HG1'][0]) < 0.001):  # HG1 centrado
            x_cross, y_cross, z_cross = nodes_key['CROSS_H3']
            x_hg, y_hg, z_hg = nodes_key['HG1']
            fig.add_trace(go.Scatter3d(
                x=[0, 0], y=[0, 0], z=[z_cross, z_hg],
                mode='lines',
                line=dict(color='black', width=4),
                showlegend=False,
                hoverinfo='skip'
            ))
    
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
                fig.add_trace(go.Scatter3d(
                    x=[x_min, x_max], y=[y_cross, y_cross], z=[altura, altura],
                    mode='lines',
                    line=dict(color='black', width=3),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Conexión vertical desde nodo de cruce a cruceta si difieren
                if abs(z_cross - altura) > 0.01:
                    fig.add_trace(go.Scatter3d(
                        x=[0, 0], y=[y_cross, y_cross], z=[z_cross, altura],
                        mode='lines',
                        line=dict(color='black', width=2, dash='dot'),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
            else:
                # Ménsula: cada conductor se conecta individualmente
                for x_cond, nombre_cond, coord_cond in conductores:
                    fig.add_trace(go.Scatter3d(
                        x=[x_cross, x_cond], y=[y_cross, y_cross], z=[z_cross, altura],
                        mode='lines',
                        line=dict(color='black', width=3),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
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
                    fig.add_trace(go.Scatter3d(
                        x=[x_min, x_max], y=[y_top, y_top], z=[z_top, z_top],
                        mode='lines',
                        line=dict(color='black', width=3),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    
                    # Conexiones verticales a TOP
                    for x_hg, nombre_hg, coord_hg in nodos_guardia:
                        z_hg = coord_hg[2]
                        y_hg = coord_hg[1]
                        if abs(z_hg - z_top) > 0.01:
                            fig.add_trace(go.Scatter3d(
                                x=[x_hg, x_hg], y=[y_hg, y_hg], z=[z_top, z_hg],
                                mode='lines',
                                line=dict(color='black', width=2, dash='dot'),
                                showlegend=False,
                                hoverinfo='skip'
                            ))
                else:
                    # Ménsula guardia: cada guardia se conecta individualmente
                    for x_hg, nombre_hg, coord_hg in nodos_guardia:
                        z_hg = coord_hg[2]
                        y_hg = coord_hg[1]
                        fig.add_trace(go.Scatter3d(
                            x=[x_top, x_hg], y=[y_top, y_hg], z=[z_top, z_hg],
                            mode='lines',
                            line=dict(color='black', width=3),
                            showlegend=False,
                            hoverinfo='skip'
                        ))


def dibujar_flechas_desde_dataframe(fig, cargas_hipotesis, nodes_key, hipotesis_nombre, visible=True):
    """Dibuja flechas usando exactamente los valores del dataframe con desplazamiento solo para posiciones exactamente iguales"""
    colores = {'x': 'red', 'y': 'green', 'z': 'blue'}
    nombres = {'x': 'Fx Transversal', 'y': 'Fy Longitudinal', 'z': 'Fz Vertical'}
    TAMANO_MAX_FLECHA_3D = 2.0
    TAMANO_MIN_PORCENTAJE = 0.25
    
    # Encontrar magnitud máxima
    max_fuerza = max(abs(val) for carga in cargas_hipotesis.values() for val in carga if val != 0) or 1
    posiciones_etiquetas = []
    
    for nombre_nodo, carga in cargas_hipotesis.items():
        if nombre_nodo not in nodes_key or not any(abs(val) > 0.01 for val in carga):
            continue
        
        x0, y0, z0 = nodes_key[nombre_nodo]
        fx, fy, fz = float(carga[0]), float(carga[1]), float(carga[2])
        fuerzas = {'x': fx, 'y': fy, 'z': fz}
        
        for comp, fuerza in fuerzas.items():
            if abs(fuerza) < 0.01:
                continue
            
            color = colores[comp]
            ratio = abs(fuerza) / max_fuerza
            magnitud = (TAMANO_MIN_PORCENTAJE + ratio * (1 - TAMANO_MIN_PORCENTAJE)) * TAMANO_MAX_FLECHA_3D
            direccion = 1 if fuerza > 0 else -1
            
            if comp == 'x':
                x1, y1, z1 = x0 + direccion * magnitud, y0, z0
                u, v, w = direccion * 0.2, 0, 0
            elif comp == 'y':
                x1, y1, z1 = x0, y0 + direccion * magnitud, z0
                u, v, w = 0, direccion * 0.2, 0
            else:
                x1, y1, z1 = x0, y0, z0 + direccion * magnitud
                u, v, w = 0, 0, direccion * 0.2
            
            # Línea de flecha
            fig.add_trace(go.Scatter3d(
                x=[x0, x1], y=[y0, y1], z=[z0, z1],
                mode='lines',
                line=dict(color=color, width=6),
                showlegend=False,
                visible=visible,
                name=f'flecha_{hipotesis_nombre}_{comp}_{nombre_nodo}_line',
                hovertemplate=f'<b>{nombre_nodo}</b><br>{nombres[comp]}: {abs(fuerza):.1f} daN<extra></extra>'
            ))
            
            # Cono de flecha
            fig.add_trace(go.Cone(
                x=[x1], y=[y1], z=[z1],
                u=[u], v=[v], w=[w],
                colorscale=[[0, color], [1, color]],
                showscale=False,
                sizemode='absolute',
                sizeref=0.15,
                showlegend=False,
                visible=visible,
                name=f'flecha_{hipotesis_nombre}_{comp}_{nombre_nodo}_cone',
                hoverinfo='skip'
            ))
            
            # Etiqueta de magnitud con desplazamiento solo para posiciones exactamente iguales
            x_text = (x0 + x1) / 2
            y_text = (y0 + y1) / 2
            z_text = (z0 + z1) / 2
            
            # Desplazar solo si posición exactamente igual
            desplazamiento = 0
            while any(abs(x_text - pos[0]) < 0.01 and abs(y_text - pos[1]) < 0.01 and abs(z_text - pos[2]) < 0.01 
                     for pos in posiciones_etiquetas):
                desplazamiento += 0.6
                x_text = (x0 + x1) / 2 + desplazamiento
            
            posiciones_etiquetas.append((x_text, y_text, z_text))
            
            fig.add_trace(go.Scatter3d(
                x=[x_text], y=[y_text], z=[z_text],
                mode='text',
                text=[f'{abs(fuerza):.1f}'],
                textfont=dict(size=10, color=color),
                showlegend=False,
                visible=visible,
                name=f'flecha_{hipotesis_nombre}_{comp}_{nombre_nodo}_text',
                hoverinfo='skip'
            ))


def dibujar_flechas_3d(fig, cargas_hipotesis, nodes_key, escala):
    """Dibuja flechas de cargas en 3D con conos (versión antigua para compatibilidad)"""
    colores = {'x': 'red', 'y': 'green', 'z': 'blue'}
    nombres = {'x': 'Fx Transversal', 'y': 'Fy Longitudinal', 'z': 'Fz Vertical'}
