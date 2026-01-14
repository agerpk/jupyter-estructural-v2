"""
Módulo para plotear flechas de cables en estados climáticos
"""

import plotly.graph_objects as go
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors


def generar_colores_estados(estados_climaticos):
    """
    Genera colores dinámicos usando colormap según cantidad de estados
    
    Args:
        estados_climaticos: Dict con estados {id: {temperatura, descripcion, ...}}
    
    Returns:
        Dict con {estado_id: color_hex}
    """
    estados_ids = sorted(estados_climaticos.keys(), key=lambda x: int(x))
    n_estados = len(estados_ids)
    
    cmap = cm.get_cmap('tab10' if n_estados <= 10 else 'tab20', n_estados)
    
    colores = {}
    for i, estado_id in enumerate(estados_ids):
        colores[estado_id] = mcolors.to_hex(cmap(i))
    
    return colores


def crear_grafico_flechas(cable_conductor, cable_guardia1, L_vano, cable_guardia2=None, estados_climaticos=None):
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
    
    # Obtener estados climáticos
    if estados_climaticos is None:
        estados_climaticos = {}
        if hasattr(cable_conductor, 'estados_climaticos'):
            estados_climaticos = cable_conductor.estados_climaticos
    
    # DEBUG: Imprimir estados para verificar
    print(f"DEBUG plot_flechas: estados_climaticos keys = {list(estados_climaticos.keys()) if estados_climaticos else 'VACIO'}")
    if estados_climaticos:
        for k, v in estados_climaticos.items():
            print(f"  Estado {k}: descripcion = {v.get('descripcion', 'SIN DESCRIPCION')}")
    
    # Generar colores dinámicos
    if estados_climaticos:
        colores = generar_colores_estados(estados_climaticos)
    else:
        colores = {
            "I": "#FF6B6B", "II": "#4ECDC4", "III": "#45B7D1", 
            "IV": "#FFA07A", "V": "#98D8C8"
        }
    
    # Crear figuras
    fig_combinado = go.Figure()
    fig_conductor = go.Figure()
    fig_guardia1 = go.Figure()
    fig_guardia2 = go.Figure() if cable_guardia2 else None
    
    # Obtener lista ordenada de estados
    estados_ids = sorted(cable_conductor.catenarias_cache.keys(), key=lambda x: int(x))
    
    # Colores fijos para gráfico combinado
    color_conductor = "#DC143C"  # Rojo sólido
    color_guardia1 = "#1E90FF"   # Azul dash
    color_guardia2 = "#32CD32"   # Verde dot
    
    # GRÁFICO COMBINADO - Plotear todos los estados
    for estado_id in estados_ids:
        descripcion = estados_climaticos.get(str(estado_id), {}).get('descripcion', f'Estado {estado_id}')
        visible = (estado_id == estados_ids[0])
        
        # Conductor
        cat_data = cable_conductor.catenarias_cache[estado_id]['catenaria_posterior']
        fig_combinado.add_trace(go.Scatter(
            x=cat_data['x'], y=cat_data['y'], mode='lines',
            name=f'Conductor ({descripcion})',
            line=dict(color=color_conductor, width=2),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>',
            visible=visible,
            legendgroup='conductor',
            showlegend=True
        ))
        idx_max = np.argmax(cat_data['y'])
        fig_combinado.add_trace(go.Scatter(
            x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
            mode='markers', marker=dict(color='orange', size=8),
            showlegend=False, hoverinfo='skip', visible=visible
        ))
        
        # Guardia 1
        cat_data = cable_guardia1.catenarias_cache[estado_id]['catenaria_posterior']
        fig_combinado.add_trace(go.Scatter(
            x=cat_data['x'], y=cat_data['y'], mode='lines',
            name=f'Guardia 1 ({descripcion})',
            line=dict(color=color_guardia1, width=2, dash='dash'),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>',
            visible=visible,
            legendgroup='guardia1',
            showlegend=True
        ))
        idx_max = np.argmax(cat_data['y'])
        fig_combinado.add_trace(go.Scatter(
            x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
            mode='markers', marker=dict(color='orange', size=8),
            showlegend=False, hoverinfo='skip', visible=visible
        ))
        
        # Guardia 2 (si existe)
        if cable_guardia2:
            cat_data = cable_guardia2.catenarias_cache[estado_id]['catenaria_posterior']
            fig_combinado.add_trace(go.Scatter(
                x=cat_data['x'], y=cat_data['y'], mode='lines',
                name=f'Guardia 2 ({descripcion})',
                line=dict(color=color_guardia2, width=2, dash='dot'),
                hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>',
                visible=visible,
                legendgroup='guardia2',
                showlegend=True
            ))
            idx_max = np.argmax(cat_data['y'])
            fig_combinado.add_trace(go.Scatter(
                x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
                mode='markers', marker=dict(color='orange', size=8),
                showlegend=False, hoverinfo='skip', visible=visible
            ))
    
    # GRÁFICOS INDIVIDUALES - Todos visibles con colores distintos
    for estado_id in estados_ids:
        descripcion = estados_climaticos.get(str(estado_id), {}).get('descripcion', f'Estado {estado_id}')
        
        # Conductor individual
        cat_data = cable_conductor.catenarias_cache[estado_id]['catenaria_posterior']
        idx_max = np.argmax(cat_data['y'])
        fig_conductor.add_trace(go.Scatter(
            x=cat_data['x'], y=cat_data['y'], mode='lines',
            name=f'{descripcion} (x={cat_data["x"][idx_max]:.1f}m)',
            line=dict(color=colores.get(estado_id), width=2),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
        ))
        fig_conductor.add_trace(go.Scatter(
            x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
            mode='markers', marker=dict(color='orange', size=8),
            showlegend=False, hoverinfo='skip'
        ))
        
        # Guardia 1 individual
        cat_data = cable_guardia1.catenarias_cache[estado_id]['catenaria_posterior']
        idx_max = np.argmax(cat_data['y'])
        fig_guardia1.add_trace(go.Scatter(
            x=cat_data['x'], y=cat_data['y'], mode='lines',
            name=f'{descripcion} (x={cat_data["x"][idx_max]:.1f}m)',
            line=dict(color=colores.get(estado_id), width=2),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
        ))
        fig_guardia1.add_trace(go.Scatter(
            x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
            mode='markers', marker=dict(color='orange', size=8),
            showlegend=False, hoverinfo='skip'
        ))
        
        # Guardia 2 individual (si existe)
        if cable_guardia2:
            cat_data = cable_guardia2.catenarias_cache[estado_id]['catenaria_posterior']
            idx_max = np.argmax(cat_data['y'])
            fig_guardia2.add_trace(go.Scatter(
                x=cat_data['x'], y=cat_data['y'], mode='lines',
                name=f'{descripcion} (x={cat_data["x"][idx_max]:.1f}m)',
                line=dict(color=colores.get(estado_id), width=2),
                hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
            ))
            fig_guardia2.add_trace(go.Scatter(
                x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
                mode='markers', marker=dict(color='orange', size=8),
                showlegend=False, hoverinfo='skip'
            ))
    
    # Línea de apoyos
    for fig in [fig_combinado, fig_conductor, fig_guardia1] + ([fig_guardia2] if fig_guardia2 else []):
        fig.add_trace(go.Scatter(
            x=[0, L_vano], y=[0, 0], mode='lines',
            name='Apoyos', line=dict(color='black', width=3),
            showlegend=False
        ))
    
    # Layout común
    layout_config = dict(
        xaxis_title='Vano (m)', yaxis_title='Flecha (m)', hovermode='closest',
        legend=dict(x=1.02, y=1, xanchor='left', yanchor='top',
                   bgcolor='rgba(255, 255, 255, 0.8)', bordercolor='gray', borderwidth=1),
        plot_bgcolor='#f8f9fa', paper_bgcolor='white',
        font=dict(size=12), height=500, margin=dict(r=250)
    )
    
    axes_config_x = dict(showgrid=True, gridwidth=1, gridcolor='lightgray',
                        zeroline=True, zerolinewidth=2, zerolinecolor='black')
    axes_config_y = dict(showgrid=True, gridwidth=1, gridcolor='lightgray',
                        zeroline=True, zerolinewidth=2, zerolinecolor='black',
                        autorange='reversed')
    
    # Dropdown para gráfico combinado
    n_traces_por_estado = 4 if not cable_guardia2 else 6
    buttons = []
    
    for i, estado_id in enumerate(estados_ids):
        descripcion = estados_climaticos.get(str(estado_id), {}).get('descripcion', f'Estado {estado_id}')
        visible = [False] * (len(estados_ids) * n_traces_por_estado + 1)
        
        start_idx = i * n_traces_por_estado
        for j in range(n_traces_por_estado):
            visible[start_idx + j] = True
        visible[-1] = True
        
        buttons.append(dict(label=descripcion, method='update', args=[{'visible': visible}]))
    
    visible_todos = [True] * (len(estados_ids) * n_traces_por_estado + 1)
    buttons.append(dict(label='Todos', method='update', args=[{'visible': visible_todos}]))
    
    # Aplicar configuración
    fig_combinado.update_layout(
        title='Flechas de Cables - Conductor y Guardia',
        updatemenus=[dict(buttons=buttons, direction='down', showactive=True,
                         x=0.02, xanchor='left', y=1.15, yanchor='top')],
        **layout_config
    )
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


def crear_grafico_flechas_solo_conductor(cable_conductor, L_vano):
    """
    Crear gráfico de flechas solo para conductor (sin guardia)
    
    Args:
        cable_conductor: Objeto Cable_AEA del conductor con catenarias_cache
        L_vano: Longitud del vano en metros
    
    Returns:
        Figura de Plotly solo para conductor
    """
    
    estados_climaticos = {}
    if hasattr(cable_conductor, 'estados_climaticos'):
        estados_climaticos = cable_conductor.estados_climaticos
    
    if estados_climaticos:
        colores = generar_colores_estados(estados_climaticos)
    else:
        colores = {"I": "#FF6B6B", "II": "#4ECDC4", "III": "#45B7D1",
                  "IV": "#FFA07A", "V": "#98D8C8"}
    
    fig_conductor = go.Figure()
    
    for estado_id, cat_estados in cable_conductor.catenarias_cache.items():
        cat_data = cat_estados['catenaria_posterior']
        descripcion = estados_climaticos.get(str(estado_id), {}).get('descripcion', f'Estado {estado_id}')
        idx_max = np.argmax(cat_data['y'])
        
        fig_conductor.add_trace(go.Scatter(
            x=cat_data['x'], y=cat_data['y'], mode='lines',
            name=f'{descripcion} (x={cat_data["x"][idx_max]:.1f}m)',
            line=dict(color=colores.get(estado_id, "#DC143C"), width=2),
            hovertemplate='<b>Vano:</b> %{x:.1f} m<br><b>Flecha:</b> %{y:.3f} m<extra></extra>'
        ))
        fig_conductor.add_trace(go.Scatter(
            x=[cat_data['x'][idx_max]], y=[cat_data['y'][idx_max]], 
            mode='markers', marker=dict(color='orange', size=8),
            showlegend=False, hoverinfo='skip'
        ))
    
    fig_conductor.add_trace(go.Scatter(
        x=[0, L_vano], y=[0, 0], mode='lines',
        name='Apoyos', line=dict(color='black', width=3),
        showlegend=False
    ))
    
    fig_conductor.update_layout(
        title='Flechas de Conductor por Estado Climático',
        xaxis_title='Vano (m)', yaxis_title='Flecha (m)', hovermode='closest',
        legend=dict(x=1.02, y=1, xanchor='left', yanchor='top',
                   bgcolor='rgba(255, 255, 255, 0.8)', bordercolor='gray', borderwidth=1),
        plot_bgcolor='#f8f9fa', paper_bgcolor='white',
        font=dict(size=12), height=500, margin=dict(r=250)
    )
    
    fig_conductor.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray',
                              zeroline=True, zerolinewidth=2, zerolinecolor='black')
    fig_conductor.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray',
                              zeroline=True, zerolinewidth=2, zerolinecolor='black',
                              autorange='reversed')
    
    return fig_conductor
