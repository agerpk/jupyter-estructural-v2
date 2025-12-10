"""Vista para diseño geométrico de estructura"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def crear_vista_diseno_geometrico(estructura_actual):
    """Vista para diseño geométrico con parámetros y cálculo"""
    
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
                html.Div(id="output-diseno-geometrico")
            ])
        ])
    ])
