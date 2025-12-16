"""
Módulo para plotear flechas de cables en estados climáticos
"""

import plotly.graph_objects as go
import numpy as np


def crear_grafico_flechas(cable_conductor, cable_guardia1, L_vano, cable_guardia2=None):
    """
    Crear gráficos de flechas usando datos de catenarias cacheadas
    
    Args:
        cable_conductor: Objeto Cable_AEA del conductor con catenarias_cache
        cable_guardia1: Objeto Cable_AEA del guardia 1 con catenarias_cache
        L_vano: Longitud del vano en metros
        cable_guardia2: Objeto Cable_AEA del guardia 2 con catenarias_cache (opcional)
    
    Returns:
        Tupla con figuras de Plotly (combinado, conductor, guardia1, guardia2 si existe)
    """
    
    # Colores por tipo de cable y estado
    colores_conductor = {
        "I": "#DC143C",    # Rojo oscuro - Tmáx
        "II": "#FF6347",   # Rojo tomate - Tmín
        "III": "#B22222",  # Rojo ladrillo - Vmáx
        "IV": "#CD5C5C",   # Rojo indio - Vmed
        "V": "#F08080"     # Rojo claro - TMA
    }
    
    colores_guardia1 = {
        "I": "#191970",    # Azul medianoche - Tmáx
        "II": "#4169E1",   # Azul real - Tmín
        "III": "#0000CD",  # Azul medio - Vmáx
        "IV": "#6495ED",   # Azul aciano - Vmed
        "V": "#87CEEB"     # Azul cielo - TMA
    }
    
    colores_guardia2 = {
        "I": "#006400",    # Verde oscuro - Tmáx
        "II": "#228B22",   # Verde bosque - Tmín
        "III": "#32CD32",  # Verde lima - Vmáx
        "IV": "#90EE90",   # Verde claro - Vmed
        "V": "#98FB98"     # Verde pálido - TMA
    }
    
    # Colores genéricos para gráficos individuales
    colores = {
        "I": "#FF6B6B",    # Rojo - Tmáx
        "II": "#4ECDC4",   # Turquesa - Tmín
        "III": "#45B7D1",  # Azul - Vmáx
        "IV": "#FFA07A",   # Naranja - Vmed
        "V": "#98D8C8"     # Verde - TMA
    }
    
    # Crear figuras
    fig_combinado = go.Figure()
    fig_conductor = go.Figure()
    fig_guardia1 = go.Figure()
    fig_guardia2 = go.Figure() if cable_guardia2 else None
    
    # Función auxiliar para plotear catenaria
    def plotear_catenaria(fig, estado_id, cat_data, nombre, color, dash=None, incluir_x_max=False):
        x = cat_data['x']
        y = cat_data['y']
        idx_max = np.argmax(y)
        x_max = x[idx_max]
        nombre_con_x = f"{nombre} (x={x_max:.1f}m)" if incluir_x_max else nombre
        fig.add_trace(go.Scatter(
            x=x, y=y, mode='lines', name=nombre_con_x,
            line=dict(color=color, width=2, dash=dash) if dash else dict(color=color, width=2),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
        ))
    
    # Plotear conductor
    for estado_id, cat_estados in cable_conductor.catenarias_cache.items():
        cat_data = cat_estados['catenaria_posterior']
        plotear_catenaria(fig_combinado, estado_id, cat_data, 
                         f'Conductor - Estado {estado_id}', colores_conductor.get(estado_id, "#DC143C"))
        plotear_catenaria(fig_conductor, estado_id, cat_data,
                         f'Estado {estado_id}', colores.get(estado_id, "#000000"), incluir_x_max=True)
        # Marcar punto de máxima flecha
        idx_max = np.argmax(cat_data['y'])
        fig_combinado.add_trace(go.Scatter(x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
                                          mode='markers', marker=dict(color='orange', size=8),
                                          showlegend=False, hoverinfo='skip'))
        fig_conductor.add_trace(go.Scatter(x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
                                          mode='markers', marker=dict(color='orange', size=8),
                                          showlegend=False, hoverinfo='skip'))
    
    # Plotear guardia1
    for estado_id, cat_estados in cable_guardia1.catenarias_cache.items():
        cat_data = cat_estados['catenaria_posterior']
        plotear_catenaria(fig_combinado, estado_id, cat_data,
                         f'Guardia 1 - Estado {estado_id}', colores_guardia1.get(estado_id, "#191970"), 'dash')
        plotear_catenaria(fig_guardia1, estado_id, cat_data,
                         f'Estado {estado_id}', colores.get(estado_id, "#000000"), incluir_x_max=True)
        # Marcar punto de máxima flecha
        idx_max = np.argmax(cat_data['y'])
        fig_combinado.add_trace(go.Scatter(x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
                                          mode='markers', marker=dict(color='orange', size=8),
                                          showlegend=False, hoverinfo='skip'))
        fig_guardia1.add_trace(go.Scatter(x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
                                          mode='markers', marker=dict(color='orange', size=8),
                                          showlegend=False, hoverinfo='skip'))
    
    # Plotear guardia2 si existe
    if cable_guardia2:
        for estado_id, cat_estados in cable_guardia2.catenarias_cache.items():
            cat_data = cat_estados['catenaria_posterior']
            plotear_catenaria(fig_combinado, estado_id, cat_data,
                             f'Guardia 2 - Estado {estado_id}', colores_guardia2.get(estado_id, "#006400"), 'dot')
            plotear_catenaria(fig_guardia2, estado_id, cat_data,
                             f'Estado {estado_id}', colores.get(estado_id, "#000000"), incluir_x_max=True)
            # Marcar punto de máxima flecha
            idx_max = np.argmax(cat_data['y'])
            fig_combinado.add_trace(go.Scatter(x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
                                              mode='markers', marker=dict(color='orange', size=8),
                                              showlegend=False, hoverinfo='skip'))
            fig_guardia2.add_trace(go.Scatter(x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
                                              mode='markers', marker=dict(color='orange', size=8),
                                              showlegend=False, hoverinfo='skip'))
    
    # Agregar línea de apoyos a todas las figuras
    figs = [fig_combinado, fig_conductor, fig_guardia1]
    if fig_guardia2:
        figs.append(fig_guardia2)
    
    for fig in figs:
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
        autorange='reversed'
    )
    
    # Aplicar configuración a cada figura
    fig_combinado.update_layout(title='Flechas de Cables - Conductor y Guardia', **layout_config)
    fig_combinado.update_xaxes(**axes_config_x)
    fig_combinado.update_yaxes(**axes_config_y)
    
    fig_conductor.update_layout(title='Flechas de Conductor por Estado Climático', **layout_config)
    fig_conductor.update_xaxes(**axes_config_x)
    fig_conductor.update_yaxes(**axes_config_y)
    
    fig_guardia1.update_layout(title='Flechas de Cable de Guardia 1 por Estado Climático', **layout_config)
    fig_guardia1.update_xaxes(**axes_config_x)
    fig_guardia1.update_yaxes(**axes_config_y)
    
    if fig_guardia2:
        fig_guardia2.update_layout(title='Flechas de Cable de Guardia 2 por Estado Climático', **layout_config)
        fig_guardia2.update_xaxes(**axes_config_x)
        fig_guardia2.update_yaxes(**axes_config_y)
        return fig_combinado, fig_conductor, fig_guardia1, fig_guardia2
    
    return fig_combinado, fig_conductor, fig_guardia1
