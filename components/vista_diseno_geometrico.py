"""Vista para diseño geométrico de estructura"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from config.app_config import DATA_DIR
from config.parametros_controles import obtener_config_control
from utils.view_helpers import ViewHelpers
from utils.calculo_cache import CalculoCache


def generar_tabla_editor_nodos(nodos_data, cables_disponibles):
    """Genera tabla editable de nodos para el modal
    
    Args:
        nodos_data: Lista de diccionarios con datos completos de nodos
        cables_disponibles: Lista de IDs de cables disponibles
    """
    print(f"🔧 DEBUG generar_tabla_editor_nodos: cables_disponibles = {cables_disponibles}")
    print(f"🔧 DEBUG generar_tabla_editor_nodos: nodos_data count = {len(nodos_data)}")
    
    # Verificar que nodos_data tenga cable_id
    for nodo in nodos_data[:3]:  # Solo primeros 3 para debug
        print(f"   Nodo {nodo.get('nombre')}: cable_id = '{nodo.get('cable_id', 'NO_EXISTE')}'")
    
    # Asegurar que todos los nodos tengan el campo cable_id
    # Si está vacío, asignar cable según el nombre del nodo
    cable_conductor = cables_disponibles[0] if len(cables_disponibles) > 0 else ""
    cable_guardia = cables_disponibles[1] if len(cables_disponibles) > 1 else cables_disponibles[0] if len(cables_disponibles) > 0 else ""
    
    for nodo in nodos_data:
        if 'cable_id' not in nodo or not nodo['cable_id']:
            nombre = nodo.get('nombre', '')
            # Asignar cable según el nombre del nodo
            if nombre.startswith('HG'):
                nodo['cable_id'] = cable_guardia
            elif nombre.startswith('C') and not nombre.startswith('CROSS'):
                nodo['cable_id'] = cable_conductor
            else:
                nodo['cable_id'] = ""
    
    # Opciones para dropdowns
    tipos_nodo = ["conductor", "guardia", "base", "cruce", "general", "viento"]
    tipos_fijacion = ["suspensión", "retención", "none"]
    
    # Debug: verificar opciones de dropdown
    opciones_cable = [{"label": "(Sin cable)", "value": ""}] + [{"label": c, "value": c} for c in cables_disponibles if c]
    print(f"🔽 DEBUG: Opciones dropdown cable_id: {opciones_cable}")
    
    return html.Div([
        dash_table.DataTable(
            id="datatable-nodos",
            data=nodos_data,
            columns=[
                {"name": "Nombre", "id": "nombre", "editable": True},
                {"name": "Tipo", "id": "tipo", "editable": True, "presentation": "dropdown"},
                {"name": "X (m)", "id": "x", "type": "numeric", "editable": True, "format": {"specifier": ".3f"}},
                {"name": "Y (m)", "id": "y", "type": "numeric", "editable": True, "format": {"specifier": ".3f"}},
                {"name": "Z (m)", "id": "z", "type": "numeric", "editable": True, "format": {"specifier": ".3f"}},
                {"name": "Cable", "id": "cable_id", "editable": True},
                {"name": "Rot. X (°)", "id": "rotacion_eje_x", "type": "numeric", "editable": True, "format": {"specifier": ".1f"}},
                {"name": "Rot. Y (°)", "id": "rotacion_eje_y", "type": "numeric", "editable": True, "format": {"specifier": ".1f"}},
                {"name": "Rot. Z (°)", "id": "rotacion_eje_z", "type": "numeric", "editable": True, "format": {"specifier": ".1f"}},
                {"name": "Áng. Quiebre (°)", "id": "angulo_quiebre", "type": "numeric", "editable": True, "format": {"specifier": ".1f"}},
                {"name": "Fijación", "id": "tipo_fijacion", "editable": True, "presentation": "dropdown"},
                {"name": "Conectado A", "id": "conectado_a", "editable": False},
                {"name": "Editar", "id": "editar_conexiones", "editable": False},
            ],
            dropdown={
                "tipo": {"options": [{"label": t, "value": t} for t in tipos_nodo]},
                "tipo_fijacion": {"options": [{"label": t, "value": t} for t in tipos_fijacion]},
            },
            editable=True,
            row_deletable=True,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "fontSize": "0.9rem",
                "backgroundColor": "#ffffff",
                "color": "#212529"
            },
            style_header={
                "backgroundColor": "#0d6efd",
                "color": "white",
                "fontWeight": "bold",
                "textAlign": "center"
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
                {"if": {"state": "selected"}, "backgroundColor": "#cfe2ff", "border": "1px solid #0d6efd"},
                {"if": {"column_id": "editar_conexiones"}, "cursor": "pointer", "color": "#0d6efd", "fontWeight": "bold"}
            ],
        )
    ])


def generar_resultados_dge(calculo_guardado, estructura_actual, mostrar_alerta_cache=False):
    """Generar HTML de resultados desde cálculo guardado - retorna html.Div"""
    try:
        dims = calculo_guardado.get('dimensiones', {})
        nodes_key = calculo_guardado.get('nodes_key', {})
        hash_params = calculo_guardado.get('hash_parametros')
        
        # Extraer valores
        altura_total = dims.get('altura_total', 0)
        h1a = dims.get('h1a', 0)
        h2a = dims.get('h2a', 0)
        lmen = dims.get('lmen', 0)
        lmenhg = dims.get('lmenhg', 0)
        hhg = dims.get('hhg', 0)
        theta_max = dims.get('theta_max', 0)
        k = dims.get('k', 0)
        Ka = dims.get('Ka', 1)
        D_fases = dims.get('D_fases', 0)
        Dhg = dims.get('Dhg', 0)
        s_estructura = dims.get('s_estructura', 0)
        a = dims.get('a', dims.get('altura_libre', 0))
        b = dims.get('b', 0)
        altura_base_electrica = dims.get('altura_base_electrica', dims.get('h_base_electrica', dims.get('altura_libre', 0)))
        
        # Parámetros de diseño
        params_txt = (
            f"Tipo estructura: {estructura_actual.get('TIPO_ESTRUCTURA')}\n" +
            f"Tensión nominal: {estructura_actual.get('TENSION')} kV\n" +
            f"Zona: {estructura_actual.get('Zona_estructura')}\n" +
            f"Disposición: {estructura_actual.get('DISPOSICION')}\n" +
            f"Terna: {estructura_actual.get('TERNA')}\n" +
            f"Cantidad HG: {estructura_actual.get('CANT_HG')}\n" +
            f"Vano: {estructura_actual.get('L_vano')} m\n" +
            f"Autoajustar lmenhg: {'ACTIVADO' if estructura_actual.get('AUTOAJUSTAR_LMENHG') else 'DESACTIVADO'}\n" +
            f"Defasaje por hielo: {'Sí' if estructura_actual.get('defasaje_mensula_hielo', False) else 'No'}\n" +
            (f"  Ménsula defasada: {estructura_actual.get('mensula_defasar', 'N/A')} ({estructura_actual.get('lmen_extra_hielo', 0.0):+.3f}m)\n" if estructura_actual.get('defasaje_mensula_hielo', False) else "")
        )
        
        # Dimensiones
        dims_txt = (
            f"Altura total: {altura_total:.2f} m\n" +
            f"Alturas: h1a={h1a:.2f}m, h2a={h2a:.2f}m\n" +
            f"Ménsulas: lmen={lmen:.2f}m, lmenhg={lmenhg:.2f}m\n" +
            f"Cable guardia: hhg={hhg:.2f}m"
        )
        
        # Nodos por tipo (usando nodos_editados para obtener el tipo)
        nodos_editados_dict = {n['nombre']: n for n in calculo_guardado.get('nodos_editados', [])}
        
        nodos_base = {}
        nodos_cross = {}
        nodos_cond = {}
        nodos_guard = {}
        nodos_gen = {}
        nodos_viento = {}
        
        for nombre_nodo, coords in nodes_key.items():
            # Obtener tipo del nodo editado si existe
            if nombre_nodo in nodos_editados_dict:
                tipo = nodos_editados_dict[nombre_nodo].get('tipo', 'general')
            else:
                # Inferir tipo por nombre
                if nombre_nodo == 'BASE':
                    tipo = 'base'
                elif nombre_nodo.startswith('CROSS'):
                    tipo = 'cruce'
                elif nombre_nodo.startswith('C') and not nombre_nodo.startswith('CROSS'):
                    tipo = 'conductor'
                elif nombre_nodo.startswith('HG'):
                    tipo = 'guardia'
                elif nombre_nodo == 'V':
                    tipo = 'viento'
                else:
                    tipo = 'general'
            
            # Clasificar por tipo
            if tipo == 'base':
                nodos_base[nombre_nodo] = coords
            elif tipo == 'cruce':
                nodos_cross[nombre_nodo] = coords
            elif tipo == 'conductor':
                nodos_cond[nombre_nodo] = coords
            elif tipo == 'guardia':
                nodos_guard[nombre_nodo] = coords
            elif tipo == 'viento':
                nodos_viento[nombre_nodo] = coords
            else:
                nodos_gen[nombre_nodo] = coords
        
        nodos_txt = "BASE:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_base.items()])
        if nodos_cross:
            nodos_txt += "\n\nCRUCE:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_cross.items()])
        if nodos_cond:
            nodos_txt += "\n\nCONDUCTOR:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_cond.items()])
        if nodos_guard:
            nodos_txt += "\n\nGUARDIA:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_guard.items()])
        if nodos_gen:
            nodos_txt += "\n\nGENERAL:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_gen.items()])
        if nodos_viento:
            nodos_txt += "\n\nVIENTO:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_viento.items()])
        
        # Parámetros dimensionantes
        param_dim_txt = (
            f"theta_max: {theta_max:.2f}°\n" +
            f"Lk: {estructura_actual.get('Lk', 0):.2f} m\n" +
            f"Coeficiente k: {k:.3f}\n" +
            f"Coeficiente Ka (altura): {Ka:.3f}"
        )
        
        # Distancias - Verificar si hay sobreescritura
        sobreescribir_s = estructura_actual.get('SOBREESCRIBIR_S', False)
        s_reposo = dims.get('s_reposo', s_estructura)
        s_tormenta = dims.get('s_tormenta', s_estructura)
        s_decmax = dims.get('s_decmax', s_estructura)
        
        if sobreescribir_s:
            dist_txt = (
                f"D_fases: {D_fases:.3f} m\n" +
                f"Dhg: {Dhg:.3f} m\n" +
                f"s_reposo: {s_reposo:.3f} m (sobreescrito)\n" +
                f"s_tormenta: {s_tormenta:.3f} m (sobreescrito)\n" +
                f"s_decmax: {s_decmax:.3f} m (sobreescrito)\n" +
                f"a: {a:.3f} m\n" +
                f"b: {b:.3f} m\n" +
                f"Altura base eléctrica: {altura_base_electrica:.3f} m"
            )
        else:
            dist_txt = (
                f"D_fases: {D_fases:.3f} m\n" +
                f"Dhg: {Dhg:.3f} m\n" +
                f"s_reposo: {s_reposo:.3f} m\n" +
                f"s_tormenta: {s_tormenta:.3f} m\n" +
                f"s_decmax: {s_decmax:.3f} m\n" +
                f"a: {a:.3f} m\n" +
                f"b: {b:.3f} m\n" +
                f"Altura base eléctrica: {altura_base_electrica:.3f} m"
            )
        
        # Verificar vigencia
        vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        
        output = []
        if mostrar_alerta_cache:
            alerta = ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=vigente)
            if alerta:
                output.append(alerta)
        
        output.append(dbc.Alert("GEOMETRIA COMPLETADA: {} nodos creados".format(len(nodes_key)), color="success", className="mb-3"))
        
        output.append(html.H5("PARAMETROS DE DISEÑO", className="mb-2"))
        output.append(html.Pre(params_txt, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.85rem', 'maxHeight': '300px', 'overflowY': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'monospace'}))
        
        output.append(html.H5("DIMENSIONES DE ESTRUCTURA", className="mb-2"))
        output.append(html.Pre(dims_txt, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.85rem', 'maxHeight': '300px', 'overflowY': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'monospace'}))
        
        output.append(html.H5(f"NODOS ESTRUCTURALES ({len(nodes_key)} nodos)", className="mb-2"))
        output.append(html.Pre(nodos_txt, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.85rem', 'maxHeight': '400px', 'overflowY': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'monospace'}))
        
        output.append(html.H5("PARAMETROS DIMENSIONANTES", className="mb-2"))
        output.append(html.Pre(param_dim_txt, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.85rem', 'maxHeight': '300px', 'overflowY': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'monospace'}))
        
        output.append(html.H5("DISTANCIAS", className="mb-2"))
        output.append(html.Pre(dist_txt, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.85rem', 'maxHeight': '300px', 'overflowY': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'monospace'}))
        
        # Cargar gráficos Plotly interactivos
        if hash_params:
            fig_estructura_json = ViewHelpers.cargar_figura_plotly_json(f"Estructura.{hash_params}.json")
            if fig_estructura_json:
                output.append(html.H5("GRAFICO DE ESTRUCTURA", className="mb-2 mt-4"))
                output.append(dcc.Graph(figure=fig_estructura_json, config={'displayModeBar': True}, style={'height': '800px', 'width': '100%'}))
            
            fig_cabezal_json = ViewHelpers.cargar_figura_plotly_json(f"Cabezal.{hash_params}.json")
            if fig_cabezal_json:
                output.append(html.H5("GRAFICO DE CABEZAL", className="mb-2 mt-4"))
                output.append(dcc.Graph(figure=fig_cabezal_json, config={'displayModeBar': True}, style={'height': '800px', 'width': '100%'}))
            
            # Cargar gráfico 3D de nodos (Plotly JSON)
            try:
                fig_nodos_json = ViewHelpers.cargar_figura_plotly_json(f"Nodos.{hash_params}.json")
                if fig_nodos_json and isinstance(fig_nodos_json, dict):
                    output.append(html.H5("GRAFICO 3D DE NODOS Y COORDENADAS", className="mb-2 mt-4"))
                    output.append(dcc.Graph(figure=fig_nodos_json, config={'displayModeBar': True}, style={'height': '800px', 'width': '100%'}))
            except Exception as e:
                import traceback
                print(f"Error cargando gráfico 3D nodos: {traceback.format_exc()}")
        
        # Agregar memoria de cálculo
        memoria_calculo = calculo_guardado.get('memoria_calculo')
        if memoria_calculo:
            output.append(html.Hr(className="mt-5"))
            output.append(dbc.Card([
                dbc.CardHeader(html.H5("Memoria de Cálculo: Diseño Geométrico de Estructura", className="mb-0")),
                dbc.CardBody(html.Pre(
                    memoria_calculo,
                    style={
                        'backgroundColor': '#1e1e1e',
                        'color': '#d4d4d4',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'fontSize': '0.85rem',
                        'maxHeight': '600px',
                        'overflowY': 'auto',
                        'whiteSpace': 'pre-wrap',
                        'fontFamily': 'monospace'
                    }
                ))
            ], className="mt-3"))
        
        # Filtrar elementos None o inválidos y retornar lista directamente
        output_limpio = [elem for elem in output if elem is not None]
        print(f"DEBUG: Retornando lista con {len(output_limpio)} elementos válidos")
        return output_limpio
    except Exception as e:
        return dbc.Alert(f"Error cargando resultados: {str(e)}", color="warning")


def crear_vista_diseno_geometrico(estructura_actual, calculo_guardado=None):
    """Vista para diseño geométrico con parámetros y cálculo"""
    
    # Generar resultados si hay cálculo guardado
    resultados_previos = []
    if calculo_guardado:
        resultados_previos = generar_resultados_dge(calculo_guardado, estructura_actual)
        if not isinstance(resultados_previos, list):
            resultados_previos = [resultados_previos]
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Diseño Geométrico de Estructura", className="mb-0")),
            dbc.CardBody([
                # Parámetros de diseño
                html.H5("Parámetros de Diseño de Cabezal", className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("TENSION (kV)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-tension-geom", **{k: v for k, v in obtener_config_control("TENSION").items() if k != "tipo"}, value=estructura_actual.get("TENSION", 220), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Zona Estructura", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-zona-estructura", value=estructura_actual.get("Zona_estructura", "Rural"),
                                   options=[{"label": opt, "value": opt} for opt in obtener_config_control("Zona_estructura")["opciones"]]),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Lk (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-lk-geom", **{k: v for k, v in obtener_config_control("Lk").items() if k != "tipo"}, value=estructura_actual.get("Lk", 2.5), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Ángulo Apantallamiento (°)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-ang-apantallamiento", **{k: v for k, v in obtener_config_control("ANG_APANTALLAMIENTO").items() if k != "tipo"}, value=estructura_actual.get("ANG_APANTALLAMIENTO", 30.0), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("TERNA", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-terna-geom", value=estructura_actual.get("TERNA", "Simple"),
                                   options=[{"label": opt, "value": opt} for opt in obtener_config_control("TERNA")["opciones"]]),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("DISPOSICION", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-disposicion-geom", value=estructura_actual.get("DISPOSICION", "triangular"),
                                   options=[{"label": opt, "value": opt} for opt in obtener_config_control("DISPOSICION")["opciones"]]),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("CANT_HG", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-cant-hg-geom", **{k: v for k, v in obtener_config_control("CANT_HG").items() if k != "tipo"}, value=estructura_actual.get("CANT_HG", 2), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=4),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Altura Mínima Cable (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-altura-min-cable", **{k: v for k, v in obtener_config_control("ALTURA_MINIMA_CABLE").items() if k != "tipo"}, value=estructura_actual.get("ALTURA_MINIMA_CABLE", 6.5), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Long. Ménsula Mín. Conductor (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-lmen-min-cond", **{k: v for k, v in obtener_config_control("LONGITUD_MENSULA_MINIMA_CONDUCTOR").items() if k != "tipo"}, value=estructura_actual.get("LONGITUD_MENSULA_MINIMA_CONDUCTOR", 1.3), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Long. Ménsula Mín. Guardia (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-lmen-min-guard", **{k: v for k, v in obtener_config_control("LONGITUD_MENSULA_MINIMA_GUARDIA").items() if k != "tipo"}, value=estructura_actual.get("LONGITUD_MENSULA_MINIMA_GUARDIA", 0.2), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("HADD (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-hadd-geom", **{k: v for k, v in obtener_config_control("HADD").items() if k != "tipo"}, value=estructura_actual.get("HADD", 0.4), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("HADD Entre Amarres (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-hadd-entre-amarres", **{k: v for k, v in obtener_config_control("HADD_ENTRE_AMARRES").items() if k != "tipo"}, value=estructura_actual.get("HADD_ENTRE_AMARRES", 0.2), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("HADD_HG (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-hadd-hg-geom", **{k: v for k, v in obtener_config_control("HADD_HG").items() if k != "tipo"}, value=estructura_actual.get("HADD_HG", 1.5), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("HADD_LMEN (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-hadd-lmen-geom", **{k: v for k, v in obtener_config_control("HADD_LMEN").items() if k != "tipo"}, value=estructura_actual.get("HADD_LMEN", 0.5), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=4),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Ancho Cruceta (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-ancho-cruceta-geom", **{k: v for k, v in obtener_config_control("ANCHO_CRUCETA").items() if k != "tipo"}, value=estructura_actual.get("ANCHO_CRUCETA", 0.3), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Dist. Reposicionar HG (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-dist-repos-hg", **{k: v for k, v in obtener_config_control("DIST_REPOSICIONAR_HG").items() if k != "tipo"}, value=estructura_actual.get("DIST_REPOSICIONAR_HG", 0.1), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("HG Centrado", style={"fontSize": "1.125rem"}),
                        dbc.Switch(id="switch-hg-centrado", value=estructura_actual.get("HG_CENTRADO", False)),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Autoajustar LMENHG", style={"fontSize": "1.125rem"}),
                        dbc.Switch(id="switch-autoajustar-lmenhg", value=estructura_actual.get("AUTOAJUSTAR_LMENHG", True)),
                    ], md=6),
                ], className="mb-3"),
                
                # Controles de hielo
                html.H5("Parámetros de Hielo", className="mb-3 mt-4"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Defasaje Ménsula por Hielo", style={"fontSize": "1.125rem"}),
                        dbc.Switch(id="switch-defasaje-hielo", value=estructura_actual.get("defasaje_mensula_hielo", False)),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Longitud Extra Hielo (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-lmen-extra-hielo", **{k: v for k, v in obtener_config_control("lmen_extra_hielo").items() if k != "tipo"}, value=estructura_actual.get("lmen_extra_hielo", 0.0), tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Ménsula a Defasar", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-mensula-defasar", value=estructura_actual.get("mensula_defasar", "primera"),
                                   options=[{"label": opt, "value": opt} for opt in obtener_config_control("mensula_defasar")["opciones"]]),
                    ], md=4),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Guardar Parámetros", id="btn-guardar-params-geom", color="primary", size="lg", className="w-100"),
                    ], md=3),
                    dbc.Col([
                        dbc.Button("Calcular Diseño Geométrico", id="btn-calcular-geom", color="success", size="lg", className="w-100"),
                    ], md=3),
                    dbc.Col([
                        dbc.Button("Cargar desde Cache", id="btn-cargar-cache-dge", color="warning", size="lg", className="w-100"),
                    ], md=3),
                    dbc.Col([
                        dbc.Button("Editar Nodos", id="btn-editar-nodos-dge", color="info", size="lg", className="w-100"),
                    ], md=3),
                ], className="mb-4"),
                
                # Store para datos de nodos
                dcc.Store(id="store-nodos-editor", data=[]),
                
                # Modal de edición de nodos
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Editor de Nodos Estructurales"), close_button=True),
                    dbc.ModalBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("+ Agregar Nodo", id="btn-agregar-nodo-tabla", color="success", size="sm", className="w-100"),
                            ], md=3),
                            dbc.Col([
                                dbc.Button("Al/Ac 70/12", id="btn-asignar-conductor", color="primary", size="sm", className="w-100", title="Asignar cable conductor"),
                            ], md=3),
                            dbc.Col([
                                dbc.Button("OPGW FiberHome", id="btn-asignar-guardia", color="info", size="sm", className="w-100", title="Asignar cable guardia"),
                            ], md=3),
                            dbc.Col([
                                dbc.Button("Sin Cable", id="btn-quitar-cable", color="secondary", size="sm", className="w-100", title="Quitar cable"),
                            ], md=3),
                        ], className="mb-2"),
                        html.Div(id="tabla-nodos-editor"),
                    ], style={"maxHeight": "70vh", "overflowY": "auto"}),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="btn-cancelar-editor-nodos", color="secondary", className="me-2"),
                        dbc.Button("Guardar Cambios", id="btn-guardar-editor-nodos", color="primary"),
                    ]),
                ], id="modal-editor-nodos", size="xl", is_open=False, backdrop="static"),
                
                # Submodal para conexiones
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Editar Conexiones")),
                    dbc.ModalBody([
                        html.Div(id="checkboxes-conexiones-nodos"),
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="btn-cancelar-submodal-conexiones", color="secondary", className="me-2"),
                        dbc.Button("Aceptar", id="btn-aceptar-submodal-conexiones", color="primary"),
                    ]),
                ], id="submodal-conexiones", size="md", is_open=False),
                
                html.Hr(),
                
                # Área de resultados
                html.Div(id="output-diseno-geometrico", children=resultados_previos if resultados_previos else [])
            ])
        ])
    ])
