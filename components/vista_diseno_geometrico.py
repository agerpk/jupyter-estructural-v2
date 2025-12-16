"""Vista para diseño geométrico de estructura"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from config.app_config import DATA_DIR
from utils.view_helpers import ViewHelpers
from utils.calculo_cache import CalculoCache


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
        
        # Nodos
        nodos_base = {k: v for k, v in nodes_key.items() if k == 'BASE'}
        nodos_cross = {k: v for k, v in nodes_key.items() if k.startswith('CROSS')}
        nodos_cond = {k: v for k, v in nodes_key.items() if k.startswith('C')}
        nodos_guard = {k: v for k, v in nodes_key.items() if k.startswith('HG')}
        nodos_gen = {k: v for k, v in nodes_key.items() if k in ['MEDIO', 'TOP', 'V']}
        
        nodos_txt = "BASE:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_base.items()])
        if nodos_cross:
            nodos_txt += "\n\nCRUCE:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_cross.items()])
        if nodos_cond:
            nodos_txt += "\n\nCONDUCTOR:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_cond.items()])
        if nodos_guard:
            nodos_txt += "\n\nGUARDIA:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_guard.items()])
        if nodos_gen:
            nodos_txt += "\n\nGENERAL:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_gen.items()])
        
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
    resultados_previos = None
    if calculo_guardado:
        resultados_previos = generar_resultados_dge(calculo_guardado, estructura_actual)
    
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
                    ], md=6),
                    dbc.Col([
                        dbc.Button("Calcular Diseño Geométrico", id="btn-calcular-geom", color="success", size="lg", className="w-100"),
                    ], md=6),
                ], className="mb-4"),
                
                html.Hr(),
                
                # Área de resultados
                html.Div(id="output-diseno-geometrico", children=resultados_previos)
            ])
        ])
    ])
