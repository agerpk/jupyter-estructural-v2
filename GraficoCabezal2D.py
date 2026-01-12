# GraficoCabezal2D.py
import plotly.graph_objects as go
import math
from typing import Dict, List, Tuple


class GraficoCabezal2D:
    """Gráfico especializado de cabezal con controles interactivos por nodo"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def generar_completo(self) -> go.Figure:
        """Generar gráfico completo con controles interactivos"""
        fig = go.Figure()
        
        # Obtener parámetros
        Lk = self.geo.lk
        theta_max = self.geo.dimensiones.get('theta_max', 0)
        theta_tormenta = theta_max / 2.0 if theta_max < 99 else 0
        s_reposo = self.geo.dimensiones.get('s_estructura', 0)
        s_tormenta = self.geo.dimensiones.get('s_tormenta', s_reposo)
        s_decmax = self.geo.dimensiones.get('s_decmax', s_tormenta)
        D_fases = self.geo.dimensiones.get('D_fases', 0)
        Dhg = self.geo.dimensiones.get('Dhg', 0)
        
        # 1. Dibujar estructura base
        self._dibujar_conexiones(fig)
        
        # 2. Dibujar nodos
        self._dibujar_nodos(fig)
        
        # 3. Dibujar conductores con declinaciones y zonas
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        # Encontrar z máxima de conductores
        z_max_conductor = max(nodo.coordenadas[2] for _, nodo in conductores) if conductores else 0
        
        for nombre_c, nodo_c in conductores:
            x_amarre, y_amarre, z_amarre = nodo_c.coordenadas
            es_z_max = abs(z_amarre - z_max_conductor) < 0.01
            
            # Determinar dirección de declinación según posición X
            dir_decmax = 'der' if x_amarre < 0 else 'izq'
            dir_tormenta = 'der' if x_amarre < 0 else 'izq'
            
            # Posiciones: reposo, tormenta_izq, tormenta_der, decmax_izq, decmax_der
            posiciones = [
                (x_amarre, z_amarre - Lk, 'reposo', s_reposo, True, True, True, es_z_max),
                (x_amarre - Lk * math.sin(math.radians(theta_tormenta)), 
                 z_amarre - Lk * math.cos(math.radians(theta_tormenta)), 'tormenta_izq', s_tormenta, False, False, dir_tormenta == 'izq', False),
                (x_amarre + Lk * math.sin(math.radians(theta_tormenta)), 
                 z_amarre - Lk * math.cos(math.radians(theta_tormenta)), 'tormenta_der', s_tormenta, False, False, dir_tormenta == 'der', False),
                (x_amarre - Lk * math.sin(math.radians(theta_max)), 
                 z_amarre - Lk * math.cos(math.radians(theta_max)), 'decmax_izq', s_decmax, False, False, dir_decmax == 'izq', False),
                (x_amarre + Lk * math.sin(math.radians(theta_max)), 
                 z_amarre - Lk * math.cos(math.radians(theta_max)), 'decmax_der', s_decmax, False, False, dir_decmax == 'der', False)
            ]
            
            for x_cond, z_cond, estado, s_val, visible, mostrar_dfases, mostrar_s, mostrar_dhg in posiciones:
                # Cadena
                fig.add_trace(go.Scatter(
                    x=[x_amarre, x_cond], y=[z_amarre, z_cond],
                    mode='lines', line=dict(color='gray', width=2),
                    name=f'{nombre_c}_{estado}_cadena',
                    visible=visible,
                    showlegend=False, hoverinfo='skip'
                ))
                
                # Conductor
                fig.add_trace(go.Scatter(
                    x=[x_cond], y=[z_cond],
                    mode='markers', marker=dict(size=8, color='red'),
                    name=f'{nombre_c}_{estado}_punto',
                    visible=visible,
                    showlegend=False, hoverinfo='skip'
                ))
                
                # Zona D_fases (solo en reposo)
                if mostrar_dfases:
                    fig.add_trace(self._crear_circulo(x_cond, z_cond, D_fases, 'green', 0.05,
                        f'{nombre_c}_{estado}_D_fases', False))
                
                # Zona Dhg (solo en reposo de z máxima)
                if mostrar_dhg:
                    fig.add_trace(self._crear_circulo(x_cond, z_cond, Dhg, 'purple', 0.05,
                        f'{nombre_c}_{estado}_Dhg', False))
                
                # Zona s_reposo/s_tormenta/s_decmax (según corresponda)
                if mostrar_s:
                    fig.add_trace(self._crear_circulo(x_cond, z_cond, s_val, 'blue', 0.1,
                        f'{nombre_c}_{estado}_s_zona', False))
        
        # 4. Zona apantallamiento
        if self.geo.cant_hg > 0:
            self._dibujar_zona_apantallamiento(fig)
        
        # 5. Dibujar cotas
        self._dibujar_cotas(fig)
        
        # 6. Crear botones de control
        self._crear_botones_control(fig, conductores)
        
        # 7. Configurar layout
        self._configurar_layout(fig)
        
        return fig
    
    def _crear_circulo(self, x, z, radio, color, alpha, name, visible):
        """Crear círculo como polígono"""
        theta = [i * 2 * math.pi / 50 for i in range(51)]
        x_circle = [x + radio * math.cos(t) for t in theta]
        z_circle = [z + radio * math.sin(t) for t in theta]
        
        return go.Scatter(
            x=x_circle, y=z_circle,
            mode='lines', fill='toself',
            line=dict(color=color, width=1),
            fillcolor=f'rgba({self._hex_to_rgb(color)},{alpha})',
            name=name, visible=visible,
            showlegend=False, hoverinfo='skip'
        )
    
    def _hex_to_rgb(self, hex_color):
        """Convertir color hex a RGB"""
        colors = {'blue': '0,0,255', 'orange': '255,165,0', 'red': '255,0,0',
                 'green': '0,255,0', 'purple': '128,0,128', 'gray': '128,128,128'}
        return colors.get(hex_color, '128,128,128')
    
    def _crear_botones_control(self, fig, conductores):
        """Crear sliders de control independientes usando updatemenus con botones toggle"""
        
        # Crear índices de traces por patrón
        indices_dfases = [i for i, trace in enumerate(fig.data) if 'D_fases' in (trace.name or '')]
        indices_dhg = [i for i, trace in enumerate(fig.data) if 'Dhg' in (trace.name or '')]
        indices_reposo_s = [i for i, trace in enumerate(fig.data) if 'reposo_s_zona' in (trace.name or '')]
        indices_tormenta = [i for i, trace in enumerate(fig.data) if 'tormenta' in (trace.name or '')]
        indices_decmax = [i for i, trace in enumerate(fig.data) if 'decmax' in (trace.name or '')]
        indices_apantallamiento = [i for i, trace in enumerate(fig.data) if 'apantallamiento' in (trace.name or '')]
        
        updatemenus = [
            # Toggle D_fases
            dict(
                type='buttons',
                direction='right',
                x=1.02,
                xanchor='left',
                y=0.70,
                yanchor='top',
                buttons=[
                    dict(
                        label='D_fases: OFF',
                        method='restyle',
                        args=[{'visible': False}, indices_dfases]
                    ),
                    dict(
                        label='D_fases: ON',
                        method='restyle',
                        args=[{'visible': True}, indices_dfases]
                    )
                ],
                active=0
            ),
            # Toggle Dhg
            dict(
                type='buttons',
                direction='right',
                x=1.02,
                xanchor='left',
                y=0.635,
                yanchor='top',
                buttons=[
                    dict(
                        label='Dhg: OFF',
                        method='restyle',
                        args=[{'visible': False}, indices_dhg]
                    ),
                    dict(
                        label='Dhg: ON',
                        method='restyle',
                        args=[{'visible': True}, indices_dhg]
                    )
                ],
                active=0
            ),
            # Toggle s_reposo
            dict(
                type='buttons',
                direction='right',
                x=1.02,
                xanchor='left',
                y=0.57,
                yanchor='top',
                buttons=[
                    dict(
                        label='s_reposo: OFF',
                        method='restyle',
                        args=[{'visible': False}, indices_reposo_s]
                    ),
                    dict(
                        label='s_reposo: ON',
                        method='restyle',
                        args=[{'visible': True}, indices_reposo_s]
                    )
                ],
                active=0
            ),
            # Toggle s_tormenta
            dict(
                type='buttons',
                direction='right',
                x=1.02,
                xanchor='left',
                y=0.505,
                yanchor='top',
                buttons=[
                    dict(
                        label='s_tormenta: OFF',
                        method='restyle',
                        args=[{'visible': False}, indices_tormenta]
                    ),
                    dict(
                        label='s_tormenta: ON',
                        method='restyle',
                        args=[{'visible': True}, indices_tormenta]
                    )
                ],
                active=0
            ),
            # Toggle s_decmax
            dict(
                type='buttons',
                direction='right',
                x=1.02,
                xanchor='left',
                y=0.44,
                yanchor='top',
                buttons=[
                    dict(
                        label='s_decmax: OFF',
                        method='restyle',
                        args=[{'visible': False}, indices_decmax]
                    ),
                    dict(
                        label='s_decmax: ON',
                        method='restyle',
                        args=[{'visible': True}, indices_decmax]
                    )
                ],
                active=0
            ),
            # Toggle Apantallamiento
            dict(
                type='buttons',
                direction='right',
                x=1.02,
                xanchor='left',
                y=0.375,
                yanchor='top',
                buttons=[
                    dict(
                        label='Apantallamiento: OFF',
                        method='restyle',
                        args=[{'visible': False}, indices_apantallamiento]
                    ),
                    dict(
                        label='Apantallamiento: ON',
                        method='restyle',
                        args=[{'visible': True}, indices_apantallamiento]
                    )
                ],
                active=1
            )
        ]
        
        fig.update_layout(updatemenus=updatemenus)
    
    def _toggle_only(self, trace, pattern, show):
        """Mostrar/ocultar solo traces que contienen pattern, mantener resto sin cambios"""
        name = trace.name if trace.name else ''
        if pattern in name:
            return show
        # Mantener estado actual, si es None significa True (visible por defecto)
        current = trace.visible
        return current if current is not None else True
    
    def _toggle_tormenta_completo(self, trace, show):
        """Mostrar/ocultar conductor declinado en tormenta + zona s_tormenta"""
        name = trace.name if trace.name else ''
        # Mostrar cadena, punto y zona de tormenta (ambos lados)
        if 'tormenta' in name:
            return show
        # Mantener estado actual, si es None significa True (visible por defecto)
        current = trace.visible
        return current if current is not None else True
    
    def _toggle_decmax_completo(self, trace, show):
        """Mostrar/ocultar conductor declinado en decmax + zona s_decmax"""
        name = trace.name if trace.name else ''
        # Mostrar cadena, punto y zona de decmax (ambos lados)
        if 'decmax' in name:
            return show
        # Mantener estado actual, si es None significa True (visible por defecto)
        current = trace.visible
        return current if current is not None else True
    
    def _dibujar_conexiones(self, fig):
        """Dibujar conexiones entre nodos con colores por tipo"""
        if not hasattr(self.geo, 'conexiones'):
            return
        
        colores = {'columna': 'gray', 'mensula': 'blue', 'cruceta': 'green', 'cadena': 'orange'}
        
        for origen, destino, tipo in self.geo.conexiones:
            if origen not in self.geo.nodos or destino not in self.geo.nodos:
                continue
            
            nodo_o = self.geo.nodos[origen]
            nodo_d = self.geo.nodos[destino]
            
            x_o, y_o, z_o = nodo_o.coordenadas
            x_d, y_d, z_d = nodo_d.coordenadas
            
            fig.add_trace(go.Scatter(
                x=[x_o, x_d], y=[z_o, z_d],
                mode='lines', line=dict(color=colores.get(tipo, 'gray'), width=2),
                name=f'conexion_{tipo}', showlegend=False, hoverinfo='skip'
            ))
    
    def _dibujar_nodos(self, fig):
        """Dibujar nodos con colores por tipo"""
        # Solo mostrar conductores, guardias y viento con nombres
        tipos_visibles = ['conductor', 'guardia', 'viento']
        
        colores_nodos = {'conductor': 'blue', 'guardia': 'green', 'viento': 'cyan'}
        
        for tipo in tipos_visibles:
            nodos = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == tipo]
            if not nodos:
                continue
            
            primera_vez = True
            for nombre, nodo in nodos:
                x, y, z = nodo.coordenadas
                
                fig.add_trace(go.Scatter(
                    x=[x],
                    y=[z],
                    mode='markers+text',
                    marker=dict(
                        size=10,
                        color=colores_nodos[tipo],
                        symbol='circle',
                        line=dict(width=1, color='black')
                    ),
                    text=[nombre],
                    textposition='top center',
                    textfont=dict(size=9),
                    name=tipo.capitalize() if primera_vez else None,
                    showlegend=primera_vez,
                    legendgroup=tipo,
                    hovertemplate=f'<b>{nombre}</b><br>x={x:.2f}m<br>z={z:.2f}m<extra></extra>'
                ))
                primera_vez = False
    
    def _dibujar_zona_apantallamiento(self, fig):
        """Dibujar zona de apantallamiento como área sombreada sin líneas"""
        guardias = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "guardia"]
        if not guardias:
            return
        
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        if not conductores:
            return
        
        Lk = self.geo.lk
        ang_apant = self.geo.ang_apantallamiento
        
        for nombre_g, nodo_g in guardias:
            x_g, y_g, z_g = nodo_g.coordenadas
            z_min = min(nodo.coordenadas[2] - Lk for _, nodo in conductores)
            
            altura_cono = z_g - z_min
            extension = altura_cono * math.tan(math.radians(ang_apant))
            
            fig.add_trace(go.Scatter(
                x=[x_g - extension, x_g, x_g + extension],
                y=[z_min, z_g, z_min],
                mode='none',
                fill='toself',
                fillcolor='rgba(0, 255, 0, 0.15)',
                name='apantallamiento',
                showlegend=False,
                hoverinfo='skip'
            ))
    
    def _dibujar_cotas(self, fig):
        """Dibujar cotas de distancias horizontales"""
        # Cotas horizontales entre CROSS y conductores (x positivo)
        for nombre_cross, nodo_cross in [(n, nodo) for n, nodo in self.geo.nodos.items() if 'CROSS_H' in n]:
            x_cross, y_cross, z_cross = nodo_cross.coordenadas
            
            # Buscar conductores en misma altura (z) con x positivo
            conductores_altura = [
                (n, nodo) for n, nodo in self.geo.nodos.items()
                if nodo.tipo_nodo == 'conductor' and abs(nodo.coordenadas[2] - z_cross) < 0.1 and nodo.coordenadas[0] > 0.01
            ]
            
            if conductores_altura:
                # Ordenar por x
                conductores_altura.sort(key=lambda x: x[1].coordenadas[0])
                
                # Cota entre CROSS y primer conductor
                primer_cond = conductores_altura[0][1]
                x_cond, y_cond, z_cond = primer_cond.coordenadas
                dist = x_cond - x_cross
                x_medio = (x_cross + x_cond) / 2
                
                fig.add_trace(go.Scatter(
                    x=[x_medio, x_medio],
                    y=[z_cross + 0.3, z_cross + 0.6],
                    mode='lines',
                    line=dict(color='gray', width=1, dash='dot'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_annotation(
                    x=x_medio,
                    y=z_cross + 0.6,
                    text=f'{dist:.2f}m',
                    showarrow=False,
                    yanchor='bottom',
                    font=dict(size=9, color='black'),
                    bgcolor='white',
                    borderpad=2
                )
                
                # Cota entre conductores si hay 2 con x distinta
                if len(conductores_altura) >= 2:
                    x1_cond = conductores_altura[0][1].coordenadas[0]
                    x2_cond = conductores_altura[1][1].coordenadas[0]
                    if abs(x2_cond - x1_cond) > 0.1:
                        dist_cond = x2_cond - x1_cond
                        x_medio_cond = (x1_cond + x2_cond) / 2
                        
                        fig.add_trace(go.Scatter(
                            x=[x_medio_cond, x_medio_cond],
                            y=[z_cross + 0.3, z_cross + 0.6],
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        
                        fig.add_annotation(
                            x=x_medio_cond,
                            y=z_cross + 0.6,
                            text=f'{dist_cond:.2f}m',
                            showarrow=False,
                            yanchor='bottom',
                            font=dict(size=9, color='black'),
                            bgcolor='white',
                            borderpad=2
                        )
        
        # Cota horizontal entre TOP y HG (x positivo)
        if 'TOP' in self.geo.nodos:
            nodo_top = self.geo.nodos['TOP']
            x_top, y_top, z_top = nodo_top.coordenadas
            
            # Buscar guardias con x positivo
            guardias_pos = [
                (n, nodo) for n, nodo in self.geo.nodos.items()
                if nodo.tipo_nodo == 'guardia' and nodo.coordenadas[0] > 0.01
            ]
            
            if guardias_pos:
                # Ordenar por x y tomar el más cercano
                guardias_pos.sort(key=lambda x: x[1].coordenadas[0])
                primer_hg = guardias_pos[0][1]
                x_hg, y_hg, z_hg = primer_hg.coordenadas
                
                if abs(x_hg - x_top) > 0.1:
                    dist = x_hg - x_top
                    x_medio = (x_top + x_hg) / 2
                    
                    fig.add_trace(go.Scatter(
                        x=[x_medio, x_medio],
                        y=[z_top + 0.3, z_top + 0.6],
                        mode='lines',
                        line=dict(color='gray', width=1, dash='dot'),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    
                    fig.add_annotation(
                        x=x_medio,
                        y=z_top + 0.6,
                        text=f'{dist:.2f}m',
                        showarrow=False,
                        yanchor='bottom',
                        font=dict(size=9, color='black'),
                        bgcolor='white',
                        borderpad=2
                    )
    
    def _configurar_layout(self, fig):
        """Configurar layout del gráfico"""
        # Calcular límites del área de cabezal
        x_vals = [nodo.coordenadas[0] for nodo in self.geo.nodos.values()]
        z_vals = [nodo.coordenadas[2] for nodo in self.geo.nodos.values()]
        
        # Límites en X: ancho de estructura + 10% margen
        x_min, x_max = min(x_vals), max(x_vals)
        ancho_x = x_max - x_min
        margen_x = ancho_x * 0.1
        
        # Límites en Z: desde conductor más bajo - 2*Lk hasta nodo más alto + 10% margen
        conductores = [nodo for nodo in self.geo.nodos.values() if nodo.tipo_nodo == "conductor"]
        z_min_conductor = min(nodo.coordenadas[2] for nodo in conductores) if conductores else min(z_vals)
        z_min = z_min_conductor - 2 * self.geo.lk
        z_max = max(z_vals)
        altura_z = z_max - z_min
        margen_z = altura_z * 0.1
        
        # Obtener sliders existentes (de _crear_botones_control)
        sliders_existentes = fig.layout.sliders if fig.layout.sliders else []
        
        # Agregar slider de Grid
        sliders_completos = list(sliders_existentes) + [{
            'active': 4,
            'yanchor': 'top',
            'y': 0.15,
            'xanchor': 'left',
            'x': 1.02,
            'currentvalue': {
                'prefix': 'Grid: ',
                'visible': True,
                'xanchor': 'left'
            },
            'pad': {'b': 5, 't': 5},
            'len': 0.15,
            'steps': [
                {
                    'args': [{'xaxis.dtick': 0.1, 'yaxis.dtick': 0.1}],
                    'label': '0.1m',
                    'method': 'relayout'
                },
                {
                    'args': [{'xaxis.dtick': 0.25, 'yaxis.dtick': 0.25}],
                    'label': '0.25m',
                    'method': 'relayout'
                },
                {
                    'args': [{'xaxis.dtick': 0.5, 'yaxis.dtick': 0.5}],
                    'label': '0.5m',
                    'method': 'relayout'
                },
                {
                    'args': [{'xaxis.dtick': 1.0, 'yaxis.dtick': 1.0}],
                    'label': '1m',
                    'method': 'relayout'
                },
                {
                    'args': [{'xaxis.dtick': 2.0, 'yaxis.dtick': 2.0}],
                    'label': '2m',
                    'method': 'relayout'
                },
                {
                    'args': [{'xaxis.dtick': 2.5, 'yaxis.dtick': 2.5}],
                    'label': '2.5m',
                    'method': 'relayout'
                },
                {
                    'args': [{'xaxis.dtick': 5.0, 'yaxis.dtick': 5.0}],
                    'label': '5m',
                    'method': 'relayout'
                }
            ]
        }]
        
        fig.update_layout(
            title='Cabezal de Estructura - Vista Lateral (XZ)',
            xaxis=dict(
                title='X [m]',
                scaleanchor='y',
                scaleratio=1,
                type='linear',
                dtick=2.0,
                range=[x_min - margen_x, x_max + margen_x],
                zeroline=False,
                showgrid=True,
                gridcolor='rgba(200, 200, 200, 0.3)',
                gridwidth=1
            ),
            yaxis=dict(
                title='Z [m]',
                type='linear',
                dtick=2.0,
                range=[z_min - margen_z, z_max + margen_z],
                zeroline=False,
                showgrid=True,
                gridcolor='rgba(200, 200, 200, 0.3)',
                gridwidth=1
            ),
            hovermode='closest',
            showlegend=True,
            legend=dict(x=1.02, y=1, xanchor='left', yanchor='top'),
            width=1200,
            height=800,
            plot_bgcolor='white',
            sliders=sliders_completos
        )
