# GraficoEstructura2D.py
import plotly.graph_objects as go
import math
from typing import Dict, List, Tuple


class GraficoEstructura2D:
    """Gráfico especializado de estructura completa - Vista lateral XZ"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def generar_completo(self) -> go.Figure:
        """Generar gráfico completo de estructura"""
        fig = go.Figure()
        
        # 1. Dibujar conexiones (estructura)
        self._dibujar_conexiones(fig)
        
        # 2. Dibujar nodos
        self._dibujar_nodos(fig)
        
        # 3. Dibujar cables (líneas punteadas desde conductores)
        self._dibujar_cables(fig)
        
        # 4. Dibujar zona de apantallamiento
        if self.geo.cant_hg > 0:
            self._dibujar_zona_apantallamiento(fig)
        
        # 5. Configurar layout
        self._configurar_layout(fig)
        
        return fig
    
    def _dibujar_conexiones(self, fig):
        """Dibujar conexiones entre nodos con colores por tipo"""
        if not hasattr(self.geo, 'conexiones'):
            return
        
        colores = {
            'columna': 'rgba(100, 100, 100, 0.8)',
            'mensula': 'rgba(0, 100, 200, 0.8)',
            'cruceta': 'rgba(0, 150, 0, 0.8)',
            'cadena': 'rgba(255, 150, 0, 0.8)'
        }
        
        anchos = {
            'columna': 4,
            'mensula': 3,
            'cruceta': 3,
            'cadena': 2
        }
        
        # Agrupar conexiones por tipo
        conexiones_por_tipo = {}
        for origen, destino, tipo in self.geo.conexiones:
            if tipo not in conexiones_por_tipo:
                conexiones_por_tipo[tipo] = []
            conexiones_por_tipo[tipo].append((origen, destino))
        
        # Dibujar cada tipo
        for tipo, conexiones in conexiones_por_tipo.items():
            for origen, destino in conexiones:
                if origen not in self.geo.nodos or destino not in self.geo.nodos:
                    continue
                
                nodo_o = self.geo.nodos[origen]
                nodo_d = self.geo.nodos[destino]
                
                x_o, y_o, z_o = nodo_o.coordenadas
                x_d, y_d, z_d = nodo_d.coordenadas
                
                fig.add_trace(go.Scatter(
                    x=[x_o, x_d],
                    y=[z_o, z_d],
                    mode='lines',
                    line=dict(
                        color=colores.get(tipo, 'gray'),
                        width=anchos.get(tipo, 2)
                    ),
                    name=tipo.capitalize(),
                    showlegend=False,
                    hoverinfo='skip'
                ))
    
    def _dibujar_nodos(self, fig):
        """Dibujar nodos con colores y símbolos por tipo"""
        colores_nodos = {
            'base': 'black',
            'cruce': 'gray',
            'conductor': 'red',
            'guardia': 'green',
            'general': 'blue',
            'viento': 'cyan'
        }
        
        simbolos = {
            'base': 'square',
            'cruce': 'diamond',
            'conductor': 'circle',
            'guardia': 'triangle-up',
            'general': 'x',
            'viento': 'star'
        }
        
        tamaños = {
            'base': 12,
            'cruce': 8,
            'conductor': 10,
            'guardia': 10,
            'general': 8,
            'viento': 8
        }
        
        # Agrupar nodos por tipo
        nodos_por_tipo = {}
        for nombre, nodo in self.geo.nodos.items():
            tipo = nodo.tipo_nodo
            if tipo not in nodos_por_tipo:
                nodos_por_tipo[tipo] = []
            nodos_por_tipo[tipo].append((nombre, nodo))
        
        # Dibujar cada tipo
        for tipo, nodos in nodos_por_tipo.items():
            x_vals = []
            y_vals = []
            text_vals = []
            
            for nombre, nodo in nodos:
                x, y, z = nodo.coordenadas
                x_vals.append(x)
                y_vals.append(z)
                text_vals.append(nombre)
            
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='markers+text',
                marker=dict(
                    size=tamaños.get(tipo, 8),
                    color=colores_nodos.get(tipo, 'gray'),
                    symbol=simbolos.get(tipo, 'circle'),
                    line=dict(width=1, color='black')
                ),
                text=text_vals,
                textposition='top center',
                textfont=dict(size=9),
                name=tipo.capitalize(),
                hovertemplate='<b>%{text}</b><br>x=%{x:.2f}m<br>z=%{y:.2f}m<extra></extra>'
            ))
    
    def _dibujar_cables(self, fig):
        """Dibujar líneas punteadas desde conductores hacia vanos"""
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        for nombre, nodo in conductores:
            x, y, z = nodo.coordenadas
            
            # Línea hacia la derecha (vano)
            fig.add_trace(go.Scatter(
                x=[x, x + 5],
                y=[z, z],
                mode='lines',
                line=dict(color='red', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    def _dibujar_zona_apantallamiento(self, fig):
        """Dibujar zona de apantallamiento"""
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
            
            # Altura mínima de conductores
            z_min = min(nodo.coordenadas[2] - Lk for _, nodo in conductores)
            
            # Extensión horizontal
            altura_cono = z_g - z_min
            extension = altura_cono * math.tan(math.radians(ang_apant))
            
            # Dibujar cono
            fig.add_trace(go.Scatter(
                x=[x_g - extension, x_g, x_g + extension],
                y=[z_min, z_g, z_min],
                mode='lines',
                line=dict(color='green', width=1, dash='dash'),
                fill='toself',
                fillcolor='rgba(0, 255, 0, 0.1)',
                name='Apantallamiento',
                showlegend=False,
                hoverinfo='skip'
            ))
    
    def _configurar_layout(self, fig):
        """Configurar layout del gráfico"""
        # Calcular límites
        x_vals = [nodo.coordenadas[0] for nodo in self.geo.nodos.values()]
        z_vals = [nodo.coordenadas[2] for nodo in self.geo.nodos.values()]
        
        x_min, x_max = min(x_vals), max(x_vals)
        z_min, z_max = min(z_vals), max(z_vals)
        
        # Agregar margen
        margen_x = (x_max - x_min) * 0.2 if x_max != x_min else 5
        margen_z = (z_max - z_min) * 0.1 if z_max != z_min else 2
        
        fig.update_layout(
            title='Estructura Completa - Vista Lateral (XZ)',
            xaxis=dict(
                title='X [m]',
                scaleanchor='y',
                scaleratio=1,
                range=[x_min - margen_x, x_max + margen_x],
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black',
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title='Z [m]',
                range=[z_min - margen_z, z_max + margen_z],
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black',
                gridcolor='lightgray'
            ),
            hovermode='closest',
            showlegend=True,
            legend=dict(
                x=1.02,
                y=1,
                xanchor='left',
                yanchor='top'
            ),
            width=1200,
            height=800,
            plot_bgcolor='white'
        )
