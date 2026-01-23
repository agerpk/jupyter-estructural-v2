"""Gráfico de estructura con zonas de servidumbre"""

import math
import plotly.graph_objects as go


def graficar_servidumbre(estructura_geometria, servidumbre_obj, usar_plotly=True):
    """
    Genera gráfico de estructura con zonas de servidumbre superpuestas
    
    Args:
        estructura_geometria: Objeto EstructuraAEA_Geometria
        servidumbre_obj: Objeto ServidumbreAEA con cálculos
        usar_plotly: Si True usa Plotly, si False usa Matplotlib
    
    Returns:
        Figura Plotly con estructura y zonas de servidumbre
    """
    if not usar_plotly:
        raise NotImplementedError("Solo Plotly soportado para servidumbre")
    
    fig = go.Figure()
    
    Lk = estructura_geometria.lk
    theta_max = servidumbre_obj.theta_max
    theta_rad = math.radians(theta_max)
    fi = servidumbre_obj.fi
    
            # Dibujar estructura completa
    conductores_extremos = []
    for nombre, nodo in estructura_geometria.nodos.items():
        x, y, z = nodo.coordenadas
        
        if nodo.tipo_nodo == "conductor":
            # Guardar conductores extremos (mayor |x|)
            if abs(x) > 0.1:
                conductores_extremos.append((nombre, nodo, x))
            
            # Nodo conductor
            fig.add_trace(go.Scatter(
                x=[x], y=[z],
                mode='markers',
                marker=dict(size=8, color='#1f77b4'),
                name='Conductor',
                showlegend=False,
                hovertemplate=f'<b>{nombre}</b><br>x={x:.2f}m<br>z={z:.2f}m<extra></extra>'
            ))
            
        elif nodo.tipo_nodo == "guardia":
            # Nodo guardia
            fig.add_trace(go.Scatter(
                x=[x], y=[z],
                mode='markers',
                marker=dict(size=8, color='#2ca02c'),
                name='Guardia',
                showlegend=False,
                hovertemplate=f'<b>{nombre}</b><br>x={x:.2f}m<br>z={z:.2f}m<extra></extra>'
            ))
        
        elif nodo.tipo_nodo in ["columna", "mensula", "cruceta"]:
            # Nodos estructura
            fig.add_trace(go.Scatter(
                x=[x], y=[z],
                mode='markers',
                marker=dict(size=6, color='black'),
                showlegend=False,
                hovertemplate=f'<b>{nombre}</b><br>x={x:.2f}m<br>z={z:.2f}m<extra></extra>'
            ))
    
    # Encontrar conductor extremo x positivo
    cond_extremo_pos = max([c for c in conductores_extremos if c[2] > 0], key=lambda c: c[2]) if any(c[2] > 0 for c in conductores_extremos) else None
    
    # Dibujar Lk y fmax solo para conductor extremo x positivo
    if cond_extremo_pos:
        nombre, nodo, x = cond_extremo_pos
        x_amarre, y_amarre, z_amarre = nodo.coordenadas
        
        # Cadena Lk
        x_extremo_cadena = x_amarre + Lk * math.sin(theta_rad)
        z_extremo_cadena = z_amarre - Lk * math.cos(theta_rad)
        fig.add_trace(go.Scatter(
            x=[x_amarre, x_extremo_cadena],
            y=[z_amarre, z_extremo_cadena],
            mode='lines',
            line=dict(color='gray', width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Flecha máxima
        x_extremo_flecha = x_extremo_cadena + fi * math.sin(theta_rad)
        z_extremo_flecha = z_extremo_cadena - fi * math.cos(theta_rad)
        fig.add_trace(go.Scatter(
            x=[x_extremo_cadena, x_extremo_flecha],
            y=[z_extremo_cadena, z_extremo_flecha],
            mode='lines',
            line=dict(color='red', width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Patch rojo en extremo de cadena
        fig.add_trace(go.Scatter(
            x=[x_extremo_cadena],
            y=[z_extremo_cadena],
            mode='markers',
            marker=dict(size=10, color='red', symbol='circle'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Cotas Lk y fmax
        x_medio_lk = (x_amarre + x_extremo_cadena) / 2
        z_medio_lk = (z_amarre + z_extremo_cadena) / 2
        fig.add_annotation(
            x=x_medio_lk + 0.5,
            y=z_medio_lk,
            text=f'<b>Lk={Lk:.2f}m</b>',
            showarrow=False,
            xanchor='left',
            font=dict(size=10, color='black'),
            bgcolor='white',
            borderpad=3
        )
        
        x_medio_fi = (x_extremo_cadena + x_extremo_flecha) / 2
        z_medio_fi = (z_extremo_cadena + z_extremo_flecha) / 2
        fig.add_annotation(
            x=x_medio_fi + 0.5,
            y=z_medio_fi,
            text=f'<b>fmax={fi:.2f}m</b>',
            showarrow=False,
            xanchor='left',
            font=dict(size=10, color='black'),
            bgcolor='white',
            borderpad=3
        )
    
    # Dibujar Lk y fmax para todos los demás conductores (sin cotas)
    for nombre, nodo, x in conductores_extremos:
        if cond_extremo_pos and nombre == cond_extremo_pos[0]:
            continue
        
        x_amarre, y_amarre, z_amarre = nodo.coordenadas
        signo = 1 if x > 0 else -1
        
        # Cadena Lk
        x_extremo_cadena = x_amarre + signo * Lk * math.sin(theta_rad)
        z_extremo_cadena = z_amarre - Lk * math.cos(theta_rad)
        fig.add_trace(go.Scatter(
            x=[x_amarre, x_extremo_cadena],
            y=[z_amarre, z_extremo_cadena],
            mode='lines',
            line=dict(color='gray', width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Flecha máxima
        x_extremo_flecha = x_extremo_cadena + signo * fi * math.sin(theta_rad)
        z_extremo_flecha = z_extremo_cadena - fi * math.cos(theta_rad)
        fig.add_trace(go.Scatter(
            x=[x_extremo_cadena, x_extremo_flecha],
            y=[z_extremo_cadena, z_extremo_flecha],
            mode='lines',
            line=dict(color='red', width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Patch rojo
        fig.add_trace(go.Scatter(
            x=[x_extremo_cadena],
            y=[z_extremo_cadena],
            mode='markers',
            marker=dict(size=10, color='red', symbol='circle'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Dibujar conexiones de estructura
    for conexion in estructura_geometria.conexiones:
        nodo1 = estructura_geometria.nodos[conexion[0]]
        nodo2 = estructura_geometria.nodos[conexion[1]]
        x1, y1, z1 = nodo1.coordenadas
        x2, y2, z2 = nodo2.coordenadas
        
        fig.add_trace(go.Scatter(
            x=[x1, x2],
            y=[z1, z2],
            mode='lines',
            line=dict(color='black', width=3),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Obtener altura máxima y mínima
    altura_max = max([coords[2] for coords in estructura_geometria.nodes_key.values()])
    z_min = -5
    
    # Calcular anchos de zonas
    ancho_d = servidumbre_obj.d
    ancho_proyeccion = (Lk + fi) * math.sin(theta_rad)
    
    # Zona C (exterior) - amarillo
    if servidumbre_obj.C > 0:
        fig.add_shape(
            type="rect",
            x0=-servidumbre_obj.C/2, x1=servidumbre_obj.C/2,
            y0=0, y1=altura_max,
            fillcolor="rgba(255,255,0,0.2)",
            line=dict(width=0),
            layer="below"
        )
        fig.add_annotation(
            x=0, y=-2,
            text=f"<b>C = {servidumbre_obj.C:.2f} m</b>",
            showarrow=False,
            font=dict(size=10, color="black"),
            bgcolor='white',
            borderpad=2
        )
    
    # Zona A (intermedia) - naranja
    fig.add_shape(
        type="rect",
        x0=-servidumbre_obj.A/2, x1=servidumbre_obj.A/2,
        y0=0, y1=altura_max,
        fillcolor="rgba(255,165,0,0.2)",
        line=dict(width=0),
        layer="below"
    )
    fig.add_annotation(
        x=0, y=altura_max + 2,
        text=f"<b>A = {servidumbre_obj.A:.2f} m</b>",
        showarrow=False,
        font=dict(size=12, color="black"),
        bgcolor='white',
        borderpad=3
    )
    
    # Zonas d (central) - rojo
    fig.add_shape(
        type="rect",
        x0=-servidumbre_obj.A/2, x1=-servidumbre_obj.A/2 + ancho_d,
        y0=0, y1=altura_max,
        fillcolor="rgba(255,0,0,0.2)",
        line=dict(width=0),
        layer="below"
    )
    fig.add_annotation(
        x=-servidumbre_obj.A/2 + ancho_d/2, y=-2,
        text=f"<b>d = {ancho_d:.2f} m</b>",
        showarrow=False,
        font=dict(size=10, color="black"),
        bgcolor='white',
        borderpad=2
    )
    
    fig.add_shape(
        type="rect",
        x0=servidumbre_obj.A/2 - ancho_d, x1=servidumbre_obj.A/2,
        y0=0, y1=altura_max,
        fillcolor="rgba(255,0,0,0.2)",
        line=dict(width=0),
        layer="below"
    )
    fig.add_annotation(
        x=servidumbre_obj.A/2 - ancho_d/2, y=-2,
        text=f"<b>d = {ancho_d:.2f} m</b>",
        showarrow=False,
        font=dict(size=10, color="black"),
        bgcolor='white',
        borderpad=2
    )
    
    # Cotas de Proyección
    fig.add_annotation(
        x=-servidumbre_obj.A/2 + ancho_d + ancho_proyeccion/2, y=-2,
        text=f"<b>Proy = {ancho_proyeccion:.2f} m</b>",
        showarrow=False,
        font=dict(size=10, color="black"),
        bgcolor='white',
        borderpad=2
    )
    
    fig.add_annotation(
        x=servidumbre_obj.A/2 - ancho_d - ancho_proyeccion/2, y=-2,
        text=f"<b>Proy = {ancho_proyeccion:.2f} m</b>",
        showarrow=False,
        font=dict(size=10, color="black"),
        bgcolor='white',
        borderpad=2
    )
    
    # Línea de terreno
    fig.add_shape(
        type='line',
        x0=-servidumbre_obj.A/2 - 2, x1=servidumbre_obj.A/2 + 2,
        y0=0, y1=0,
        line=dict(color='brown', width=3)
    )
    
    # Configurar layout
    fig.update_layout(
        title=dict(
            text=f"FRANJA DE SERVIDUMBRE AEA-95301-2007<br>{estructura_geometria.tension_nominal}kV - {estructura_geometria.tipo_estructura.upper()}",
            font=dict(size=14, family="Arial Black")
        ),
        xaxis=dict(
            title='X [m]',
            scaleanchor='y',
            scaleratio=1,
            zeroline=False,
            gridcolor='rgba(200, 200, 200, 0.3)',
            dtick=2.0
        ),
        yaxis=dict(
            title='Z [m]',
            zeroline=False,
            gridcolor='rgba(200, 200, 200, 0.3)',
            dtick=2.0
        ),
        hovermode='closest',
        showlegend=False,
        width=1200,
        height=800,
        plot_bgcolor='white'
    )
    
    return fig
