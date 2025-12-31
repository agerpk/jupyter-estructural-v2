"""
Sistema de pestañas para alternar entre Modo Tabla y Modo Panel.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

def crear_pestanas_parametros() -> html.Div:
    """Crea pestañas para Modo Tabla y Modo Panel"""
    
    return html.Div([
        dbc.Tabs(
            id="pestanas-parametros",
            active_tab="tabla",
            children=[
                dbc.Tab(
                    label="Modo Tabla", 
                    tab_id="tabla",
                    label_style={"color": "#495057"},
                    active_label_style={"color": "#007bff", "font-weight": "bold"}
                ),
                dbc.Tab(
                    label="Modo Panel",
                    tab_id="panel",
                    label_style={"color": "#495057"},
                    active_label_style={"color": "#007bff", "font-weight": "bold"}
                )
            ],
            style={"margin-bottom": "20px"}
        ),
        
        # Contenedor para el contenido de cada pestaña
        html.Div(id="contenido-pestana-parametros")
    ])

def crear_botones_accion() -> html.Div:
    """Crea botones de acción comunes para ambos modos"""
    
    return dbc.Row([
        dbc.Col([
            dbc.Button(
                "Guardar Parámetros",
                id="guardar-parametros-tabla",
                color="primary",
                size="lg",
                className="w-100"
            )
        ], width=6),
        dbc.Col([
            dbc.Button(
                "Volver",
                id={"type": "btn-volver", "index": "ajuste-tabla"},
                color="secondary", 
                size="lg",
                className="w-100"
            )
        ], width=6)
    ], className="mt-4")

def crear_indicador_modo(modo_activo: str) -> html.Div:
    """Crea indicador visual del modo activo"""
    
    icono = "📋" if modo_activo == "tabla" else "🎛️"
    texto = "Modo Tabla" if modo_activo == "tabla" else "Modo Panel"
    color = "primary" if modo_activo == "tabla" else "secondary"
    
    return dbc.Badge(
        [html.I(className="me-1"), f"{icono} {texto}"],
        color=color,
        className="mb-3"
    )

def crear_alerta_sincronizacion() -> html.Div:
    """Crea alerta informativa sobre sincronización"""
    
    return dbc.Alert([
        html.I(className="fas fa-sync-alt me-2"),
        html.Strong("Sincronización automática: "),
        "Los cambios realizados en cualquier modo se reflejan automáticamente en el otro. ",
        "Los parámetros se guardan en la estructura activa al presionar 'Guardar Parámetros'."
    ], color="info", className="mb-3", dismissable=True)

def crear_estadisticas_parametros(total: int, editables: int, categorias: int) -> html.Div:
    """Crea panel de estadísticas de parámetros"""
    
    return dbc.Card([
        dbc.CardBody([
            html.H6("Estadísticas", className="card-title"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H4(str(total), className="text-primary mb-0"),
                        html.Small("Total parámetros", className="text-muted")
                    ], className="text-center")
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.H4(str(editables), className="text-success mb-0"),
                        html.Small("Editables", className="text-muted")
                    ], className="text-center")
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.H4(str(categorias), className="text-info mb-0"),
                        html.Small("Categorías", className="text-muted")
                    ], className="text-center")
                ], width=4)
            ])
        ])
    ], className="mb-3")

def crear_toast_validacion() -> dbc.Toast:
    """Crea toast para notificaciones de validación"""
    
    return dbc.Toast(
        id="toast-validacion-tabla",
        header="Validación de Parámetros",
        is_open=False,
        dismissable=True,
        duration=4000,
        icon="danger",
        style={
            "position": "fixed", 
            "top": 66, 
            "right": 10, 
            "width": 350, 
            "z-index": 9999,
            "backgroundColor": "#ffffff",
            "color": "#000000",
            "border": "1px solid #dee2e6"
        },
        header_style={
            "backgroundColor": "#f8f9fa",
            "color": "#000000",
            "border-bottom": "1px solid #dee2e6"
        },
        body_style={
            "color": "#000000"
        }
    )