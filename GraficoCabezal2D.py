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
        
        for nombre_c, nodo_c in conductores:
            x_amarre, y_amarre, z_amarre = nodo_c.coordenadas
            
            # Posiciones: reposo, tormenta_izq, tormenta_der, decmax_izq, decmax_der
            posiciones = [
                (x_amarre, z_amarre - Lk, 'reposo', s_reposo, True),
                (x_amarre - Lk * math.sin(math.radians(theta_tormenta)), 
                 z_amarre - Lk * math.cos(math.radians(theta_tormenta)), 'tormenta_izq', s_tormenta, False),
                (x_amarre + Lk * math.sin(math.radians(theta_tormenta)), 
                 z_amarre - Lk * math.cos(math.radians(theta_tormenta)), 'tormenta_der', s_tormenta, False),
                (x_amarre - Lk * math.sin(math.radians(theta_max)), 
                 z_amarre - Lk * math.cos(math.radians(theta_max)), 'decmax_izq', s_decmax, False),
                (x_amarre + Lk * math.sin(math.radians(theta_max)), 
                 z_amarre - Lk * math.cos(math.radians(theta_max)), 'decmax_der', s_decmax, False)
            ]
            
            for x_cond, z_cond, estado, s_val, visible in posiciones:
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
                
                # Zona s_reposo
                fig.add_trace(self._crear_circulo(x_cond, z_cond, s_reposo, 'blue', 0.1,
                    f'{nombre_c}_{estado}_s_reposo', visible))
                
                # Zona s_tormenta
                fig.add_trace(self._crear_circulo(x_cond, z_cond, s_tormenta, 'orange', 0.1,
                    f'{nombre_c}_{estado}_s_tormenta', False))
                
                # Zona s_decmax
                fig.add_trace(self._crear_circulo(x_cond, z_cond, s_decmax, 'red', 0.1,
                    f'{nombre_c}_{estado}_s_decmax', False))
                
                # Zona D_fases
                fig.add_trace(self._crear_circulo(x_cond, z_cond, D_fases, 'green', 0.05,
                    f'{nombre_c}_{estado}_D_fases', False))
                
                # Zona Dhg
                fig.add_trace(self._crear_circulo(x_cond, z_cond, Dhg, 'purple', 0.05,
                    f'{nombre_c}_{estado}_Dhg', False))
        
        # 4. Zona apantallamiento
        if self.geo.cant_hg > 0:
            self._dibujar_zona_apantallamiento(fig)
        
        # 5. Crear botones de control
        self._crear_botones_control(fig, conductores)
        
        # 6. Configurar layout
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
        """Crear botones interactivos por conductor"""
        buttons = []
        
        # Botón: Mostrar todo
        buttons.append(dict(
            label='Mostrar Todo',
            method='update',
            args=[{'visible': [True] * len(fig.data)}]
        ))
        
        # Botón: Solo reposo
        visible_reposo = []
        for trace in fig.data:
            visible_reposo.append('reposo' in trace.name or 'conexion' in trace.name or 'nodo' in trace.name)
        buttons.append(dict(
            label='Solo Reposo',
            method='update',
            args=[{'visible': visible_reposo}]
        ))
        
        # Botones por conductor
        for nombre_c, _ in conductores:
            # Declinación tormenta
            visible_tormenta = []
            for trace in fig.data:
                visible_tormenta.append(
                    nombre_c in trace.name and ('tormenta' in trace.name or 'reposo' in trace.name) or
                    'conexion' in trace.name or 'nodo' in trace.name
                )
            buttons.append(dict(
                label=f'{nombre_c}: Tormenta',
                method='update',
                args=[{'visible': visible_tormenta}]
            ))
            
            # Declinación máxima
            visible_decmax = []
            for trace in fig.data:
                visible_decmax.append(
                    nombre_c in trace.name and ('decmax' in trace.name or 'reposo' in trace.name) or
                    'conexion' in trace.name or 'nodo' in trace.name
                )
            buttons.append(dict(
                label=f'{nombre_c}: Dec.Máx',
                method='update',
                args=[{'visible': visible_decmax}]
            ))
        
        # Botones de zonas
        for zona in ['s_reposo', 's_tormenta', 's_decmax', 'D_fases', 'Dhg']:
            visible_zona = []
            for trace in fig.data:
                visible_zona.append(zona in trace.name or 'conexion' in trace.name or 'nodo' in trace.name)
            buttons.append(dict(
                label=f'Zona: {zona}',
                method='update',
                args=[{'visible': visible_zona}]
            ))
        
        fig.update_layout(
            updatemenus=[
                dict(
                    type='dropdown',
                    direction='down',
                    x=0.02, y=0.98,
                    xanchor='left', yanchor='top',
                    buttons=buttons
                )
            ]
        )
    
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
        colores_nodos = {'base': 'black', 'cruce': 'gray', 'conductor': 'red',
                        'guardia': 'green', 'general': 'blue', 'viento': 'cyan'}
        
        simbolos = {'base': 'square', 'cruce': 'diamond', 'conductor': 'circle',
                   'guardia': 'triangle-up', 'general': 'x', 'viento': 'star'}
        
        nodos_por_tipo = {}
        for nombre, nodo in self.geo.nodos.items():
            tipo = nodo.tipo_nodo
            if tipo not in nodos_por_tipo:
                nodos_por_tipo[tipo] = []
            nodos_por_tipo[tipo].append((nombre, nodo))
        
        for tipo, nodos in nodos_por_tipo.items():
            x_vals, y_vals, text_vals = [], [], []
            
            for nombre, nodo in nodos:
                x, y, z = nodo.coordenadas
                x_vals.append(x)
                y_vals.append(z)
                text_vals.append(nombre)
            
            fig.add_trace(go.Scatter(
                x=x_vals, y=y_vals,
                mode='markers+text',
                marker=dict(size=10, color=colores_nodos.get(tipo, 'gray'),
                           symbol=simbolos.get(tipo, 'circle'),
                           line=dict(width=1, color='black')),
                text=text_vals, textposition='top center',
                name=f'nodo_{tipo}',
                hovertemplate='%{text}<br>x=%{x:.2f}m<br>z=%{y:.2f}m<extra></extra>'
            ))
    
    def _dibujar_zona_apantallamiento(self, fig):
        """Dibujar zona de apantallamiento como área sombreada"""
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
                mode='lines', fill='toself',
                line=dict(color='green', width=1, dash='dash'),
                fillcolor='rgba(0, 255, 0, 0.1)',
                name='apantallamiento', showlegend=False, hoverinfo='skip'
            ))
    
    def _configurar_layout(self, fig):
        """Configurar layout del gráfico"""
        fig.update_layout(
            title='Cabezal de Estructura - Vista Lateral (XZ)',
            xaxis=dict(title='X [m]', scaleanchor='y', scaleratio=1,
                      zeroline=True, zerolinewidth=2, zerolinecolor='black',
                      gridcolor='lightgray'),
            yaxis=dict(title='Z [m]', zeroline=True, zerolinewidth=2,
                      zerolinecolor='black', gridcolor='lightgray'),
            hovermode='closest', showlegend=True,
            legend=dict(x=1.02, y=1, xanchor='left', yanchor='top'),
            width=1200, height=800, plot_bgcolor='white'
        )
