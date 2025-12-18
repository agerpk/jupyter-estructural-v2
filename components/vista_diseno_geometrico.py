"""Vista para diseño geométrico de estructura"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from config.app_config import DATA_DIR
from utils.view_helpers import ViewHelpers
from utils.calculo_cache import CalculoCache


def generar_tabla_editor_nodos(nodos_dict, cables_disponibles, nodos_objetos=None):
    """Genera tabla editable de nodos para el modal"""
    # Convertir nodos a lista de diccionarios
    nodos_data = []
    for nombre, coords in nodos_dict.items():
        # Obtener datos del objeto nodo si existe
        tipo_nodo = "general"
        cable_id = ""
        rotacion = 0.0
        angulo_quiebre = 0.0
        tipo_fijacion = "suspensión"
        conectado_a = ""
        
        if nodos_objetos and nombre in nodos_objetos:
            nodo_obj = nodos_objetos[nombre]
            tipo_nodo = getattr(nodo_obj, 'tipo', 'general')
            if hasattr(nodo_obj, 'cable') and nodo_obj.cable:
                cable_id = nodo_obj.cable.nombre if hasattr(nodo_obj.cable, 'nombre') else ""
            rotacion = getattr(nodo_obj, 'rotacion_eje_z', 0.0)
            angulo_quiebre = getattr(nodo_obj, 'angulo_quiebre', 0.0)
            tipo_fijacion = getattr(nodo_obj, 'tipo_fijacion', 'suspensión') or 'suspensión'
            conectado_a_list = getattr(nodo_obj, 'conectado_a', [])
            if conectado_a_list:
                conectado_a = ", ".join(conectado_a_list)
        
        # Obtener rotaciones X e Y si existen
        rotacion_x = getattr(nodo_obj, 'rotacion_eje_x', 0.0) if nodos_objetos and nombre in nodos_objetos else 0.0
        rotacion_y = getattr(nodo_obj, 'rotacion_eje_y', 0.0) if nodos_objetos and nombre in nodos_objetos else 0.0
        
        nodos_data.append({
            "nombre": nombre,
            "tipo": tipo_nodo,
            "x": coords[0],
            "y": coords[1],
            "z": coords[2],
            "cable_id": cable_id,
            "rotacion_eje_x": rotacion_x,
            "rotacion_eje_y": rotacion_y,
            "rotacion_eje_z": rotacion,
            "angulo_quiebre": angulo_quiebre,
            "tipo_fijacion": tipo_fijacion,
            "conectado_a": conectado_a,
            "editar_conexiones": "✏️ Editar"
        })
    
    # Opciones para dropdowns
    tipos_nodo = ["conductor", "guardia", "base", "cruce", "general", "viento"]
    tipos_fijacion = ["suspensión", "retención", "none"]
    
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
                {"name": "Cable", "id": "cable_id", "editable": True, "presentation": "dropdown"},
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
                "cable_id": {"options": [{"label": c, "value": c} for c in cables_disponibles]},
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


def generar_resultados_dge(calculo_guardado, estructura_actual):
    """Generar HTML de resultados desde cálculo guardado"""
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
            f"Autoajustar lmenhg: {'ACTIVADO' if estructura_actual.get('AUTOAJUSTAR_LMENHG') else 'DESACTIVADO'}"
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
        
        # Distancias
        dist_txt = (
            f"D_fases: {D_fases:.3f} m\n" +
            f"Dhg: {Dhg:.3f} m\n" +
            f"s_estructura: {s_estructura:.3f} m\n" +
            f"a: {a:.3f} m\n" +
            f"b: {b:.3f} m\n" +
            f"Altura base eléctrica: {altura_base_electrica:.3f} m"
        )
        
        # Verificar vigencia
        vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        
        output = [
            ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=vigente),
            dbc.Alert("GEOMETRIA COMPLETADA: {} nodos creados".format(len(nodes_key)), color="success", className="mb-3")
        ]
        
        output.extend(ViewHelpers.crear_pre_output(params_txt, "PARAMETROS DE DISEÑO"))
        output.extend(ViewHelpers.crear_pre_output(dims_txt, "DIMENSIONES DE ESTRUCTURA"))
        output.extend(ViewHelpers.crear_pre_output(nodos_txt, f"NODOS ESTRUCTURALES ({len(nodes_key)} nodos)", max_height='400px'))
        output.extend(ViewHelpers.crear_pre_output(param_dim_txt, "PARAMETROS DIMENSIONANTES"))
        output.extend(ViewHelpers.crear_pre_output(dist_txt, "DISTANCIAS"))
        
        # Cargar imágenes
        if hash_params:
            img_str_estructura = ViewHelpers.cargar_imagen_base64(f"Estructura.{hash_params}.png")
            if img_str_estructura:
                output.extend([
                    html.H5("GRAFICO DE ESTRUCTURA", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str_estructura}', style={'width': '100%', 'maxWidth': '800px'})
                ])
            
            img_str_cabezal = ViewHelpers.cargar_imagen_base64(f"Cabezal.{hash_params}.png")
            if img_str_cabezal:
                output.extend([
                    html.H5("GRAFICO DE CABEZAL", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str_cabezal}', style={'width': '100%', 'maxWidth': '800px'})
                ])
            
            img_str_nodos = ViewHelpers.cargar_imagen_base64(f"Nodos.{hash_params}.png")
            if img_str_nodos:
                output.extend([
                    html.H5("GRAFICO DE NODOS Y COORDENADAS", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str_nodos}', style={'width': '100%', 'maxWidth': '800px'})
                ])
        
        # Agregar memoria de cálculo
        memoria_calculo = calculo_guardado.get('memoria_calculo')
        if memoria_calculo:
            output.append(html.Hr(className="mt-5"))
            output.append(dbc.Card([
                dbc.CardHeader(html.H5("Memoria de Cálculo: Diseño Geométrico de Estructura", className="mb-0")),
                dbc.CardBody(ViewHelpers.crear_pre_output(memoria_calculo, max_height='600px', font_size='0.85rem'))
            ], className="mt-3"))
        
        print(f"DEBUG: Retornando Div con {len(output)} elementos")
        return html.Div(output)
    except Exception as e:
        return dbc.Alert(f"Error cargando resultados: {str(e)}", color="warning")


def crear_vista_diseno_geometrico(estructura_actual, calculo_guardado=None):
    """Vista para diseño geométrico con parámetros y cálculo"""
    
    # Generar resultados si hay cálculo guardado
    resultados_previos = []
    if calculo_guardado:
        resultados_previos = generar_resultados_dge(calculo_guardado, estructura_actual)
    else:
        resultados_previos = []
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Diseño Geométrico de Estructura", className="mb-0")),
            dbc.CardBody([
                # Parámetros de diseño
                html.H5("Parámetros de Diseño de Cabezal", className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("TENSION (kV)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-tension-geom", min=0, max=1000, step=1, value=estructura_actual.get("TENSION", 220),
                                   marks={0: "0", 13.2: "13.2", 33: "33", 66: "66", 132: "132", 220: "220", 330: "330", 500: "500", 600: "600", 700: "700", 800: "800", 900: "900", 1000: "1000"},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Zona Estructura", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-zona-estructura", value=estructura_actual.get("Zona_estructura", "Rural"),
                                   options=[{"label": "Peatonal", "value": "Peatonal"}, {"label": "Rural", "value": "Rural"},
                                           {"label": "Urbana", "value": "Urbana"}, {"label": "Autopista", "value": "Autopista"},
                                           {"label": "Ferrocarril", "value": "Ferrocarril"}, {"label": "Línea Eléctrica", "value": "Línea Eléctrica"}]),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Lk (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-lk-geom", min=0, max=8, step=0.5, value=estructura_actual.get("Lk", 2.5),
                                   marks={i: str(i) for i in range(0, 9)},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Ángulo Apantallamiento (°)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-ang-apantallamiento", min=0, max=45, step=1, value=estructura_actual.get("ANG_APANTALLAMIENTO", 30.0),
                                   marks={i: str(i) for i in range(0, 46, 15)},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("TERNA", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-terna-geom", value=estructura_actual.get("TERNA", "Simple"),
                                   options=[{"label": "Simple", "value": "Simple"}, {"label": "Doble", "value": "Doble"}]),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("DISPOSICION", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-disposicion-geom", value=estructura_actual.get("DISPOSICION", "triangular"),
                                   options=[{"label": "Triangular", "value": "triangular"}, {"label": "Horizontal", "value": "horizontal"},
                                           {"label": "Vertical", "value": "vertical"}]),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("CANT_HG", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-cant-hg-geom", min=0, max=2, step=1, value=estructura_actual.get("CANT_HG", 2),
                                   marks={0: "0", 1: "1", 2: "2"},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=4),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Altura Mínima Cable (m)", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-altura-min-cable", type="number", step=0.1, value=estructura_actual.get("ALTURA_MINIMA_CABLE", 6.5)),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Long. Ménsula Mín. Conductor (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-lmen-min-cond", min=0, max=5, step=0.5, value=estructura_actual.get("LONGITUD_MENSULA_MINIMA_CONDUCTOR", 1.3),
                                   marks={i: str(i) for i in range(0, 6)},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Long. Ménsula Mín. Guardia (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-lmen-min-guard", min=0, max=5, step=0.5, value=estructura_actual.get("LONGITUD_MENSULA_MINIMA_GUARDIA", 0.2),
                                   marks={i: str(i) for i in range(0, 6)},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("HADD (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-hadd-geom", min=0, max=4, step=1, value=estructura_actual.get("HADD", 0.4),
                                   marks={i: str(i) for i in range(0, 5)},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("HADD Entre Amarres (m)", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-hadd-entre-amarres", type="number", step=0.1, value=estructura_actual.get("HADD_ENTRE_AMARRES", 0.2)),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("HADD_HG (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-hadd-hg-geom", min=0, max=2, step=0.5, value=estructura_actual.get("HADD_HG", 1.5),
                                   marks={i: str(i) for i in [0, 0.5, 1.0, 1.5, 2.0]},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("HADD_LMEN (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-hadd-lmen-geom", min=0, max=2, step=0.2, value=estructura_actual.get("HADD_LMEN", 0.5),
                                   marks={i: str(round(i, 1)) for i in [0, 0.5, 1.0, 1.5, 2.0]},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=4),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Ancho Cruceta (m)", style={"fontSize": "1.125rem"}),
                        dcc.Slider(id="slider-ancho-cruceta-geom", min=0, max=0.5, step=0.1, value=estructura_actual.get("ANCHO_CRUCETA", 0.3),
                                   marks={i/10: str(i/10) for i in range(0, 6)},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Dist. Reposicionar HG (m)", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-dist-repos-hg", type="number", step=0.05, value=estructura_actual.get("DIST_REPOSICIONAR_HG", 0.1)),
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
                        dbc.Alert("Edite los nodos existentes o agregue nuevos. Los cambios se aplicarán al recalcular DGE.", color="info", className="mb-3"),
                        dbc.Button("+ Agregar Nodo", id="btn-agregar-nodo-tabla", color="success", size="sm", className="mb-2"),
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
