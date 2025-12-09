"""Vistas para gestión de cables"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def crear_vista_agregar_cable():
    """Vista para agregar un nuevo cable"""
    return crear_vista_agregar_cable_con_opciones([])


def crear_vista_agregar_cable_con_opciones(cables_disponibles):
    """Vista para agregar un nuevo cable con opciones de copiar"""
    opciones_cables = [{"label": c, "value": c} for c in cables_disponibles]
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Agregar Nuevo Cable", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Copiar Desde:", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-cable-copiar", options=opciones_cables, placeholder="Seleccione un cable..."),
                    ], md=10),
                    dbc.Col([
                        dbc.Button("Copiar", id="btn-copiar-cable", color="success", className="w-100 mt-4"),
                    ], md=2),
                ], className="mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Nombre del Cable *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-id", type="text", placeholder="Ej: AlAc 500/65", required=True),
                    ], md=12),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Tipo", style={"fontSize": "1.125rem"}),
                        dbc.RadioItems(
                            id="input-cable-tipo",
                            options=[
                                {"label": "ADSS", "value": "ADSS"},
                                {"label": "OPGW", "value": "OPGW"},
                                {"label": "ACSR", "value": "ACSR"},
                                {"label": "AAAC", "value": "AAAC"},
                                {"label": "ACERO", "value": "ACERO"},
                                {"label": "OTRO", "value": "OTRO"}
                            ],
                            value="OTRO",
                            inline=True
                        ),
                    ], md=12),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Material", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-material", type="text", placeholder="Ej: Al/Ac"),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Sección Nominal", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-seccion-nominal", type="text", placeholder="Ej: 435/55"),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Sección Total (mm²) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-seccion-total", type="number", step=0.01, required=True),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Diámetro Total (mm) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-diametro", type="number", step=0.1, required=True),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Peso Unitario (daN/m) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-peso", type="number", step=0.001, required=True),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Coef. Dilatación (1/°C) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-dilatacion", type="number", step=0.0000001, value=0.0000193, required=True),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Módulo Elasticidad (daN/mm²) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-modulo", type="number", step=1, required=True),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Carga Rotura Mínima (daN) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-rotura", type="number", step=0.1, required=True),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Tensión Rotura Mínima (MPa) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-tension-rotura", type="number", step=0.01, required=True),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Carga Máx. Trabajo (daN) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-carga-max", type="number", step=0.1, required=True),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Tensión Máx. Trabajo (MPa) *", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-tension-max", type="number", step=0.01, required=True),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Norma Fabricación", style={"fontSize": "1.125rem"}),
                        dbc.Input(id="input-cable-norma", type="text", placeholder="Ej: IRAM 2187"),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Guardar Cable", id="btn-guardar-cable", color="primary", size="lg", className="w-100"),
                    ], md=6),
                    dbc.Col([
                        dbc.Button("Volver", id={"type": "btn-volver", "index": "cables"}, color="secondary", size="lg", className="w-100"),
                    ], md=6),
                ])
            ])
        ])
    ])


def crear_vista_modificar_cable(cables_disponibles):
    """Vista para modificar un cable existente"""
    opciones_cables = [{"label": c, "value": c} for c in cables_disponibles]
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Modificar Cable", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Seleccionar Cable", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-cable-modificar", options=opciones_cables, placeholder="Seleccione un cable..."),
                    ], md=10),
                    dbc.Col([
                        dbc.Button("Volver", id={"type": "btn-volver", "index": "cables-mod"}, color="secondary", className="w-100 mt-4"),
                    ], md=2),
                ], className="mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Copiar Desde:", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-cable-copiar-mod", options=opciones_cables, placeholder="Seleccione un cable..."),
                    ], md=10),
                    dbc.Col([
                        dbc.Button("Copiar", id="btn-copiar-cable-mod", color="success", className="w-100 mt-4"),
                    ], md=2),
                ], className="mb-4"),
                
                html.Div(id="form-modificar-cable")
            ])
        ])
    ])


def crear_vista_eliminar_cable(cables_disponibles):
    """Vista para eliminar un cable"""
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Eliminar Cable", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Seleccionar Cable a Eliminar", style={"fontSize": "1.125rem"}),
                        dbc.Select(id="select-cable-eliminar", options=[
                            {"label": cable_id, "value": cable_id} for cable_id in cables_disponibles
                        ], placeholder="Seleccione un cable..."),
                    ], md=12),
                ], className="mb-3"),
                
                html.Div(id="info-cable-eliminar", className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Eliminar Cable", id="btn-eliminar-cable", color="danger", size="lg", className="w-100"),
                    ], md=6),
                    dbc.Col([
                        dbc.Button("Volver", id={"type": "btn-volver", "index": "cables-eliminar"}, color="secondary", size="lg", className="w-100"),
                    ], md=6),
                ])
            ])
        ])
    ])
