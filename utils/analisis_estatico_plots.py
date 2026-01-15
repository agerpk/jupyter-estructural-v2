"""
Funciones de plotting para Análisis Estático de Esfuerzos (AEE)
Genera diagramas 2D/3D con hover interactivo usando Plotly
"""

import numpy as np
import plotly.graph_objects as go
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def generar_diagrama_plotly_3d(geometria, conexiones, valores_subnodos, reacciones, parametros, tipo, hipotesis, escala="lineal"):
    """Genera diagrama 3D interactivo con Plotly"""
    
    n_corta = parametros.get('n_segmentar_conexion_corta')
    n_larga = parametros.get('n_segmentar_conexion_larga')
    percentil = parametros.get('percentil_separacion_corta_larga')
    
    # Calcular umbral
    longitudes = [np.linalg.norm(np.array(geometria.nodos[nj].coordenadas) - np.array(geometria.nodos[ni].coordenadas)) 
                  for ni, nj in conexiones]
    umbral_longitud = np.percentile(longitudes, percentil)
    
    # Preparar datos para hover
    x_lines, y_lines, z_lines, colors, hover_texts = [], [], [], [], []
    
    vals = list(valores_subnodos.values())
    vmin, vmax = min(vals), max(vals)
    
    for ni, nj in conexiones:
        ci = np.array(geometria.nodos[ni].coordenadas)
        cj = np.array(geometria.nodos[nj].coordenadas)
        longitud = np.linalg.norm(cj - ci)
        n_subdiv = n_larga if longitud > umbral_longitud else n_corta
        
        for sub_idx in range(n_subdiv):
            t_i = sub_idx / n_subdiv
            t_j = (sub_idx + 1) / n_subdiv
            c_i = ci + t_i * (cj - ci)
            c_j = ci + t_j * (cj - ci)
            
            key = f"{ni}_{nj}_{sub_idx}_i"
            val = valores_subnodos.get(key, 0)
            
            x_lines.extend([c_i[0], c_j[0], None])
            y_lines.extend([c_i[1], c_j[1], None])
            z_lines.extend([c_i[2], c_j[2], None])
            colors.extend([val, val, None])
            hover_texts.extend([
                f"Conexión: {ni}-{nj}<br>Segmento: {sub_idx}<br>{tipo}: {val:.2f} daN.m",
                f"Conexión: {ni}-{nj}<br>Segmento: {sub_idx}<br>{tipo}: {val:.2f} daN.m",
                None
            ])
    
    # Crear trace con hover
    trace = go.Scatter3d(
        x=x_lines, y=y_lines, z=z_lines,
        mode='lines',
        line=dict(color=colors, colorscale='Jet', cmin=vmin, cmax=vmax, width=5,
                  colorbar=dict(title=f'{tipo} [daN.m]')),
        text=hover_texts,
        hoverinfo='text',
        name='Estructura'
    )
    
    fig = go.Figure(data=[trace])
    fig.update_layout(
        title=f'{tipo} - {hipotesis}',
        scene=dict(
            xaxis_title='X [m]',
            yaxis_title='Y [m]',
            zaxis_title='Z [m]',
            aspectmode='data'
        ),
        height=800
    )
    
    return fig

def generar_diagrama_plotly_2d(geometria, conexiones, valores_subnodos, reacciones, parametros, tipo, hipotesis, escala="lineal"):
    """Genera diagrama 2D interactivo con Plotly"""
    
    n_corta = parametros.get('n_segmentar_conexion_corta')
    n_larga = parametros.get('n_segmentar_conexion_larga')
    percentil = parametros.get('percentil_separacion_corta_larga')
    
    # Calcular umbral
    longitudes = [np.linalg.norm(np.array(geometria.nodos[nj].coordenadas) - np.array(geometria.nodos[ni].coordenadas)) 
                  for ni, nj in conexiones]
    umbral_longitud = np.percentile(longitudes, percentil)
    
    # Preparar datos para hover
    x_lines, z_lines, colors, hover_texts = [], [], [], []
    
    vals = list(valores_subnodos.values())
    vmin, vmax = min(vals), max(vals)
    
    for ni, nj in conexiones:
        ci = np.array(geometria.nodos[ni].coordenadas)
        cj = np.array(geometria.nodos[nj].coordenadas)
        longitud = np.linalg.norm(cj - ci)
        n_subdiv = n_larga if longitud > umbral_longitud else n_corta
        
        for sub_idx in range(n_subdiv):
            t_i = sub_idx / n_subdiv
            t_j = (sub_idx + 1) / n_subdiv
            c_i = ci + t_i * (cj - ci)
            c_j = ci + t_j * (cj - ci)
            
            key = f"{ni}_{nj}_{sub_idx}_i"
            val = valores_subnodos.get(key, 0)
            
            x_lines.extend([c_i[0], c_j[0], None])
            z_lines.extend([c_i[2], c_j[2], None])
            colors.extend([val, val, None])
            hover_texts.extend([
                f"Conexión: {ni}-{nj}<br>Segmento: {sub_idx}<br>{tipo}: {val:.2f} daN.m",
                f"Conexión: {ni}-{nj}<br>Segmento: {sub_idx}<br>{tipo}: {val:.2f} daN.m",
                None
            ])
    
    # Crear trace con hover
    trace = go.Scatter(
        x=x_lines, y=z_lines,
        mode='lines',
        line=dict(color=colors, colorscale='Jet', cmin=vmin, cmax=vmax, width=5,
                  colorbar=dict(title=f'{tipo} [daN.m]')),
        text=hover_texts,
        hoverinfo='text',
        name='Estructura'
    )
    
    fig = go.Figure(data=[trace])
    fig.update_layout(
        title=f'{tipo} - {hipotesis}',
        xaxis_title='X [m]',
        yaxis_title='Z [m]',
        height=800,
        yaxis=dict(scaleanchor="x", scaleratio=1)
    )
    
    return fig

def generar_diagrama_mqnt_plotly(geometria, conexiones, valores_subnodos, reacciones, parametros, hipotesis, graficos_3d=False, escala="lineal"):
    """Genera diagrama combinado Mf, Q, N, T con Plotly"""
    
    # Extraer valores por tipo
    valores_mf, valores_q, valores_n, valores_t = {}, {}, {}, {}
    
    for k, v in valores_subnodos.items():
        if isinstance(v, np.ndarray) and len(v) >= 10:
            My, Mz = v[8], v[9]
            Qy, Qz = v[5], v[6]
            N, Mx = v[4], v[7]
            
            valores_mf[k] = float(np.sqrt(My**2 + Mz**2))
            valores_q[k] = float(np.sqrt(Qy**2 + Qz**2))
            valores_n[k] = float(abs(N))
            valores_t[k] = float(abs(Mx))
    
    # Crear subplots
    from plotly.subplots import make_subplots
    
    if graficos_3d:
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}],
                   [{'type': 'scatter3d'}, {'type': 'scatter3d'}]],
            subplot_titles=('Momento Flector (Mf)', 'Esfuerzo Cortante (Q)',
                           'Esfuerzo Normal (N)', 'Momento Torsor (T)')
        )
        
        configs = [
            (valores_mf, 'Mf', 'daN.m', 1, 1),
            (valores_q, 'Q', 'daN', 1, 2),
            (valores_n, 'N', 'daN', 2, 1),
            (valores_t, 'T', 'daN.m', 2, 2)
        ]
        
        for valores_dict, nombre, unidad, row, col in configs:
            trace = _crear_trace_3d(geometria, conexiones, valores_dict, parametros, nombre, unidad)
            fig.add_trace(trace, row=row, col=col)
    else:
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Momento Flector (Mf)', 'Esfuerzo Cortante (Q)',
                           'Esfuerzo Normal (N)', 'Momento Torsor (T)')
        )
        
        configs = [
            (valores_mf, 'Mf', 'daN.m', 1, 1),
            (valores_q, 'Q', 'daN', 1, 2),
            (valores_n, 'N', 'daN', 2, 1),
            (valores_t, 'T', 'daN.m', 2, 2)
        ]
        
        for valores_dict, nombre, unidad, row, col in configs:
            trace = _crear_trace_2d(geometria, conexiones, valores_dict, parametros, nombre, unidad)
            fig.add_trace(trace, row=row, col=col)
    
    fig.update_layout(height=1000, showlegend=False, title_text=f"Diagramas MQNT - {hipotesis}")
    return fig

def _crear_trace_3d(geometria, conexiones, valores_dict, parametros, nombre, unidad):
    """Crea trace 3D con hover para subplot"""
    n_corta = parametros.get('n_segmentar_conexion_corta')
    n_larga = parametros.get('n_segmentar_conexion_larga')
    percentil = parametros.get('percentil_separacion_corta_larga')
    
    longitudes = [np.linalg.norm(np.array(geometria.nodos[nj].coordenadas) - np.array(geometria.nodos[ni].coordenadas)) 
                  for ni, nj in conexiones]
    umbral_longitud = np.percentile(longitudes, percentil)
    
    x_lines, y_lines, z_lines, colors, hover_texts = [], [], [], [], []
    vals = list(valores_dict.values())
    vmin, vmax = min(vals), max(vals)
    
    for ni, nj in conexiones:
        ci = np.array(geometria.nodos[ni].coordenadas)
        cj = np.array(geometria.nodos[nj].coordenadas)
        longitud = np.linalg.norm(cj - ci)
        n_subdiv = n_larga if longitud > umbral_longitud else n_corta
        
        for sub_idx in range(n_subdiv):
            t_i = sub_idx / n_subdiv
            t_j = (sub_idx + 1) / n_subdiv
            c_i = ci + t_i * (cj - ci)
            c_j = ci + t_j * (cj - ci)
            
            key = f"{ni}_{nj}_{sub_idx}_i"
            val = valores_dict.get(key, 0)
            
            x_lines.extend([c_i[0], c_j[0], None])
            y_lines.extend([c_i[1], c_j[1], None])
            z_lines.extend([c_i[2], c_j[2], None])
            colors.extend([val, val, None])
            hover_texts.extend([
                f"{ni}-{nj} seg{sub_idx}<br>{nombre}: {val:.2f} {unidad}",
                f"{ni}-{nj} seg{sub_idx}<br>{nombre}: {val:.2f} {unidad}",
                None
            ])
    
    return go.Scatter3d(
        x=x_lines, y=y_lines, z=z_lines,
        mode='lines',
        line=dict(color=colors, colorscale='Jet', cmin=vmin, cmax=vmax, width=5),
        text=hover_texts,
        hoverinfo='text'
    )

def _crear_trace_2d(geometria, conexiones, valores_dict, parametros, nombre, unidad):
    """Crea trace 2D con hover para subplot"""
    n_corta = parametros.get('n_segmentar_conexion_corta')
    n_larga = parametros.get('n_segmentar_conexion_larga')
    percentil = parametros.get('percentil_separacion_corta_larga')
    
    longitudes = [np.linalg.norm(np.array(geometria.nodos[nj].coordenadas) - np.array(geometria.nodos[ni].coordenadas)) 
                  for ni, nj in conexiones]
    umbral_longitud = np.percentile(longitudes, percentil)
    
    x_lines, z_lines, colors, hover_texts = [], [], [], []
    vals = list(valores_dict.values())
    vmin, vmax = min(vals), max(vals)
    
    for ni, nj in conexiones:
        ci = np.array(geometria.nodos[ni].coordenadas)
        cj = np.array(geometria.nodos[nj].coordenadas)
        longitud = np.linalg.norm(cj - ci)
        n_subdiv = n_larga if longitud > umbral_longitud else n_corta
        
        for sub_idx in range(n_subdiv):
            t_i = sub_idx / n_subdiv
            t_j = (sub_idx + 1) / n_subdiv
            c_i = ci + t_i * (cj - ci)
            c_j = ci + t_j * (cj - ci)
            
            key = f"{ni}_{nj}_{sub_idx}_i"
            val = valores_dict.get(key, 0)
            
            x_lines.extend([c_i[0], c_j[0], None])
            z_lines.extend([c_i[2], c_j[2], None])
            colors.extend([val, val, None])
            hover_texts.extend([
                f"{ni}-{nj} seg{sub_idx}<br>{nombre}: {val:.2f} {unidad}",
                f"{ni}-{nj} seg{sub_idx}<br>{nombre}: {val:.2f} {unidad}",
                None
            ])
    
    return go.Scatter(
        x=x_lines, y=z_lines,
        mode='lines',
        line=dict(color=colors, colorscale='Jet', cmin=vmin, cmax=vmax, width=5),
        text=hover_texts,
        hoverinfo='text'
    )

# ============================================================================
# MATPLOTLIB PLOTS (STATIC)
# ============================================================================

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d import Axes3D

def generar_diagrama_matplotlib_3d(geometria, conexiones, valores_subnodos, reacciones, parametros, tipo, hipotesis, escala="lineal"):
    """Genera diagrama 3D con matplotlib"""
    
    n_corta = parametros.get('n_segmentar_conexion_corta')
    n_larga = parametros.get('n_segmentar_conexion_larga')
    percentil = parametros.get('percentil_separacion_corta_larga')
    
    if n_corta is None or n_larga is None or percentil is None:
        raise ValueError("Faltan parámetros de subdivisión para generar diagrama")
    
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    x_coords = [n.coordenadas[0] for n in geometria.nodos.values()]
    y_coords = [n.coordenadas[1] for n in geometria.nodos.values()]
    z_coords = [n.coordenadas[2] for n in geometria.nodos.values()]
    
    max_range = max(max(x_coords)-min(x_coords), max(y_coords)-min(y_coords), max(z_coords)-min(z_coords))
    x_c, y_c, z_c = sum(x_coords)/len(x_coords), sum(y_coords)/len(y_coords), sum(z_coords)/len(z_coords)
    
    vals = list(valores_subnodos.values())
    if vals:
        vmin, vmax = min(vals), max(vals)
        if escala == "logaritmica":
            norm = mcolors.LogNorm(vmin=max(vmin, 0.1), vmax=vmax)
        else:
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.jet
        
        # Calcular umbral para determinar n_subdiv por conexión
        longitudes = []
        for ni, nj in conexiones:
            ci = np.array(geometria.nodos[ni].coordenadas)
            cj = np.array(geometria.nodos[nj].coordenadas)
            longitudes.append(np.linalg.norm(cj - ci))
        umbral_longitud = np.percentile(longitudes, percentil)
        
        for ni, nj in conexiones:
            ci = np.array(geometria.nodos[ni].coordenadas)
            cj = np.array(geometria.nodos[nj].coordenadas)
            longitud = np.linalg.norm(cj - ci)
            n_subdiv = n_larga if longitud > umbral_longitud else n_corta
            
            for sub_idx in range(n_subdiv):
                t_i = sub_idx / n_subdiv
                t_j = (sub_idx + 1) / n_subdiv
                c_i = ci + t_i * (cj - ci)
                c_j = ci + t_j * (cj - ci)
                
                val = valores_subnodos.get(f"{ni}_{nj}_{sub_idx}_i", 0)
                ax.plot([c_i[0], c_j[0]], [c_i[1], c_j[1]], [c_i[2], c_j[2]], 
                       color=cmap(norm(val)), linewidth=3)
        
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, label=f'{tipo} [daN.m]', shrink=0.8)
        
        # Etiqueta con valor máximo y mínimo
        ax.text2D(0.02, 0.98, f"Máximo: {vmax:.2f}\nMínimo: {vmin:.2f} daN.m", 
                  transform=ax.transAxes, fontsize=10, fontweight='bold',
                  va='top', ha='left',
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor='none'))

        # Reacciones BASE (hasta 4)
        texto = "REACCIONES BASE:\n"
        for idx, (nombre, reac) in enumerate(reacciones.items()):
            if idx >= 4:
                break
            if idx > 0:
                texto += "\n"
            texto += f"{nombre}:\n"
            texto += f"Fx: {reac['Fx']:.1f} daN\n"
            texto += f"Fy: {reac['Fy']:.1f} daN\n"
            texto += f"Fz: {reac['Fz']:.1f} daN\n"
            texto += f"Mx: {reac['Mx']:.1f} daN·m\n"
            texto += f"My: {reac['My']:.1f} daN·m\n"
            texto += f"Mz: {reac['Mz']:.1f} daN·m"
        ax.text2D(0.02, 0.02, texto, transform=ax.transAxes, fontsize=7, fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor='black'),
                 ha='left', va='bottom')
    
    ax.set_xlim(x_c - max_range/2, x_c + max_range/2)
    ax.set_ylim(y_c - max_range/2, y_c + max_range/2)
    ax.set_zlim(z_c - max_range/2, z_c + max_range/2)
    ax.set_box_aspect([1,1,1])
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    ax.set_title(f'{tipo} - {hipotesis}')
    
    return fig

def generar_diagrama_matplotlib_2d(geometria, conexiones, valores_subnodos, reacciones, parametros, tipo, hipotesis, escala="lineal"):
    """Genera diagrama 2D con matplotlib"""
    
    n_corta = parametros.get('n_segmentar_conexion_corta')
    n_larga = parametros.get('n_segmentar_conexion_larga')
    percentil = parametros.get('percentil_separacion_corta_larga')
    
    if n_corta is None or n_larga is None or percentil is None:
        raise ValueError("Faltan parámetros de subdivisión para generar diagrama")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x_coords = [n.coordenadas[0] for n in geometria.nodos.values()]
    z_coords = [n.coordenadas[2] for n in geometria.nodos.values()]
    max_range = max(max(x_coords)-min(x_coords), max(z_coords)-min(z_coords))
    x_c, z_c = sum(x_coords)/len(x_coords), sum(z_coords)/len(z_coords)
    
    vals = list(valores_subnodos.values())
    if vals:
        vmin, vmax = min(vals), max(vals)
        if escala == "logaritmica":
            norm = mcolors.LogNorm(vmin=max(vmin, 0.1), vmax=vmax)
        else:
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.jet
        
        # Calcular umbral para determinar n_subdiv por conexión
        longitudes = []
        for ni, nj in conexiones:
            ci = np.array(geometria.nodos[ni].coordenadas)
            cj = np.array(geometria.nodos[nj].coordenadas)
            longitudes.append(np.linalg.norm(cj - ci))
        umbral_longitud = np.percentile(longitudes, percentil)
        
        for ni, nj in conexiones:
            ci = np.array(geometria.nodos[ni].coordenadas)
            cj = np.array(geometria.nodos[nj].coordenadas)
            longitud = np.linalg.norm(cj - ci)
            n_subdiv = n_larga if longitud > umbral_longitud else n_corta
            
            for sub_idx in range(n_subdiv):
                t_i = sub_idx / n_subdiv
                t_j = (sub_idx + 1) / n_subdiv
                c_i = ci + t_i * (cj - ci)
                c_j = ci + t_j * (cj - ci)
                
                val = valores_subnodos.get(f"{ni}_{nj}_{sub_idx}_i", 0)
                ax.plot([c_i[0], c_j[0]], [c_i[2], c_j[2]], color=cmap(norm(val)), linewidth=3)
        
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, label=f'{tipo} [daN.m]')
        
        # Etiqueta con valor máximo y mínimo
        ax.text(0.02, 0.98, f"Máximo: {vmax:.2f}\nMínimo: {vmin:.2f} daN.m", 
                transform=ax.transAxes, fontsize=10, fontweight='bold',
                va='top', ha='left',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor='none'))
        
        # Reacciones BASE (hasta 4)
        texto = "REACCIONES BASE:\n"
        for idx, (nombre, reac) in enumerate(reacciones.items()):
            if idx >= 4:
                break
            if idx > 0:
                texto += "\n"
            texto += f"{nombre}:\n"
            texto += f"Fx: {reac['Fx']:.1f} daN\n"
            texto += f"Fy: {reac['Fy']:.1f} daN\n"
            texto += f"Fz: {reac['Fz']:.1f} daN\n"
            texto += f"Mx: {reac['Mx']:.1f} daN·m\n"
            texto += f"My: {reac['My']:.1f} daN·m\n"
            texto += f"Mz: {reac['Mz']:.1f} daN·m"
        ax.text(0.02, 0.02, texto, transform=ax.transAxes, fontsize=7, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor='black'),
               ha='left', va='bottom')
    
    ax.set_xlim(x_c - max_range/2, x_c + max_range/2)
    ax.set_ylim(z_c - max_range/2, z_c + max_range/2)
    ax.set_aspect('equal')
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Z [m]')
    ax.set_title(f'{tipo} - {hipotesis}')
    ax.grid(True, alpha=0.3)
    
    return fig

def generar_diagrama_mqnt_matplotlib(geometria, conexiones, valores_subnodos, reacciones, parametros, hipotesis, graficos_3d=False, escala="lineal"):
    """Genera diagrama combinado MQNT con matplotlib"""
    
    fig = plt.figure(figsize=(16, 12))
    
    # Extraer valores por tipo
    valores_mf, valores_q, valores_n, valores_t = {}, {}, {}, {}
    
    for k, v in valores_subnodos.items():
        if isinstance(v, np.ndarray) and len(v) >= 10:
            My, Mz = v[8], v[9]
            Qy, Qz = v[5], v[6]
            N, Mx = v[4], v[7]
            
            valores_mf[k] = float(np.sqrt(My**2 + Mz**2))
            valores_q[k] = float(np.sqrt(Qy**2 + Qz**2))
            valores_n[k] = float(abs(N))
            valores_t[k] = float(abs(Mx))
    
    configs = [
        (valores_mf, 'Momento Flector (Mf)', 'daN.m', 221),
        (valores_q, 'Esfuerzo Cortante (Q)', 'daN', 222),
        (valores_n, 'Esfuerzo Normal (N)', 'daN', 223),
        (valores_t, 'Momento Torsor (T)', 'daN.m', 224)
    ]
    
    for valores_dict, titulo, unidad, subplot_pos in configs:
        if graficos_3d:
            ax = fig.add_subplot(subplot_pos, projection='3d')
            _dibujar_matplotlib_3d(ax, geometria, conexiones, valores_dict, parametros, titulo, unidad, hipotesis, reacciones, escala)
        else:
            ax = fig.add_subplot(subplot_pos)
            _dibujar_matplotlib_2d(ax, geometria, conexiones, valores_dict, parametros, titulo, unidad, hipotesis, reacciones, escala)
    
    plt.tight_layout()
    return fig

def _dibujar_matplotlib_3d(ax, geometria, conexiones, valores_dict, parametros, titulo, unidad, hipotesis, reacciones, escala="lineal"):
    """Dibuja subplot 3D con matplotlib"""
    n_corta = parametros.get('n_segmentar_conexion_corta')
    n_larga = parametros.get('n_segmentar_conexion_larga')
    percentil = parametros.get('percentil_separacion_corta_larga')
    
    if n_corta is None or n_larga is None or percentil is None:
        raise ValueError("Faltan parámetros de subdivisión para dibujar")
    
    x_coords = [n.coordenadas[0] for n in geometria.nodos.values()]
    y_coords = [n.coordenadas[1] for n in geometria.nodos.values()]
    z_coords = [n.coordenadas[2] for n in geometria.nodos.values()]
    
    max_range = max(max(x_coords)-min(x_coords), max(y_coords)-min(y_coords), max(z_coords)-min(z_coords))
    x_c, y_c, z_c = sum(x_coords)/len(x_coords), sum(y_coords)/len(y_coords), sum(z_coords)/len(z_coords)
    
    vals = list(valores_dict.values())
    if vals:
        vmin, vmax = min(vals), max(vals)
        if escala == "logaritmica":
            norm = mcolors.LogNorm(vmin=max(vmin, 0.1), vmax=vmax)
        else:
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.jet
        
        # Calcular umbral
        longitudes = []
        for ni, nj in conexiones:
            ci = np.array(geometria.nodos[ni].coordenadas)
            cj = np.array(geometria.nodos[nj].coordenadas)
            longitudes.append(np.linalg.norm(cj - ci))
        umbral_longitud = np.percentile(longitudes, percentil)
        
        for ni, nj in conexiones:
            ci = np.array(geometria.nodos[ni].coordenadas)
            cj = np.array(geometria.nodos[nj].coordenadas)
            longitud = np.linalg.norm(cj - ci)
            n_subdiv = n_larga if longitud > umbral_longitud else n_corta
            
            for sub_idx in range(n_subdiv):
                t_i = sub_idx / n_subdiv
                t_j = (sub_idx + 1) / n_subdiv
                c_i = ci + t_i * (cj - ci)
                c_j = ci + t_j * (cj - ci)
                
                key = f"{ni}_{nj}_{sub_idx}_i"
                val = valores_dict.get(key, 0)
                ax.plot([c_i[0], c_j[0]], [c_i[1], c_j[1]], [c_i[2], c_j[2]], 
                       color=cmap(norm(val)), linewidth=3)
        
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, label=f'{unidad}', shrink=0.6)
        
        # Etiqueta con valor máximo y mínimo
        ax.text2D(0.02, 0.98, f"Máximo: {vmax:.2f}\nMínimo: {vmin:.2f} {unidad}", 
                  transform=ax.transAxes, fontsize=10, fontweight='bold',
                  va='top', ha='left',
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor='none'))
    
    ax.set_xlim(x_c - max_range/2, x_c + max_range/2)
    ax.set_ylim(y_c - max_range/2, y_c + max_range/2)
    ax.set_zlim(z_c - max_range/2, z_c + max_range/2)
    ax.set_box_aspect([1,1,1])
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    ax.set_title(f'{titulo} - {hipotesis}')

def _dibujar_matplotlib_2d(ax, geometria, conexiones, valores_dict, parametros, titulo, unidad, hipotesis, reacciones, escala="lineal"):
    """Dibuja subplot 2D con matplotlib"""
    n_corta = parametros.get('n_segmentar_conexion_corta')
    n_larga = parametros.get('n_segmentar_conexion_larga')
    percentil = parametros.get('percentil_separacion_corta_larga')
    
    if n_corta is None or n_larga is None or percentil is None:
        raise ValueError("Faltan parámetros de subdivisión para dibujar")
    
    x_coords = [n.coordenadas[0] for n in geometria.nodos.values()]
    z_coords = [n.coordenadas[2] for n in geometria.nodos.values()]
    max_range = max(max(x_coords)-min(x_coords), max(z_coords)-min(z_coords))
    x_c, z_c = sum(x_coords)/len(x_coords), sum(z_coords)/len(z_coords)
    
    vals = list(valores_dict.values())
    if vals:
        vmin, vmax = min(vals), max(vals)
        if escala == "logaritmica":
            norm = mcolors.LogNorm(vmin=max(vmin, 0.1), vmax=vmax)
        else:
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.jet
        
        # Calcular umbral
        longitudes = []
        for ni, nj in conexiones:
            ci = np.array(geometria.nodos[ni].coordenadas)
            cj = np.array(geometria.nodos[nj].coordenadas)
            longitudes.append(np.linalg.norm(cj - ci))
        umbral_longitud = np.percentile(longitudes, percentil)
        
        for ni, nj in conexiones:
            ci = np.array(geometria.nodos[ni].coordenadas)
            cj = np.array(geometria.nodos[nj].coordenadas)
            longitud = np.linalg.norm(cj - ci)
            n_subdiv = n_larga if longitud > umbral_longitud else n_corta
            
            for sub_idx in range(n_subdiv):
                t_i = sub_idx / n_subdiv
                t_j = (sub_idx + 1) / n_subdiv
                c_i = ci + t_i * (cj - ci)
                c_j = ci + t_j * (cj - ci)
                
                key = f"{ni}_{nj}_{sub_idx}_i"
                val = valores_dict.get(key, 0)
                ax.plot([c_i[0], c_j[0]], [c_i[2], c_j[2]], color=cmap(norm(val)), linewidth=3)
        
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, label=f'{unidad}')
        
        # Etiqueta con valor máximo y mínimo
        ax.text(0.02, 0.98, f"Máximo: {vmax:.2f}\nMínimo: {vmin:.2f} {unidad}", 
                transform=ax.transAxes, fontsize=10, fontweight='bold',
                va='top', ha='left',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor='none'))
    
    ax.set_xlim(x_c - max_range/2, x_c + max_range/2)
    ax.set_ylim(z_c - max_range/2, z_c + max_range/2)
    ax.set_aspect('equal')
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Z [m]')
    ax.set_title(f'{titulo} - {hipotesis}')
    ax.grid(True, alpha=0.3)

def generar_diagrama_ejes_locales_matplotlib(geometria, conexiones, elementos_dict, hipotesis):
    """Genera diagrama 3D mostrando ejes locales de elementos"""
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    x_coords = [n.coordenadas[0] for n in geometria.nodos.values()]
    y_coords = [n.coordenadas[1] for n in geometria.nodos.values()]
    z_coords = [n.coordenadas[2] for n in geometria.nodos.values()]
    
    max_range = max(max(x_coords)-min(x_coords), max(y_coords)-min(y_coords), max(z_coords)-min(z_coords))
    x_c, y_c, z_c = sum(x_coords)/len(x_coords), sum(y_coords)/len(y_coords), sum(z_coords)/len(z_coords)
    
    # Dibujar estructura
    for ni, nj in conexiones:
        ci = np.array(geometria.nodos[ni].coordenadas)
        cj = np.array(geometria.nodos[nj].coordenadas)
        ax.plot([ci[0], cj[0]], [ci[1], cj[1]], [ci[2], cj[2]], 'k-', linewidth=2, alpha=0.3)
    
    # Dibujar ejes locales (cada 3 elementos para claridad)
    escala = max_range * 0.1
    for eid, data in list(elementos_dict.items())[::3]:
        ni, nj, _ = data['origen']
        ci = np.array(geometria.nodos[ni].coordenadas)
        cj = np.array(geometria.nodos[nj].coordenadas)
        centro = (ci + cj) / 2
        
        ejes = data['ejes_locales']
        
        # Eje X local (rojo) - dirección del elemento
        ax.quiver(centro[0], centro[1], centro[2],
                 ejes[0,0]*escala, ejes[1,0]*escala, ejes[2,0]*escala,
                 color='red', arrow_length_ratio=0.3, linewidth=2)
        
        # Eje Y local (verde)
        ax.quiver(centro[0], centro[1], centro[2],
                 ejes[0,1]*escala, ejes[1,1]*escala, ejes[2,1]*escala,
                 color='green', arrow_length_ratio=0.3, linewidth=2)
        
        # Eje Z local (azul)
        ax.quiver(centro[0], centro[1], centro[2],
                 ejes[0,2]*escala, ejes[1,2]*escala, ejes[2,2]*escala,
                 color='blue', arrow_length_ratio=0.3, linewidth=2)
    
    ax.set_xlim(x_c - max_range/2, x_c + max_range/2)
    ax.set_ylim(y_c - max_range/2, y_c + max_range/2)
    ax.set_zlim(z_c - max_range/2, z_c + max_range/2)
    ax.set_box_aspect([1,1,1])
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    ax.set_title(f'Ejes Locales de Elementos - {hipotesis}\nRojo=X(long), Verde=Y, Azul=Z')
    
    return fig
