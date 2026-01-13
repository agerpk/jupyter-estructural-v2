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
        
        # 1.5. Dibujar offsets (líneas punteadas grises)
        self._dibujar_offsets(fig)
        
        # 2. Dibujar nodos
        self._dibujar_nodos(fig)
        
        # 3. Dibujar cables (líneas punteadas desde conductores)
        self._dibujar_cables(fig)
        
        # 4. Dibujar cotas
        self._dibujar_cotas(fig)
        
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
    
    def _dibujar_offsets(self, fig):
        """Dibujar offsets de columnas y ménsulas como líneas punteadas grises"""
        from utils.offset_geometria import calcular_offset_columna, calcular_offset_mensula
        
        print(f"\n🎨 DEBUG OFFSETS - GraficoEstructura2D")
        print(f"   offset_columna_base: {getattr(self.geo, 'offset_columna_base', 'NO EXISTE')}")
        print(f"   offset_columna_inter: {getattr(self.geo, 'offset_columna_inter', 'NO EXISTE')}")
        print(f"   offset_mensula: {getattr(self.geo, 'offset_mensula', 'NO EXISTE')}")
        
        if not hasattr(self.geo, 'conexiones'):
            print(f"   ❌ No hay conexiones")
            return
        
        print(f"   Total conexiones: {len(self.geo.conexiones)}")
        
        h_cross_h1 = self.geo.dimensiones.get('h1a', 0)
        print(f"   h_cross_h1: {h_cross_h1:.3f}m")
        
        offsets_dibujados = 0
        
        for origen, destino, tipo in self.geo.conexiones:
            if origen not in self.geo.nodos or destino not in self.geo.nodos:
                continue
            
            nodo_o = self.geo.nodos[origen]
            nodo_d = self.geo.nodos[destino]
            x_o, y_o, z_o = nodo_o.coordenadas
            x_d, y_d, z_d = nodo_d.coordenadas
            
            if tipo == 'columna':
                # Determinar si es base o inter
                z_min = min(z_o, z_d)
                es_base = z_min < h_cross_h1
                
                print(f"   Columna {origen}-{destino}: z_min={z_min:.3f}, es_base={es_base}")
                
                if es_base and self.geo.offset_columna_base:
                    print(f"      ✅ Dibujando offset columna base")
                    # Dibujar offset columna base con interpolación
                    import numpy as np
                    z_vals = np.linspace(z_o, z_d, 10)
                    x_left = []
                    x_right = []
                    z_plot = []
                    for z in z_vals:
                        offset = calcular_offset_columna(
                            z, 0, h_cross_h1,
                            self.geo.offset_columna_base_inicio,
                            self.geo.offset_columna_base_fin,
                            self.geo.offset_columna_base_tipo
                        )
                        if offset > 0:
                            x_left.append(-offset)
                            x_right.append(offset)
                            z_plot.append(z)
                    
                    if x_left:
                        print(f"         Dibujando {len(z_plot)} puntos interpolados")
                        # Línea izquierda
                        fig.add_trace(go.Scatter(
                            x=x_left,
                            y=z_plot,
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        # Línea derecha
                        fig.add_trace(go.Scatter(
                            x=x_right,
                            y=z_plot,
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        offsets_dibujados += 2
                
                elif not es_base and self.geo.offset_columna_inter:
                    print(f"      ✅ Dibujando offset columna inter")
                    # Dibujar offset columna inter con interpolación
                    import numpy as np
                    z_max = max(z_o, z_d)
                    z_vals = np.linspace(z_o, z_d, 10)
                    x_left = []
                    x_right = []
                    z_plot = []
                    for z in z_vals:
                        offset = calcular_offset_columna(
                            z, h_cross_h1, z_max,
                            self.geo.offset_columna_inter_inicio,
                            self.geo.offset_columna_inter_fin,
                            self.geo.offset_columna_inter_tipo
                        )
                        if offset > 0:
                            x_left.append(-offset)
                            x_right.append(offset)
                            z_plot.append(z)
                    
                    if x_left:
                        print(f"         Dibujando {len(z_plot)} puntos interpolados")
                        # Línea izquierda
                        fig.add_trace(go.Scatter(
                            x=x_left,
                            y=z_plot,
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        # Línea derecha
                        fig.add_trace(go.Scatter(
                            x=x_right,
                            y=z_plot,
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        offsets_dibujados += 2
            
            elif tipo == 'mensula' and self.geo.offset_mensula:
                print(f"   Ménsula {origen}-{destino}")
                print(f"      ✅ Dibujando offset ménsula")
                # Dibujar offset ménsula (solo +Z) con interpolación
                import numpy as np
                x_min = min(abs(x_o), abs(x_d))
                x_max = max(abs(x_o), abs(x_d))
                
                # Interpolar a lo largo de la ménsula
                if abs(x_d - x_o) > 0.01:
                    x_vals = np.linspace(x_o, x_d, 10)
                    z_vals = np.linspace(z_o, z_d, 10)
                    
                    x_plot = []
                    z_plot = []
                    for x, z in zip(x_vals, z_vals):
                        offset = calcular_offset_mensula(
                            abs(x), x_min, x_max,
                            self.geo.offset_mensula_inicio,
                            self.geo.offset_mensula_fin,
                            self.geo.offset_mensula_tipo
                        )
                        if offset > 0:
                            x_plot.append(x)
                            z_plot.append(z + offset)
                    
                    if x_plot:
                        print(f"         Dibujando {len(x_plot)} puntos interpolados")
                        fig.add_trace(go.Scatter(
                            x=x_plot,
                            y=z_plot,
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        offsets_dibujados += 1
        
        print(f"   ✅ Total offsets dibujados: {offsets_dibujados}")
    
    def _dibujar_nodos(self, fig):
        """Dibujar nodos con colores y símbolos por tipo"""
        Lk = self.geo.lk
        
        # Dibujar nodos conductor (azul) y extremos de cadena (rojo)
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        primera_vez_conductor = True
        primera_vez_extremo = True
        primera_vez_cadena = True
        
        for nombre, nodo in conductores:
            x, y, z = nodo.coordenadas
            
            # Nodo amarre (azul)
            fig.add_trace(go.Scatter(
                x=[x],
                y=[z],
                mode='markers+text',
                marker=dict(
                    size=10,
                    color='blue',
                    symbol='circle',
                    line=dict(width=1, color='black')
                ),
                text=[nombre],
                textposition='top center',
                textfont=dict(size=9),
                name='Amarre conductor' if primera_vez_conductor else None,
                showlegend=primera_vez_conductor,
                legendgroup='conductor',
                hovertemplate=f'<b>{nombre}</b><br>x={x:.2f}m<br>z={z:.2f}m<extra></extra>'
            ))
            primera_vez_conductor = False
            
            # Extremo de cadena (rojo) - Lk por debajo
            z_extremo = z - Lk
            fig.add_trace(go.Scatter(
                x=[x],
                y=[z_extremo],
                mode='markers',
                marker=dict(
                    size=8,
                    color='red',
                    symbol='circle',
                    line=dict(width=1, color='black')
                ),
                name='Extremo cadena' if primera_vez_extremo else None,
                showlegend=primera_vez_extremo,
                legendgroup='extremo',
                hovertemplate=f'<b>{nombre} (extremo)</b><br>x={x:.2f}m<br>z={z_extremo:.2f}m<extra></extra>'
            ))
            primera_vez_extremo = False
            
            # Cadena (línea gris punteada)
            fig.add_trace(go.Scatter(
                x=[x, x],
                y=[z, z_extremo],
                mode='lines',
                line=dict(color='gray', width=2, dash='dot'),
                name='Cadena Lk' if primera_vez_cadena else None,
                showlegend=primera_vez_cadena,
                legendgroup='cadena',
                hoverinfo='skip'
            ))
            primera_vez_cadena = False
        
        # Dibujar nodos guardia (verde)
        guardias = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "guardia"]
        
        primera_vez_guardia = True
        for nombre, nodo in guardias:
            x, y, z = nodo.coordenadas
            
            fig.add_trace(go.Scatter(
                x=[x],
                y=[z],
                mode='markers+text',
                marker=dict(
                    size=10,
                    color='green',
                    symbol='circle',
                    line=dict(width=1, color='black')
                ),
                text=[nombre],
                textposition='top center',
                textfont=dict(size=9),
                name='Cable guardia' if primera_vez_guardia else None,
                showlegend=primera_vez_guardia,
                legendgroup='guardia',
                hovertemplate=f'<b>{nombre}</b><br>x={x:.2f}m<br>z={z:.2f}m<extra></extra>'
            ))
            primera_vez_guardia = False
        
        # Dibujar otros nodos sin nombres (base, cruce, general)
        otros = [(n, nodo) for n, nodo in self.geo.nodos.items() 
                 if nodo.tipo_nodo not in ["conductor", "guardia"]]
        
        for nombre, nodo in otros:
            x, y, z = nodo.coordenadas
            
            fig.add_trace(go.Scatter(
                x=[x],
                y=[z],
                mode='markers',
                marker=dict(
                    size=6,
                    color='gray',
                    symbol='circle',
                    line=dict(width=1, color='black')
                ),
                showlegend=False,
                hovertemplate=f'<b>{nombre}</b><br>x={x:.2f}m<br>z={z:.2f}m<extra></extra>'
            ))
    
    def _dibujar_cables(self, fig):
        """Dibujar cotas de alturas para primera altura"""
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        if not conductores:
            return
        
        z_min = min(nodo.coordenadas[2] for _, nodo in conductores)
        primera_altura = [(n, nodo) for n, nodo in conductores if abs(nodo.coordenadas[2] - z_min) < 0.01]
        
        if not primera_altura:
            return
        
        nodo_ref_nombre, nodo_ref = max(primera_altura, key=lambda item: item[1].coordenadas[0])
        x_ref, y_ref, z_ref = nodo_ref.coordenadas
        
        Lk = self.geo.lk
        z_extremo_cadena = z_ref - Lk
        
        # Obtener datos
        termino_flecha = self.geo.dimensiones.get('termino_flecha', 0)
        if termino_flecha > 0:
            flecha_max = termino_flecha - Lk
        else:
            flecha_max = 0
        
        altura_electrica = self.geo.dimensiones.get('h_base_electrica', 0)
        if altura_electrica == 0:
            altura_electrica = self.geo.dimensiones.get('altura_base_electrica', 0)
        
        hadd = self.geo.hadd if hasattr(self.geo, 'hadd') else 0
        
        if flecha_max == 0 or altura_electrica == 0:
            return
        
        x_linea = x_ref
        
        # 1. Flecha máxima (línea vertical roja punteada desde extremo cadena hacia abajo)
        z_inicio_flecha = z_extremo_cadena
        z_fin_flecha = z_extremo_cadena - flecha_max
        
        fig.add_trace(go.Scatter(
            x=[x_linea, x_linea],
            y=[z_inicio_flecha, z_fin_flecha],
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_annotation(
            x=x_linea + 0.2,
            y=(z_inicio_flecha + z_fin_flecha) / 2,
            text=f'f={flecha_max:.2f}m',
            showarrow=False,
            xanchor='left',
            font=dict(size=9, color='red'),
            bgcolor='white',
            borderpad=2
        )
        
        # 2. Altura eléctrica (línea vertical gris punteada desde fin flecha hacia abajo)
        z_inicio_electrica = z_fin_flecha
        z_fin_electrica = z_fin_flecha - altura_electrica
        
        fig.add_trace(go.Scatter(
            x=[x_linea, x_linea],
            y=[z_inicio_electrica, z_fin_electrica],
            mode='lines',
            line=dict(color='gray', width=2, dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_annotation(
            x=x_linea + 0.2,
            y=(z_inicio_electrica + z_fin_electrica) / 2,
            text=f'a+b={altura_electrica:.2f}m',
            showarrow=False,
            xanchor='left',
            font=dict(size=9, color='gray'),
            bgcolor='white',
            borderpad=2
        )
        
        # 3. HADD (línea vertical naranja punteada desde fin electrica hacia abajo)
        if hadd > 0:
            z_inicio_hadd = z_fin_electrica
            z_fin_hadd = z_fin_electrica - hadd
            
            fig.add_trace(go.Scatter(
                x=[x_linea, x_linea],
                y=[z_inicio_hadd, z_fin_hadd],
                mode='lines',
                line=dict(color='orange', width=2, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig.add_annotation(
                x=x_linea + 0.2,
                y=(z_inicio_hadd + z_fin_hadd) / 2,
                text=f'HADD={hadd:.2f}m',
                showarrow=False,
                xanchor='left',
                font=dict(size=9, color='orange'),
                bgcolor='white',
                borderpad=2
            )
            z_terreno = z_fin_hadd
        else:
            z_terreno = z_fin_electrica
        
        # 4. Línea negra horizontal (terreno)
        fig.add_trace(go.Scatter(
            x=[x_ref - 0.6, x_ref + 0.6],
            y=[z_terreno, z_terreno],
            mode='lines',
            line=dict(color='black', width=3),
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
    
    def _dibujar_cotas(self, fig):
        """Dibujar cotas de distancias verticales y horizontales"""
        # Cota vertical entre BASE y primer CROSS_H*
        if 'BASE' in self.geo.nodos:
            cross_nodes = sorted(
                [(n, nodo) for n, nodo in self.geo.nodos.items() if 'CROSS_H' in n],
                key=lambda x: x[1].coordenadas[2]
            )
            
            if cross_nodes:
                nodo_base = self.geo.nodos['BASE']
                primer_cross = cross_nodes[0][1]
                x_base, y_base, z_base = nodo_base.coordenadas
                x_cross, y_cross, z_cross = primer_cross.coordenadas
                dist = z_cross - z_base
                z_medio = (z_base + z_cross) / 2
                
                # Línea de cota
                fig.add_trace(go.Scatter(
                    x=[0.3, 0.6],
                    y=[z_medio, z_medio],
                    mode='lines',
                    line=dict(color='gray', width=1, dash='dot'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Texto de cota
                fig.add_annotation(
                    x=0.6,
                    y=z_medio,
                    text=f'{dist:.2f}m',
                    showarrow=False,
                    xanchor='left',
                    font=dict(size=9, color='black'),
                    bgcolor='white',
                    borderpad=2
                )
        
        # 4. Cotas verticales entre CROSS_H*
        cross_nodes = sorted(
            [(n, nodo) for n, nodo in self.geo.nodos.items() if 'CROSS_H' in n],
            key=lambda x: x[1].coordenadas[2]
        )
        
        for i in range(len(cross_nodes) - 1):
            n1, nodo1 = cross_nodes[i]
            n2, nodo2 = cross_nodes[i + 1]
            x1, y1, z1 = nodo1.coordenadas
            x2, y2, z2 = nodo2.coordenadas
            dist = z2 - z1
            z_medio = (z1 + z2) / 2
            
            # Línea de cota
            fig.add_trace(go.Scatter(
                x=[0.3, 0.6],
                y=[z_medio, z_medio],
                mode='lines',
                line=dict(color='gray', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Texto de cota
            fig.add_annotation(
                x=0.6,
                y=z_medio,
                text=f'{dist:.2f}m',
                showarrow=False,
                xanchor='left',
                font=dict(size=9, color='black'),
                bgcolor='white',
                borderpad=2
            )
        
        # Cota entre último CROSS y TOP (si existe)
        if cross_nodes and 'TOP' in self.geo.nodos:
            ultimo_cross = cross_nodes[-1][1]
            nodo_top = self.geo.nodos['TOP']
            x1, y1, z1 = ultimo_cross.coordenadas
            x2, y2, z2 = nodo_top.coordenadas
            dist = z2 - z1
            z_medio = (z1 + z2) / 2
            
            fig.add_trace(go.Scatter(
                x=[0.3, 0.6],
                y=[z_medio, z_medio],
                mode='lines',
                line=dict(color='gray', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_annotation(
                x=0.6,
                y=z_medio,
                text=f'{dist:.2f}m',
                showarrow=False,
                xanchor='left',
                font=dict(size=9, color='black'),
                bgcolor='white',
                borderpad=2
            )
        
        # 5. Cotas horizontales entre CROSS y conductores (x positivo)
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
        
        # 6. Cota horizontal entre TOP y HG (x positivo)
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
        # Calcular límites
        x_vals = [nodo.coordenadas[0] for nodo in self.geo.nodos.values()]
        z_vals = [nodo.coordenadas[2] for nodo in self.geo.nodos.values()]
        
        x_min, x_max = min(x_vals), max(x_vals)
        z_min, z_max = min(z_vals), max(z_vals)
        
        # Agregar margen
        margen_x = (x_max - x_min) * 0.2 if x_max != x_min else 5
        margen_z = (z_max - z_min) * 0.1 if z_max != z_min else 2
        
        # Determinar dtick según rango (zoom) - default 2.0m
        dtick_default = 2.0
        
        # Valores de grid disponibles
        grid_values = [0.1, 0.25, 0.5, 1.0, 2.0, 2.5, 5.0]
        
        # Crear steps para el slider
        steps = []
        for val in grid_values:
            step = dict(
                method="relayout",
                args=[{
                    "xaxis.dtick": val,
                    "yaxis.dtick": val
                }],
                label=f"{val}m"
            )
            steps.append(step)
        
        # Índice del valor default (2.0m)
        default_idx = grid_values.index(2.0)
        
        sliders = [dict(
            active=default_idx,
            yanchor="top",
            y=0.70,
            xanchor="left",
            x=1.02,
            currentvalue=dict(
                prefix="Grid: ",
                visible=True,
                xanchor="left"
            ),
            pad=dict(b=10, t=10),
            len=0.15,
            steps=steps
        )]
        
        fig.update_layout(
            title='Estructura Completa - Vista Lateral (XZ)',
            xaxis=dict(
                title='X [m]',
                scaleanchor='y',
                scaleratio=1,
                range=[x_min - margen_x, x_max + margen_x],
                zeroline=False,
                gridcolor='rgba(200, 200, 200, 0.3)',
                dtick=dtick_default
            ),
            yaxis=dict(
                title='Z [m]',
                range=[z_min - margen_z, z_max + margen_z],
                zeroline=False,
                gridcolor='rgba(200, 200, 200, 0.3)',
                dtick=dtick_default
            ),
            hovermode='closest',
            showlegend=True,
            legend=dict(
                x=1.02,
                y=1,
                xanchor='left',
                yanchor='top'
            ),
            sliders=sliders,
            width=1200,
            height=800,
            plot_bgcolor='white',
            shapes=[
                # Línea de terreno en z=0
                dict(
                    type='line',
                    x0=x_min - margen_x,
                    x1=x_max + margen_x,
                    y0=0,
                    y1=0,
                    line=dict(color='brown', width=1)
                )
            ]
        )
