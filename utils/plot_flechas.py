"""
Módulo para plotear flechas de cables en estados climáticos
"""

import plotly.graph_objects as go
import numpy as np


def crear_grafico_flechas(resultados_conductor, resultados_guardia, L_vano):
    """
    Crear tres gráficos de flechas para diferentes estados climáticos
    
    Args:
        resultados_conductor: Diccionario con resultados del conductor por estado
        resultados_guardia: Diccionario con resultados del guardia por estado
        L_vano: Longitud del vano en metros
    
    Returns:
        Tupla con tres figuras de Plotly (combinado, conductor, guardia)
    """
    
    # Colores para cada estado
    colores = {
        "I": "#FF6B6B",    # Rojo - Tmáx
        "II": "#4ECDC4",   # Turquesa - Tmín
        "III": "#45B7D1",  # Azul - Vmáx
        "IV": "#FFA07A",   # Naranja - Vmed
        "V": "#98D8C8"     # Verde - TMA
    }
    
    # Generar puntos para la catenaria
    x = np.linspace(0, L_vano, 100)
    
    # Crear tres figuras
    fig_combinado = go.Figure()
    fig_conductor = go.Figure()
    fig_guardia = go.Figure()
    
    # Plotear conductor en ambos gráficos (combinado y solo conductor)
    for estado_id, resultado in resultados_conductor.items():
        flecha = resultado["flecha_vertical_m"]
        descripcion = resultado.get("descripcion", estado_id)
        
        y = 4 * flecha * x * (L_vano - x) / (L_vano ** 2)
        
        # Gráfico combinado
        fig_combinado.add_trace(go.Scatter(
            x=x,
            y=y,  # Positivo para que vaya hacia abajo
            mode='lines',
            name=f'Conductor - Estado {estado_id} ({descripcion})',
            line=dict(color=colores.get(estado_id, "#000000"), width=2),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
        ))
        
        # Gráfico solo conductor
        fig_conductor.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines',
            name=f'Estado {estado_id} ({descripcion})',
            line=dict(color=colores.get(estado_id, "#000000"), width=2),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
        ))
    
    # Plotear guardia en ambos gráficos (combinado y solo guardia)
    for estado_id, resultado in resultados_guardia.items():
        flecha = resultado["flecha_vertical_m"]
        descripcion = resultado.get("descripcion", estado_id)
        
        y = 4 * flecha * x * (L_vano - x) / (L_vano ** 2)
        
        # Gráfico combinado
        fig_combinado.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines',
            name=f'Guardia - Estado {estado_id} ({descripcion})',
            line=dict(color=colores.get(estado_id, "#000000"), width=2, dash='dash'),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
        ))
        
        # Gráfico solo guardia
        fig_guardia.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines',
            name=f'Estado {estado_id} ({descripcion})',
            line=dict(color=colores.get(estado_id, "#000000"), width=2),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
        ))
    
    # Agregar línea de apoyos a todas las figuras
    for fig in [fig_combinado, fig_conductor, fig_guardia]:
        fig.add_trace(go.Scatter(
            x=[0, L_vano],
            y=[0, 0],
            mode='lines',
            name='Apoyos',
            line=dict(color='black', width=3),
            showlegend=False
        ))
    
    # Configurar layout común
    layout_config = dict(
        xaxis_title='Vano (m)',
        yaxis_title='Flecha (m)',
        hovermode='closest',
        legend=dict(
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        ),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        font=dict(size=12),
        height=500,
        margin=dict(r=250)
    )
    
    # Configurar ejes común
    axes_config_x = dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='black'
    )
    
    axes_config_y = dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='black',
        autorange='reversed'  # Invertir eje Y para que vaya hacia abajo
    )
    
    # Aplicar configuración a cada figura
    fig_combinado.update_layout(title='Flechas de Cables - Conductor y Guardia', **layout_config)
    fig_combinado.update_xaxes(**axes_config_x)
    fig_combinado.update_yaxes(**axes_config_y)
    
    fig_conductor.update_layout(title='Flechas de Conductor por Estado Climático', **layout_config)
    fig_conductor.update_xaxes(**axes_config_x)
    fig_conductor.update_yaxes(**axes_config_y)
    
    fig_guardia.update_layout(title='Flechas de Cable de Guardia por Estado Climático', **layout_config)
    fig_guardia.update_xaxes(**axes_config_x)
    fig_guardia.update_yaxes(**axes_config_y)
    
    return fig_combinado, fig_conductor, fig_guardia
