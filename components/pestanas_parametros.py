"""
Sistema de pestañas para alternar entre Modo Tabla y Modo Panel.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def crear_tabla_estados_climaticos_ajuste(estructura_actual):
    """Crear tabla editable de estados climáticos con restricciones para vista ajuste parámetros"""
    
    # Cargar estados desde estructura_actual si existen
    estados_guardados = estructura_actual.get("estados_climaticos", {})
    
    # Valores por defecto
    estados_default = {
        "I": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "espesor_hielo": 0},
        "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "espesor_hielo": 0},
        "III": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": estructura_actual.get("Vmax", 38.9), "espesor_hielo": 0},
        "IV": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": estructura_actual.get("Vmed", 15.56), "espesor_hielo": estructura_actual.get("t_hielo", 0.01)},
        "V": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "espesor_hielo": 0}
    }
    
    # Mezclar estados guardados con defaults
    for estado_id in estados_default.keys():
        if estado_id in estados_guardados:
            estados_default[estado_id].update(estados_guardados[estado_id])
    
    # Cargar restricciones desde estructura_actual si existen
    restricciones_guardadas = estructura_actual.get("restricciones_cables", {})
    restricciones_conductor = restricciones_guardadas.get("conductor", {}).get("tension_max_porcentaje", {})
    restricciones_guardia = restricciones_guardadas.get("guardia", {}).get("tension_max_porcentaje", {})
    
    # Defaults si no existen
    if not restricciones_conductor:
        restricciones_conductor = {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25}
    if not restricciones_guardia:
        restricciones_guardia = {"I": 0.7, "II": 0.70, "III": 0.70, "IV": 0.7, "V": 0.7}
    
    # Encabezado
    header = dbc.Row([
        dbc.Col(html.Strong("Estado"), md=1),
        dbc.Col(html.Strong("Temp (°C)"), md=1),
        dbc.Col(html.Strong("Descripción"), md=2),
        dbc.Col(html.Strong("Viento (m/s)"), md=2),
        dbc.Col(html.Strong("Hielo (m)"), md=2),
        dbc.Col(html.Strong("Restricción Conductor (%)"), md=2),
        dbc.Col(html.Strong("Restricción Guardia (%)"), md=2),
    ], className="mb-2 fw-bold")
    
    filas = [header]
    for estado_id, valores in estados_default.items():
        fila = dbc.Row([
            dbc.Col(html.Strong(estado_id), md=1),
            dbc.Col(
                dbc.Input(id={"type": "estado-temp-ajuste", "index": estado_id}, type="number", 
                         value=valores.get("temperatura"), size="sm"), md=1
            ),
            dbc.Col(
                dbc.Input(id={"type": "estado-desc-ajuste", "index": estado_id}, type="text",
                         value=valores.get("descripcion"), size="sm", disabled=True), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "estado-viento-ajuste", "index": estado_id}, type="number",
                         value=valores.get("viento_velocidad"), size="sm"), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "estado-hielo-ajuste", "index": estado_id}, type="number",
                         value=valores.get("espesor_hielo"), size="sm"), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "restriccion-conductor-ajuste", "index": estado_id}, type="number",
                         value=restricciones_conductor.get(estado_id, 0.25), size="sm", step=0.01, min=0, max=1), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "restriccion-guardia-ajuste", "index": estado_id}, type="number",
                         value=restricciones_guardia.get(estado_id, 0.7), size="sm", step=0.01, min=0, max=1), md=2
            ),
        ], className="mb-2")
        filas.append(fila)
    
    return html.Div(filas)

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