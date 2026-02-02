# GraficoCabezal2D.py
import plotly.graph_objects as go
import math
import re
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
        s_reposo = self.geo.dimensiones.get('s_reposo', 0)
        s_tormenta = self.geo.dimensiones.get('s_tormenta', 0)
        s_decmax = self.geo.dimensiones.get('s_decmax', 0)
        D_fases = self.geo.dimensiones.get('D_fases', 0)
        Dhg = self.geo.dimensiones.get('Dhg', 0)
        
        # Validar que s_reposo, s_tormenta, s_decmax no sean 0
        if s_reposo <= 0:
            raise ValueError(f"Error: s_reposo no puede ser {s_reposo}")
        if s_tormenta <= 0:
            raise ValueError(f"Error: s_tormenta no puede ser {s_tormenta}")
        if s_decmax <= 0:
            raise ValueError(f"Error: s_decmax no puede ser {s_decmax}")
        
        print(f"\n=== DEBUG RADIOS ===")
        print(f"s_reposo: {s_reposo}")
        print(f"s_tormenta: {s_tormenta}")
        print(f"s_decmax: {s_decmax}")
        print(f"D_fases: {D_fases}")
        print(f"Dhg: {Dhg}")
        
        # 1. Dibujar estructura base
        self._dibujar_conexiones(fig)
        
        # 1.5. Dibujar offsets (líneas punteadas grises)
        self._dibujar_offsets(fig)
        
        # 2. Dibujar nodos
        self._dibujar_nodos(fig)
        
        # 3. Dibujar conductores con declinaciones y zonas
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        # Encontrar z máxima de conductores
        z_max_conductor = max(nodo.coordenadas[2] for _, nodo in conductores) if conductores else 0
        
        for nombre_c, nodo_c in conductores:
            x_amarre, y_amarre, z_amarre = nodo_c.coordenadas
            es_z_max = abs(z_amarre - z_max_conductor) < 0.01
            
            # Determinar signo según posición X (>=0 => derecha, <0 => izquierda)
            sign = 1 if x_amarre >= 0 else -1

            # Generar solo declinaciones hacia adentro (hacia x=0): x_cond = x_amarre - sign*offset
            posiciones = [
                (x_amarre, z_amarre - Lk, 'reposo', s_reposo, True, True, True, es_z_max),
                (x_amarre - sign * Lk * math.sin(math.radians(theta_tormenta)),
                 z_amarre - Lk * math.cos(math.radians(theta_tormenta)), 'tormenta', s_tormenta, False, False, True, False),
                (x_amarre - sign * Lk * math.sin(math.radians(theta_max)),
                 z_amarre - Lk * math.cos(math.radians(theta_max)), 'decmax', s_decmax, False, False, True, False)
            ]
            
            for x_cond, z_cond, estado, s_val, visible, mostrar_dfases, mostrar_s, mostrar_dhg in posiciones:
                # Cadena
                fig.add_trace(go.Scatter(
                    x=[x_amarre, x_cond], y=[z_amarre, z_cond],
                    mode='lines', line=dict(color='gray', width=2),
                    name=f'{nombre_c}_{estado}_cadena',
                    visible=False,
                    showlegend=False, hoverinfo='skip'
                ))
                
                # Conductor
                fig.add_trace(go.Scatter(
                    x=[x_cond], y=[z_cond],
                    mode='markers', marker=dict(size=8, color='red'),
                    name=f'{nombre_c}_{estado}_punto',
                    visible=False,
                    showlegend=False, hoverinfo='skip'
                ))
                
                # Zona D_fases (solo en reposo)
                if mostrar_dfases:
                    fig.add_trace(self._crear_circulo(x_cond, z_cond, D_fases, 'green', 0.05,
                        f'{nombre_c}_{estado}_D_fases', False))
                    fig.add_trace(go.Scatter(
                        x=[x_cond], y=[z_cond + D_fases + D_fases * 0.05],
                        mode='text', text=[f'D_fases<br>{D_fases:.2f}m'], textfont=dict(size=9, color='green'),
                        name=f'{nombre_c}_{estado}_D_fases_label', showlegend=False, hoverinfo='skip', visible=False
                    ))
                
                # Zona Dhg (solo en reposo de z máxima)
                if mostrar_dhg:
                    fig.add_trace(self._crear_circulo(x_cond, z_cond, Dhg, 'purple', 0.05,
                        f'{nombre_c}_{estado}_Dhg', False))
                    fig.add_trace(go.Scatter(
                        x=[x_cond], y=[z_cond + Dhg + Dhg * 0.05],
                        mode='text', text=[f'Dhg<br>{Dhg:.2f}m'], textfont=dict(size=9, color='purple'),
                        name=f'{nombre_c}_{estado}_Dhg_label', showlegend=False, hoverinfo='skip', visible=False
                    ))
                
                # Zona s_reposo/s_tormenta/s_decmax (según corresponda)
                if mostrar_s:
                    fig.add_trace(self._crear_circulo(x_cond, z_cond, s_val, 'blue', 0.1,
                        f'{nombre_c}_{estado}_s_zona', False))
                    # Etiquetas específicas según tipo de estado. Usar color azul uniforme y centrado cuando corresponda
                    if 'tormenta' in estado:
                        fig.add_trace(go.Scatter(
                            x=[x_cond - s_val - 0.05], y=[z_cond],
                            mode='text', text=[f's_tormenta<br>{s_val:.2f}m'], textfont=dict(size=9, color='blue'),
                            textposition='middle center',
                            name=f'{nombre_c}_{estado}_s_label', showlegend=False, hoverinfo='skip', visible=False
                        ))
                    elif 'decmax' in estado:
                        fig.add_trace(go.Scatter(
                            x=[x_cond], y=[z_cond - s_val - 0.05],
                            mode='text', text=[f's_decmax<br>{s_val:.2f}m'], textfont=dict(size=9, color='blue'),
                            textposition='middle center',
                            name=f'{nombre_c}_{estado}_s_label', showlegend=False, hoverinfo='skip', visible=False
                        ))
                    else:
                        # reposo
                        fig.add_trace(go.Scatter(
                            x=[x_cond], y=[z_cond + s_val + s_val * 0.05],
                            mode='text', text=[f's_reposo<br>{s_val:.2f}m'], textfont=dict(size=9, color='blue'),
                            name=f'{nombre_c}_{estado}_s_label', showlegend=False, hoverinfo='skip', visible=False
                        ))
        
        # 4. Zona apantallamiento
        if self.geo.cant_hg > 0:
            self._dibujar_zona_apantallamiento(fig)
        
        # 5. Dibujar cotas
        self._dibujar_cotas(fig)
        
        # 5.5 Dibujar vista GENERAL (círculos/áreas/resumen) - visible por defecto
        self._dibujar_vista_general(fig, conductores)

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
        
        # Crear índices de traces por patrón (excluir traces de la VISTA GENERAL que empiezan con 'GENERAL_')
        indices_dfases = [i for i, trace in enumerate(fig.data) if 'D_fases' in (trace.name or '') and not (trace.name or '').startswith('GENERAL_')]
        indices_dhg = [i for i, trace in enumerate(fig.data) if 'Dhg' in (trace.name or '') and not (trace.name or '').startswith('GENERAL_')]
        indices_reposo_s = [i for i, trace in enumerate(fig.data) if 'reposo_s_zona' in (trace.name or '') and not (trace.name or '').startswith('GENERAL_')]
        indices_tormenta_s = [i for i, trace in enumerate(fig.data) if 'tormenta' in (trace.name or '') and 's_zona' in (trace.name or '') and not (trace.name or '').startswith('GENERAL_')]
        indices_decmax_s = [i for i, trace in enumerate(fig.data) if 'decmax' in (trace.name or '') and 's_zona' in (trace.name or '') and not (trace.name or '').startswith('GENERAL_')]
        indices_apantallamiento = [i for i, trace in enumerate(fig.data) if 'apantallamiento' in (trace.name or '') and not (trace.name or '').startswith('GENERAL_')]
        # Índices para VISTA GENERAL (traces con prefijo GENERAL_)
        indices_general = [i for i, trace in enumerate(fig.data) if (trace.name or '').startswith('GENERAL_')]
        
        # Inicializar estado: la ESTRUCTURA BASE visible por defecto; GENERAL ON por defecto
        for i, trace in enumerate(fig.data):
            name = trace.name or ''
            # Considerar base los trazos sin nombre (offsets, cotas), conexiones y nodos visibles siempre
            is_base = (name == '') or name.startswith('conexion_') or name in ('Conductor', 'Guardia', 'Viento')
            if is_base or name.startswith('GENERAL_'):
                trace.visible = True
            else:
                trace.visible = False

        # Crear lista de visibilidad base (mantener estado actual de cada trace; por defecto False si no especificado)
        def crear_visibility(indices_mostrar):
            return [i in indices_mostrar or (trace.visible if isinstance(trace.visible, bool) else False)
                    for i, trace in enumerate(fig.data)]

        def crear_visibility_ocultar(indices_ocultar):
            return [False if i in indices_ocultar else (trace.visible if isinstance(trace.visible, bool) else False)
                    for i, trace in enumerate(fig.data)]

        # Helpers que fuerzan comportamiento respecto a la VISTA GENERAL
        def crear_visibility_excluding_general(indices_mostrar):
            vis = crear_visibility(indices_mostrar)
            for i in indices_general:
                if 0 <= i < len(vis):
                    vis[i] = False
            return vis

        def crear_visibility_only_general():
            # Activar traces GENERAL sin cambiar la visibilidad actual del resto
            return [(i in indices_general) or (trace.visible if isinstance(trace.visible, bool) else False)
                    for i, trace in enumerate(fig.data)]

        # Construir índices adicionales para control fino
        indices_base = [i for i, trace in enumerate(fig.data)
                        if (trace.name or '') == '' or (trace.name or '').startswith('conexion_') or (trace.name or '') in ('Guardia', 'Viento')]

        # Añadir al estado base el 'reposo' del conductor principal sin hardcodear nombres (case-insensitive)
        primary_name = None
        # Preferir nodos que empiecen por 'c1_r' o 'c1' (case-insensitive)
        for pref in ('c1_r', 'c1'):
            found = None
            for n, nodo in conductores:
                if n.lower().startswith(pref):
                    found = n
                    break
            if found:
                primary_name = found
                break

        # Si no existe pref, elegir el conductor más central por |x|
        if primary_name is None and conductores:
            primary_name = min(conductores, key=lambda item: abs(item[1].coordenadas[0]))[0]

        if primary_name:
            # Solo incluir el marcador de 'reposo' del conductor primario (no cadena, no area, no label)
            punto_name = f'{primary_name}_reposo_punto'
            for i, trace in enumerate(fig.data):
                name = trace.name or ''
                if name == punto_name:
                    if i not in indices_base:
                        indices_base.append(i)
                    try:
                        fig.data[i].visible = True
                    except Exception:
                        pass

        # Use stricter matching to avoid picking up D_fases/Dhg traces that include '_reposo' as a prefix in their names
        indices_reposo_all = [i for i, t in enumerate(fig.data)
                               if re.search(r'_reposo(?:$|_)', (t.name or '')) and not (t.name or '').startswith('GENERAL_')
                               and 'D_fases' not in (t.name or '') and 'Dhg' not in (t.name or '')]
        indices_reposo_chains_points = [i for i, t in enumerate(fig.data)
                                        if re.search(r'_reposo_(?:cadena|punto)', (t.name or '')) and not (t.name or '').startswith('GENERAL_')]
        indices_dfases_all = [i for i, t in enumerate(fig.data) if 'D_fases' in (t.name or '') and not (t.name or '').startswith('GENERAL_')]
        indices_dhg_all = [i for i, t in enumerate(fig.data) if 'Dhg' in (t.name or '') and not (t.name or '').startswith('GENERAL_')]
        indices_tormenta_all = [i for i, t in enumerate(fig.data) if 'tormenta' in (t.name or '') and not (t.name or '').startswith('GENERAL_')]
        indices_decmax_all = [i for i, t in enumerate(fig.data) if 'decmax' in (t.name or '') and not (t.name or '').startswith('GENERAL_')]

        # DEBUG temporary: print trace names for these index groups to detect overlaps while debugging s_reposo contamination
        try:
            names_reposo = [fig.data[i].name for i in indices_reposo_all]
            names_dfases = [fig.data[i].name for i in indices_dfases_all]
            names_dhg = [fig.data[i].name for i in indices_dhg_all]
            print(f"DEBUG indices_reposo_all ({len(names_reposo)}): {names_reposo}")
            print(f"DEBUG indices_dfases_all ({len(names_dfases)}): {names_dfases}")
            print(f"DEBUG indices_dhg_all ({len(names_dhg)}): {names_dhg}")
        except Exception:
            pass

        # Todos los overlays (usados cuando apagamos todo)
        indices_overlays = set(list(indices_dfases_all) + list(indices_dhg_all) + list(indices_reposo_all) + list(indices_tormenta_all) + list(indices_decmax_all) + list(indices_apantallamiento) + list(indices_general))

        # Helper para crear visibilidad inicial (base visible, overlays por defecto off)
        def visibility_base_only():
            return [True if i in indices_base else False for i, _ in enumerate(fig.data)]

        # Helper: mantener GENERAL sin tocar (en ON), pero activar indices específicos
        def visibility_activate(indices_to_activate):
            vis = [trace.visible if isinstance(trace.visible, bool) else (i in indices_base)
                   for i, trace in enumerate(fig.data)]
            for i in indices_to_activate:
                if 0 <= i < len(vis):
                    vis[i] = True
            return vis

        # Helper: apagar completamente overlays + GENERAL y volver a base
        def visibility_all_off():
            vis = [True if i in indices_base else False for i, _ in enumerate(fig.data)]
            return vis

        # Construir listas específicas para tor/dec segun lado (x signo) de forma robusta
        tor_on_indices = []
        dec_on_indices = []
        # Map names to indices for fast lookup
        name_to_index = { (t.name or ''): i for i, t in enumerate(fig.data) }

        for i, t in enumerate(fig.data):
            name = t.name or ''
            if name.startswith('GENERAL_'):
                continue
            # Buscamos cadenas de tormenta/decmax que contengan '_cadena' (tienen x[0]=amarre, x[1]=cond)
            if '_cadena' in name and ('tormenta' in name or 'decmax' in name):
                try:
                    x_vals = t.x if hasattr(t, 'x') else None
                    if not x_vals or len(x_vals) < 2:
                        continue
                    delta_x = x_vals[1] - x_vals[0]
                    amarre_x = x_vals[0]
                except Exception:
                    continue

                # Determinar lado deseado para declinaciones INWARD (hacia el centro):
                # si amarre_x >=0 (derecha), la cadena hacia adentro tendrá delta_x negativo (-1)
                desired_inward = -1 if amarre_x >= 0 else 1
                side = 1 if delta_x > 0 else (-1 if delta_x < 0 else 0)

                if 'tormenta' in name and side == desired_inward:
                    # incluir la cadena, el punto y el s_zona asociado
                    tor_on_indices.append(i)
                    punto_name = name.replace('_cadena', '_punto')
                    zona_name = name.replace('_cadena', '_s_zona')
                    label_name = name.replace('_cadena', '_s_label')
                    if punto_name in name_to_index:
                        tor_on_indices.append(name_to_index[punto_name])
                    if zona_name in name_to_index:
                        tor_on_indices.append(name_to_index[zona_name])
                    if label_name in name_to_index:
                        tor_on_indices.append(name_to_index[label_name])
                if 'decmax' in name and side == desired_inward:
                    dec_on_indices.append(i)
                    punto_name = name.replace('_cadena', '_punto')
                    zona_name = name.replace('_cadena', '_s_zona')
                    label_name = name.replace('_cadena', '_s_label')
                    if punto_name in name_to_index:
                        dec_on_indices.append(name_to_index[punto_name])
                    if zona_name in name_to_index:
                        dec_on_indices.append(name_to_index[zona_name])
                    if label_name in name_to_index:
                        dec_on_indices.append(name_to_index[label_name])
        # Visibilidades precomputadas para cada botón
        # Use exclusive activation relative to the base (blank) view for all overlays so they don't contaminate each other
        def visibility_activate_exclusive(indices_to_activate):
            vis = visibility_base_only()
            for i in indices_to_activate:
                if 0 <= i < len(vis):
                    vis[i] = True
            return vis

        vis_d_fases_on = visibility_activate_exclusive(indices_dfases_all + indices_reposo_chains_points)
        vis_d_fases_off = visibility_all_off()

        vis_dhg_on = visibility_activate_exclusive(indices_dhg_all + indices_reposo_chains_points)
        vis_dhg_off = visibility_all_off()

        vis_s_reposo_on = visibility_activate_exclusive(indices_reposo_all)
        vis_s_reposo_off = visibility_all_off()

        vis_s_tor_on = visibility_activate_exclusive(list(set(tor_on_indices)))
        vis_s_tor_off = visibility_all_off()

        vis_s_dec_on = visibility_activate_exclusive(list(set(dec_on_indices)))
        vis_s_dec_off = visibility_all_off()

        vis_apant_on = visibility_activate_exclusive(indices_apantallamiento + indices_reposo_chains_points)
        vis_apant_off = visibility_all_off()

        # GENERAL ON/OFF (GENERAL should show base + general traces)
        vis_general_on = visibility_activate_exclusive(indices_general)
        # Hide primary reposo punto when GENERAL is ON (so GENERAL doesn't show base reposo marker)
        if primary_name:
            # Find any trace whose name matches '<primary>_reposo_punto' case-insensitive and hide it
            primary_key = f'{primary_name.lower()}_reposo_punto'
            for i, t in enumerate(fig.data):
                name_i = (t.name or '').lower()
                if name_i == primary_key:
                    if 0 <= i < len(vis_general_on):
                        vis_general_on[i] = False
        vis_general_off = visibility_all_off()

        updatemenus = [
            dict(type='buttons', direction='right', x=1.02, xanchor='left', y=0.70, yanchor='top',
                 buttons=[
                     dict(label='D_fases: OFF', method='update', args=[{'visible': vis_d_fases_off}]),
                     dict(label='D_fases: ON', method='update', args=[{'visible': vis_d_fases_on}])
                 ], active=0),

            dict(type='buttons', direction='right', x=1.02, xanchor='left', y=0.635, yanchor='top',
                 buttons=[
                     dict(label='Dhg: OFF', method='update', args=[{'visible': vis_dhg_off}]),
                     dict(label='Dhg: ON', method='update', args=[{'visible': vis_dhg_on}])
                 ], active=0),

            dict(type='buttons', direction='right', x=1.02, xanchor='left', y=0.57, yanchor='top',
                 buttons=[
                     dict(label='s_reposo: OFF', method='update', args=[{'visible': vis_s_reposo_off}]),
                     dict(label='s_reposo: ON', method='update', args=[{'visible': vis_s_reposo_on}])
                 ], active=0),

            dict(type='buttons', direction='right', x=1.02, xanchor='left', y=0.505, yanchor='top',
                 buttons=[
                     dict(label='s_tormenta: OFF', method='update', args=[{'visible': vis_s_tor_off}]),
                     dict(label='s_tormenta: ON', method='update', args=[{'visible': vis_s_tor_on}])
                 ], active=0),

            dict(type='buttons', direction='right', x=1.02, xanchor='left', y=0.44, yanchor='top',
                 buttons=[
                     dict(label='s_decmax: OFF', method='update', args=[{'visible': vis_s_dec_off}]),
                     dict(label='s_decmax: ON', method='update', args=[{'visible': vis_s_dec_on}])
                 ], active=0),

            dict(type='buttons', direction='right', x=1.02, xanchor='left', y=0.375, yanchor='top',
                 buttons=[
                     dict(label='Apantallamiento: OFF', method='update', args=[{'visible': vis_apant_off}]),
                     dict(label='Apantallamiento: ON', method='update', args=[{'visible': vis_apant_on}])
                 ], active=0),

            dict(type='buttons', direction='right', x=1.02, xanchor='left', y=0.31, yanchor='top',
                 buttons=[
                     dict(label='GENERAL: OFF', method='update', args=[{'visible': vis_general_off}]),
                     dict(label='GENERAL: ON', method='update', args=[{'visible': vis_general_on}])
                 ], active=1)
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
    
    def _dibujar_offsets(self, fig):
        """Dibujar offsets de columnas y ménsulas como líneas punteadas grises"""
        from utils.offset_geometria import calcular_offset_columna, calcular_offset_mensula
        
        # print(f"\n🎨 DEBUG OFFSETS - GraficoCabezal2D")
        # print(f"   offset_columna_base: {getattr(self.geo, 'offset_columna_base', 'NO EXISTE')}")
        # print(f"   offset_columna_inter: {getattr(self.geo, 'offset_columna_inter', 'NO EXISTE')}")
        # print(f"   offset_mensula: {getattr(self.geo, 'offset_mensula', 'NO EXISTE')}")
        
        if not hasattr(self.geo, 'conexiones'):
            # print(f"   ❌ No hay conexiones")
            return
        
        # print(f"   Total conexiones: {len(self.geo.conexiones)}")
        
        h_cross_h1 = self.geo.dimensiones.get('h1a', 0)
        # print(f"   h_cross_h1: {h_cross_h1:.3f}m")
        
        offsets_dibujados = 0
        
        for origen, destino, tipo in self.geo.conexiones:
            if origen not in self.geo.nodos or destino not in self.geo.nodos:
                continue
            
            nodo_o = self.geo.nodos[origen]
            nodo_d = self.geo.nodos[destino]
            x_o, y_o, z_o = nodo_o.coordenadas
            x_d, y_d, z_d = nodo_d.coordenadas
            
            if tipo == 'columna':
                z_min = min(z_o, z_d)
                es_base = z_min < h_cross_h1
                
                # print(f"   Columna {origen}-{destino}: z_min={z_min:.3f}, es_base={es_base}")
                
                if es_base and self.geo.offset_columna_base:
                    # print(f"      ✅ Dibujando offset columna base")
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
                        # print(f"         Dibujando {len(z_plot)} puntos interpolados")
                        fig.add_trace(go.Scatter(
                            x=x_left,
                            y=z_plot,
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
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
                    # print(f"      ✅ Dibujando offset columna inter")
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
                        # print(f"         Dibujando {len(z_plot)} puntos interpolados")
                        fig.add_trace(go.Scatter(
                            x=x_left,
                            y=z_plot,
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
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
                # print(f"   Ménsula {origen}-{destino}")
                # print(f"      ✅ Dibujando offset ménsula")
                import numpy as np
                x_min = min(abs(x_o), abs(x_d))
                x_max = max(abs(x_o), abs(x_d))
                
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
                        # print(f"         Dibujando {len(x_plot)} puntos interpolados")
                        fig.add_trace(go.Scatter(
                            x=x_plot,
                            y=z_plot,
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        offsets_dibujados += 1
        
        # print(f"   ✅ Total offsets dibujados: {offsets_dibujados}")
    
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
                if nodo.tipo_nodo == 'conductor' and not (n.startswith('V') or n.startswith('Viento')) and abs(nodo.coordenadas[2] - z_cross) < 0.1 and nodo.coordenadas[0] > 0.01
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
                # Excluir nodos que se llamen 'V' o 'Viento' si existieran
                guardias_pos = [(n, nodo) for n, nodo in guardias_pos if not (n.startswith('V') or n.startswith('Viento'))]
                if not guardias_pos:
                    return
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

        # --- Cotas verticales para elementos 'columna' (longitud de columna) ---
        for origen, destino, tipo in self.geo.conexiones:
            if tipo != 'columna':
                continue
            if origen not in self.geo.nodos or destino not in self.geo.nodos:
                continue

            nodo_o = self.geo.nodos[origen]
            nodo_d = self.geo.nodos[destino]
            x_o, y_o, z_o = nodo_o.coordenadas
            x_d, y_d, z_d = nodo_d.coordenadas

            # Posicionar cota ligeramente al lado de la columna para evitar solapamiento
            x_centro = (x_o + x_d) / 2.0
            offset = 0.3 if x_centro >= 0 else -0.3
            x_cota = x_centro + offset

            z_min = min(z_o, z_d)
            z_max = max(z_o, z_d)
            longitud = z_max - z_min

            # Línea de cota vertical (punteada)
            fig.add_trace(go.Scatter(
                x=[x_cota, x_cota],
                y=[z_min, z_max],
                mode='lines',
                line=dict(color='gray', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
            # Marcadores circulares en los extremos
            fig.add_trace(go.Scatter(
                x=[x_cota, x_cota],
                y=[z_min, z_max],
                mode='markers',
                marker=dict(size=6, color='gray'),
                showlegend=False,
                hoverinfo='skip'
            ))
            # Anotación con la longitud en el medio
            fig.add_annotation(
                x=x_cota,
                y=(z_min + z_max) / 2.0,
                text=f'{longitud:.2f}m',
                showarrow=False,
                xanchor='center',
                yanchor='middle',
                font=dict(size=9, color='black'),
                bgcolor='white',
                borderpad=2
            )
    
    def _dibujar_vista_general(self, fig, conductores):
        """Dibujar elementos resumidos para la 'Vista GENERAL' (ON por defecto).

        - Círculo Dhg en HG1 con etiqueta Dist. Guardia/Salto
        - Primer conductor (C1 / C1_R) con zonas s_reposo, s_tormenta, s_decmax y etiquetas
        - Segundo nivel (C2 / C2_R / C3) en reposo con su zona s_reposo y etiqueta (si existe)
        - Etiqueta de Apantallamiento con ángulo
        """
        # Calcular dimensiones básicas
        x_vals = [nodo.coordenadas[0] for nodo in self.geo.nodos.values()]
        x_min, x_max = min(x_vals), max(x_vals)
        ancho = x_max - x_min if x_max != x_min else 1.0
        nivel = 0.1 * ancho

        Lk = self.geo.lk
        theta_max = self.geo.dimensiones.get('theta_max', 0)
        theta_tormenta = theta_max / 2.0 if theta_max < 99 else 0
        s_reposo = self.geo.dimensiones.get('s_reposo', 0)
        s_tormenta = self.geo.dimensiones.get('s_tormenta', 0)
        s_decmax = self.geo.dimensiones.get('s_decmax', 0)
        D_fases = self.geo.dimensiones.get('D_fases', 0)
        Dhg = self.geo.dimensiones.get('Dhg', 0)
        ang_apant = getattr(self.geo, 'ang_apantallamiento', None) or getattr(self.geo, 'ang_apantallamiento', 0)

        # --- Dhg en la primera HG disponible (no hardcodear 'HG1') ---
        hg_nodes = [(n, nodo) for n, nodo in self.geo.nodos.items() if n.startswith('HG')]
        if hg_nodes and Dhg > 0:
            nombre_hg, nodo_hg = hg_nodes[0]
            x_hg, y_hg, z_hg = nodo_hg.coordenadas
            fig.add_trace(self._crear_circulo(x_hg, z_hg, Dhg, 'purple', 0.08, f'GENERAL_Dhg_{nombre_hg}', False))

            # Distancia horizontal mínima a un conductor (como aproximación de 'salto')
            if conductores:
                dist_min = min(abs(x_hg - nodo.coordenadas[0]) for _, nodo in conductores)
            else:
                dist_min = 0.0

            fig.add_trace(go.Scatter(
                x=[x_hg], y=[z_hg + Dhg + Dhg * 0.05],
                mode='text', text=[f'Dist. Guardia<br>{dist_min:.2f}m'],
                textfont=dict(size=9, color='purple'),
                name=f'GENERAL_Dhg_label_{nombre_hg}', showlegend=False, hoverinfo='skip', visible=False
            ))

        # --- Primer conductor (C1 / C1_R) con zonas y etiquetas ---
        # --- Primer conductor (C1 / C1_R) con zonas y etiquetas ---
        c1_candidate = None
        if conductores:
            # Preferencia por nombres 'c1_r' o 'c1' (case-insensitive)
            for pref in ('c1_r', 'c1'):
                for n, nodo in conductores:
                    if n.lower().startswith(pref):
                        c1_candidate = (n, nodo)
                        break
                if c1_candidate:
                    break
            # Si no se encontró el pref, tomar el conductor con menor |x| (central)
            if not c1_candidate:
                c1_candidate = min(conductores, key=lambda item: abs(item[1].coordenadas[0]))

        if c1_candidate:
            name_c1, nodo_c1 = c1_candidate
            x_a, y_a, z_a = nodo_c1.coordenadas

            # (NO dibujar s_reposo para el primer conductor en la vista GENERAL)

            # Tormenta (usar theta_tormenta) - declinación invertida
            if theta_tormenta > 0:
                x_tor = x_a - Lk * math.sin(math.radians(theta_tormenta))
                z_tor = z_a - Lk * math.cos(math.radians(theta_tormenta))
                # Area circle
                fig.add_trace(self._crear_circulo(x_tor, z_tor, s_tormenta, 'orange', 0.12, f'GENERAL_{name_c1}_tormenta_s', False))
                # Chain line from amarre to tormenta position
                fig.add_trace(go.Scatter(
                    x=[x_a, x_tor], y=[z_a, z_tor], mode='lines', line=dict(color='gray', width=2),
                    name=f'GENERAL_{name_c1}_tormenta_cadena', showlegend=False, hoverinfo='skip', visible=False
                ))
                # Conductor/point at tormenta
                fig.add_trace(go.Scatter(
                    x=[x_tor], y=[z_tor], mode='markers', marker=dict(size=7, color='orange'),
                    name=f'GENERAL_{name_c1}_tormenta_punto', showlegend=False, hoverinfo='skip', visible=False
                ))
                # Label placed to the right of the area (aligned outside)
                fig.add_trace(go.Scatter(
                    x=[x_tor + s_tormenta + 0.05], y=[z_tor],
                    mode='text', text=[f's_tormenta<br>{s_tormenta:.2f}m<br>θ={theta_tormenta:.1f}°'], textfont=dict(size=9, color='blue'),
                    textposition='middle left',
                    name=f'GENERAL_{name_c1}_tormenta_label', showlegend=False, hoverinfo='skip', visible=False
                ))

            # Decmax (theta_max) - declinación invertida
            if theta_max > 0:
                x_dec = x_a - Lk * math.sin(math.radians(theta_max))
                z_dec = z_a - Lk * math.cos(math.radians(theta_max))
                # Area circle
                fig.add_trace(self._crear_circulo(x_dec, z_dec, s_decmax, 'red', 0.12, f'GENERAL_{name_c1}_decmax_s', False))
                # Chain line from amarre to decmax position
                fig.add_trace(go.Scatter(
                    x=[x_a, x_dec], y=[z_a, z_dec], mode='lines', line=dict(color='gray', width=2),
                    name=f'GENERAL_{name_c1}_decmax_cadena', showlegend=False, hoverinfo='skip', visible=False
                ))
                # Conductor/point at decmax
                fig.add_trace(go.Scatter(
                    x=[x_dec], y=[z_dec], mode='markers', marker=dict(size=7, color='red'),
                    name=f'GENERAL_{name_c1}_decmax_punto', showlegend=False, hoverinfo='skip', visible=False
                ))
                # Label centered below the area
                fig.add_trace(go.Scatter(
                    x=[x_dec], y=[z_dec - s_decmax - 0.05],
                    mode='text', text=[f's_decmax<br>{s_decmax:.2f}m<br>θ={theta_max:.1f}°'], textfont=dict(size=9, color='blue'),
                    textposition='middle center',
                    name=f'GENERAL_{name_c1}_decmax_label', showlegend=False, hoverinfo='skip', visible=False
                ))

        # --- Segundo nivel conductor (C2 / C2_R / C3) si existe ---
        c2_candidate = None
        for pref in ('c2_r', 'c2', 'c3'):
            for n, nodo in conductores:
                if n.lower().startswith(pref):
                    c2_candidate = (n, nodo)
                    break
            if c2_candidate:
                break

        if c2_candidate:
            name_c2, nodo_c2 = c2_candidate
            x2, y2, z2 = nodo_c2.coordenadas
            x_repo2, z_repo2 = x2, z2 - Lk
            # Reposo area for second level (drawn as part of GENERAL, hidden by default); add chain and conductor point
            fig.add_trace(self._crear_circulo(x_repo2, z_repo2, s_reposo, 'blue', 0.12, f'GENERAL_{name_c2}_reposo_s', False))
            fig.add_trace(go.Scatter(
                x=[x2, x_repo2], y=[z2, z_repo2], mode='lines', line=dict(color='gray', width=2),
                name=f'GENERAL_{name_c2}_reposo_cadena', showlegend=False, hoverinfo='skip', visible=False
            ))
            fig.add_trace(go.Scatter(
                x=[x_repo2], y=[z_repo2], mode='markers', marker=dict(size=7, color='red'),
                name=f'GENERAL_{name_c2}_reposo_punto', showlegend=False, hoverinfo='skip', visible=False
            ))
            fig.add_trace(go.Scatter(
                x=[x_repo2], y=[z_repo2 + s_reposo + s_reposo * 0.05],
                mode='text', text=[f's_reposo<br>{s_reposo:.2f}m'], textfont=dict(size=9, color='blue'),
                name=f'GENERAL_{name_c2}_reposo_label', showlegend=False, hoverinfo='skip', visible=False
            ))
        # --- Tercer nivel conductor (C3 / C3_R) si existe ---
        c3_candidate = None
        for pref in ('C3_R', 'C3'):
            for n, nodo in conductores:
                if n.startswith(pref):
                    c3_candidate = (n, nodo)
                    break
            if c3_candidate:
                break

        if c3_candidate:
            name_c3, nodo_c3 = c3_candidate
            x3, y3, z3 = nodo_c3.coordenadas
            x_repo3, z_repo3 = x3, z3 - Lk
            fig.add_trace(self._crear_circulo(x_repo3, z_repo3, s_reposo, 'blue', 0.12, f'GENERAL_{name_c3}_reposo_s', False))
            fig.add_trace(go.Scatter(
                x=[x3, x_repo3], y=[z3, z_repo3], mode='lines', line=dict(color='gray', width=2),
                name=f'GENERAL_{name_c3}_reposo_cadena', showlegend=False, hoverinfo='skip', visible=False
            ))
            fig.add_trace(go.Scatter(
                x=[x_repo3], y=[z_repo3], mode='markers', marker=dict(size=7, color='red'),
                name=f'GENERAL_{name_c3}_reposo_punto', showlegend=False, hoverinfo='skip', visible=False
            ))
            fig.add_trace(go.Scatter(
                x=[x_repo3], y=[z_repo3 + s_reposo + s_reposo * 0.05],
                mode='text', text=[f's_reposo<br>{s_reposo:.2f}m'], textfont=dict(size=9, color='blue'),
                name=f'GENERAL_{name_c3}_reposo_label', showlegend=False, hoverinfo='skip', visible=False
            ))

        # --- Etiqueta Apantallamiento (top-right del área) ---
        if self.geo.cant_hg > 0 and ang_apant is not None and ang_apant > 0 and conductores:
            # Tomar primera HG disponible (case-insensitive)
            hg_nodes = [(n, nodo) for n, nodo in self.geo.nodos.items() if n.upper().startswith('HG')]
            if hg_nodes:
                nombre_hg, nodo_hg = hg_nodes[0]
                xg, yg, zg = nodo_hg.coordenadas
                # Altura mínima de conductores (considerando Lk)
                z_min = min(nodo.coordenadas[2] - Lk for _, nodo in conductores)
                altura_cono = zg - z_min
                extension = altura_cono * math.tan(math.radians(ang_apant))

                # Posicionar etiqueta a la derecha si HG está en x positiva, sino a la izquierda
                sign = 1 if xg >= 0 else -1
                x_label = xg + sign * extension * 0.8
                y_label = zg + abs(extension) * 0.05

                fig.add_trace(go.Scatter(
                    x=[x_label], y=[y_label], mode='text',
                    text=[f'Apantallamiento<br>({ang_apant:.0f}°)'],
                    textfont=dict(size=9, color='green'),
                    name='GENERAL_apantallamiento_label', showlegend=False, hoverinfo='skip'
                ))

        # --- fin _dibujar_vista_general ---

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

        # Asegurar que Dhg (círculo en nodos HG) quede incluido: extender z_max si es necesario
        Dhg = self.geo.dimensiones.get('Dhg', 0)
        hg_nodes = [nodo for n, nodo in self.geo.nodos.items() if n.startswith('HG')]
        if hg_nodes and Dhg > 0:
            z_max_hg = max((nodo.coordenadas[2] + Dhg) for nodo in hg_nodes)
            z_max = max(z_max, z_max_hg)
            extra = max(0.2, Dhg * 0.1)
            z_max = z_max + extra

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
