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
    
    # Dibujar estructura base (conexiones)
    if hasattr(estructura_geometria, 'conexiones'):
        for origen, destino, tipo in estructura_geometria.conexiones:
            if origen not in estructura_geometria.nodos or destino not in estructura_geometria.nodos:
                continue
            
            nodo_o = estructura_geometria.nodos[origen]
            nodo_d = estructura_geometria.nodos[destino]
            x_o, y_o, z_o = nodo_o.coordenadas
            x_d, y_d, z_d = nodo_d.coordenadas
            
            fig.add_trace(go.Scatter(
                x=[x_o, x_d],
                y=[z_o, z_d],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Obtener altura máxima
    altura_max = max([coords[2] for coords in estructura_geometria.nodes_key.values()])
    
    # Calcular anchos de zonas
    ancho_d = servidumbre_obj.d
    theta_rad = math.radians(servidumbre_obj.theta_max)
    ancho_proyeccion = (servidumbre_obj.Lk + servidumbre_obj.fi) * math.sin(theta_rad)
    
    # Zona A (total) - fondo gris transparente
    fig.add_shape(
        type="rect",
        x0=-servidumbre_obj.A/2, x1=servidumbre_obj.A/2,
        y0=0, y1=altura_max,
        fillcolor="rgba(200,200,200,0.3)",
        line=dict(width=2, color="gray", dash="dash"),
        layer="below"
    )
    
    # Zonas d (seguridad) - externas rojas
    fig.add_shape(
        type="rect",
        x0=-servidumbre_obj.A/2, x1=-servidumbre_obj.A/2 + ancho_d,
        y0=0, y1=altura_max,
        fillcolor="rgba(255,200,200,0.4)",
        line=dict(width=1, color="red"),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=servidumbre_obj.A/2 - ancho_d, x1=servidumbre_obj.A/2,
        y0=0, y1=altura_max,
        fillcolor="rgba(255,200,200,0.4)",
        line=dict(width=1, color="red"),
        layer="below"
    )
    
    # Zonas Proyección - intermedias verdes
    fig.add_shape(
        type="rect",
        x0=-servidumbre_obj.A/2 + ancho_d, 
        x1=-servidumbre_obj.A/2 + ancho_d + ancho_proyeccion,
        y0=0, y1=altura_max,
        fillcolor="rgba(200,255,200,0.4)",
        line=dict(width=1, color="green"),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=servidumbre_obj.A/2 - ancho_d - ancho_proyeccion,
        x1=servidumbre_obj.A/2 - ancho_d,
        y0=0, y1=altura_max,
        fillcolor="rgba(200,255,200,0.4)",
        line=dict(width=1, color="green"),
        layer="below"
    )
    
    # Zona C (central) - azul
    if servidumbre_obj.C > 0:
        fig.add_shape(
            type="rect",
            x0=-servidumbre_obj.C/2, x1=servidumbre_obj.C/2,
            y0=0, y1=altura_max,
            fillcolor="rgba(200,200,255,0.4)",
            line=dict(width=1, color="blue"),
            layer="below"
        )
    
    # Anotación con ancho total
    fig.add_annotation(
        x=0, y=altura_max + 1,
        text=f"A = {servidumbre_obj.A:.2f} m",
        showarrow=False,
        font=dict(size=14, color="black", family="Arial Black")
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
            gridcolor='rgba(200, 200, 200, 0.3)'
        ),
        yaxis=dict(
            title='Z [m]',
            zeroline=False,
            gridcolor='rgba(200, 200, 200, 0.3)'
        ),
        hovermode='closest',
        showlegend=False,
        width=1200,
        height=800,
        plot_bgcolor='white'
    )
    
    return fig
