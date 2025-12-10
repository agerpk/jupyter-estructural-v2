"""Componente para editar hipótesis maestro"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def crear_editor_hipotesis_campo(codigo_hip, datos_hip):
    """Crea los campos de edición para una hipótesis específica"""
    
    # Valores por defecto
    viento = datos_hip.get('viento')
    tiro = datos_hip.get('tiro', {})
    peso = datos_hip.get('peso', {})
    sobrecarga = datos_hip.get('sobrecarga')
    
    return dbc.Card([
        dbc.CardHeader(html.H6(f"Hipótesis {codigo_hip}: {datos_hip.get('desc', '')}", className="mb-0")),
        dbc.CardBody([
            # Descripción
            dbc.Row([
                dbc.Col([
                    dbc.Label("Descripción"),
                    dbc.Input(
                        id={"type": "hip-desc", "index": codigo_hip},
                        value=datos_hip.get('desc', ''),
                        placeholder="Descripción de la hipótesis"
                    )
                ], md=12)
            ], className="mb-2"),
            
            # Viento
            dbc.Row([
                dbc.Col([
                    dbc.Label("Viento - Estado"),
                    dbc.Select(
                        id={"type": "hip-viento-estado", "index": codigo_hip},
                        value=viento.get('estado') if viento else None,
                        options=[
                            {"label": "Sin viento", "value": "None"},
                            {"label": "Vmax", "value": "Vmax"},
                            {"label": "Vmed", "value": "Vmed"}
                        ]
                    )
                ], md=4),
                dbc.Col([
                    dbc.Label("Viento - Dirección"),
                    dbc.Select(
                        id={"type": "hip-viento-dir", "index": codigo_hip},
                        value=viento.get('direccion') if viento else None,
                        options=[
                            {"label": "Transversal", "value": "Transversal"},
                            {"label": "Longitudinal", "value": "Longitudinal"},
                            {"label": "Oblicua", "value": "Oblicua"}
                        ],
                        disabled=not viento
                    )
                ], md=4),
                dbc.Col([
                    dbc.Label("Viento - Factor"),
                    dbc.Input(
                        id={"type": "hip-viento-factor", "index": codigo_hip},
                        type="number",
                        value=viento.get('factor', 1.0) if viento else 1.0,
                        step=0.1,
                        disabled=not viento
                    )
                ], md=4)
            ], className="mb-2"),
            
            # Tiro
            html.Hr(),
            html.H6("Tiro", className="mb-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Estado"),
                    dbc.Select(
                        id={"type": "hip-tiro-estado", "index": codigo_hip},
                        value=tiro.get('estado', 'TMA'),
                        options=[
                            {"label": "Tmin", "value": "Tmin"},
                            {"label": "TMA", "value": "TMA"},
                            {"label": "Vmax", "value": "Vmax"},
                            {"label": "Vmed", "value": "Vmed"},
                            {"label": "Tmax", "value": "Tmax"},
                            {"label": "máximo", "value": "máximo"}
                        ]
                    )
                ], md=6),
                dbc.Col([
                    dbc.Label("Patrón"),
                    dbc.Select(
                        id={"type": "hip-tiro-patron", "index": codigo_hip},
                        value=tiro.get('patron', 'bilateral'),
                        options=[
                            {"label": "Unilateral", "value": "unilateral"},
                            {"label": "Bilateral", "value": "bilateral"},
                            {"label": "Dos unilaterales", "value": "dos-unilaterales"},
                            {"label": "Doble terna a simple", "value": "doble-terna-a-simple"}
                        ]
                    )
                ], md=6)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Reducción Conductor"),
                    dcc.Slider(
                        id={"type": "hip-tiro-red-cond", "index": codigo_hip},
                        min=0, max=1, step=0.1,
                        value=tiro.get('reduccion_cond', 0.0),
                        marks={i/10: f"{i/10:.1f}" for i in range(0, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=6),
                dbc.Col([
                    dbc.Label("Reducción Guardia"),
                    dcc.Slider(
                        id={"type": "hip-tiro-red-guard", "index": codigo_hip},
                        min=0, max=1, step=0.1,
                        value=tiro.get('reduccion_guardia', 0.0),
                        marks={i/10: f"{i/10:.1f}" for i in range(0, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=6)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Factor Conductor"),
                    dcc.Slider(
                        id={"type": "hip-tiro-factor-cond", "index": codigo_hip},
                        min=0, max=2, step=0.1,
                        value=tiro.get('factor_cond', 1.0),
                        marks={i/10: f"{i/10:.1f}" for i in range(0, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=6),
                dbc.Col([
                    dbc.Label("Factor Guardia"),
                    dcc.Slider(
                        id={"type": "hip-tiro-factor-guard", "index": codigo_hip},
                        min=0, max=2, step=0.1,
                        value=tiro.get('factor_guardia', 1.0),
                        marks={i/10: f"{i/10:.1f}" for i in range(0, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=6)
            ], className="mb-2"),
            
            # Peso
            html.Hr(),
            html.H6("Peso", className="mb-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Factor"),
                    dcc.Slider(
                        id={"type": "hip-peso-factor", "index": codigo_hip},
                        min=0, max=3, step=0.1,
                        value=peso.get('factor', 1.0),
                        marks={i/2: f"{i/2:.1f}" for i in range(0, 7, 1)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=8),
                dbc.Col([
                    dbc.Label("Hielo"),
                    dbc.Switch(
                        id={"type": "hip-peso-hielo", "index": codigo_hip},
                        value=peso.get('hielo', False)
                    )
                ], md=4)
            ], className="mb-2"),
            
            # Sobrecarga
            html.Hr(),
            html.H6("Sobrecarga", className="mb-2"),
            dbc.Row([
                dbc.Col([
                    dcc.Slider(
                        id={"type": "hip-sobrecarga", "index": codigo_hip},
                        min=0, max=1000, step=10,
                        value=sobrecarga if sobrecarga else 0,
                        marks={0: "0", 220: "220", 300: "300", 500: "500", 1000: "1000"},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=12)
            ])
        ])
    ], className="mb-3")


def crear_modal_editor_hipotesis(tipo_estructura, hipotesis_maestro):
    """Crea el modal para editar hipótesis"""
    
    # Obtener hipótesis del tipo de estructura
    hipotesis_tipo = hipotesis_maestro.get(tipo_estructura, {})
    
    # Crear campos para cada hipótesis
    campos_hipotesis = [
        crear_editor_hipotesis_campo(codigo, datos)
        for codigo, datos in hipotesis_tipo.items()
    ]
    
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(f"Editar Hipótesis - {tipo_estructura}")),
        dbc.ModalBody([
            dbc.Alert(
                "Modifica los parámetros de las hipótesis. Los cambios se guardarán en el archivo específico de esta estructura.",
                color="info",
                className="mb-3"
            ),
            html.Div(campos_hipotesis, style={"maxHeight": "60vh", "overflowY": "auto"})
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-hipotesis", color="secondary", className="me-2"),
            dbc.Button("Guardar Hipótesis", id="btn-guardar-hipotesis", color="primary")
        ])
    ], id="modal-editor-hipotesis", size="xl", is_open=False, scrollable=True)
