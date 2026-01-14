"""
Modal para edición de estados climáticos y restricciones de cables.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

def crear_modal_estados_climaticos(modal_id="modal-estados-climaticos"):
    """
    Crea modal para editar estados climáticos
    
    Args:
        modal_id: ID del modal
    
    Returns:
        dbc.Modal con tabla dinámica de estados
    """
    
    return dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle("Estados Climáticos y Restricciones", style={"color": "#ffffff"}), 
            style={"backgroundColor": "#1e1e1e"}
        ),
        dbc.ModalBody([
            # Botones de control
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Agregar Estado",
                        id=f"{modal_id}-btn-agregar",
                        color="success",
                        size="sm",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Copiar Estados Desde",
                        id=f"{modal_id}-btn-copiar",
                        color="info",
                        size="sm"
                    )
                ], width=12, className="mb-3")
            ]),
            
            # Tabla de estados
            html.Div(id=f"{modal_id}-tabla-container"),
            
            # Stores
            dcc.Store(id=f"{modal_id}-estados-data", data={}),
        ], style={"backgroundColor": "#2d2d2d", "color": "#ffffff"}),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id=f"{modal_id}-btn-cancelar", color="secondary", className="me-2"),
            dbc.Button("Guardar", id=f"{modal_id}-btn-guardar", color="primary")
        ], style={"backgroundColor": "#1e1e1e"})
    ], id=modal_id, is_open=False, size="xl", scrollable=True)


def generar_tabla_estados(estados_climaticos, modal_id="modal-estados-climaticos"):
    """
    Genera tabla HTML con estados climáticos
    
    Args:
        estados_climaticos: Dict con estados {id: {temperatura, descripcion, ...}}
        modal_id: ID del modal padre
    
    Returns:
        html.Div con tabla
    """
    
    if not estados_climaticos:
        return html.Div("No hay estados definidos", 
                       style={"color": "#ffffff", "backgroundColor": "#2d2d2d", "padding": "20px"})
    
    # Ordenar por ID (manejar legacy romanos y numéricos)
    def sort_key(item):
        estado_id = item[0]
        # Mapeo legacy romano a numérico
        mapeo_romano = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
        if estado_id in mapeo_romano:
            return mapeo_romano[estado_id]
        try:
            return int(estado_id)
        except ValueError:
            return 999  # Otros al final
    
    estados_ordenados = sorted(estados_climaticos.items(), key=sort_key)
    
    # Crear filas
    filas = []
    for estado_id, datos in estados_ordenados:
        fila = html.Tr([
            # ID (no editable)
            html.Td(estado_id, className="text-center fw-bold", 
                   style={"color": "#ffffff", "backgroundColor": "#2d2d2d"}),
            
            # Temperatura
            html.Td(
                dbc.Input(
                    id={"type": "input-temp", "modal": modal_id, "id": estado_id},
                    type="number",
                    value=datos.get("temperatura", 0),
                    min=-273,
                    max=400,
                    step=1,
                    size="sm",
                    style={"backgroundColor": "#1e1e1e", "color": "#ffffff", "borderColor": "#555"}
                ),
                style={"backgroundColor": "#2d2d2d"}
            ),
            
            # Descripción
            html.Td(
                dbc.Input(
                    id={"type": "input-desc", "modal": modal_id, "id": estado_id},
                    type="text",
                    value=datos.get("descripcion", ""),
                    size="sm",
                    style={"backgroundColor": "#1e1e1e", "color": "#ffffff", "borderColor": "#555"}
                ),
                style={"backgroundColor": "#2d2d2d"}
            ),
            
            # Viento
            html.Td(
                dbc.Input(
                    id={"type": "input-viento", "modal": modal_id, "id": estado_id},
                    type="number",
                    value=datos.get("viento_velocidad", 0),
                    min=0,
                    step=0.1,
                    size="sm",
                    style={"backgroundColor": "#1e1e1e", "color": "#ffffff", "borderColor": "#555"}
                ),
                style={"backgroundColor": "#2d2d2d"}
            ),
            
            # Hielo
            html.Td(
                dbc.Input(
                    id={"type": "input-hielo", "modal": modal_id, "id": estado_id},
                    type="number",
                    value=datos.get("espesor_hielo", 0),
                    min=0,
                    step=0.001,
                    size="sm",
                    style={"backgroundColor": "#1e1e1e", "color": "#ffffff", "borderColor": "#555"}
                ),
                style={"backgroundColor": "#2d2d2d"}
            ),
            
            # Restricción conductor
            html.Td(
                dbc.Input(
                    id={"type": "input-rest-cond", "modal": modal_id, "id": estado_id},
                    type="number",
                    value=datos.get("restriccion_conductor", 0.25),
                    min=0,
                    max=1,
                    step=0.01,
                    size="sm",
                    style={"backgroundColor": "#1e1e1e", "color": "#ffffff", "borderColor": "#555"}
                ),
                style={"backgroundColor": "#2d2d2d"}
            ),
            
            # Restricción guardia
            html.Td(
                dbc.Input(
                    id={"type": "input-rest-guard", "modal": modal_id, "id": estado_id},
                    type="number",
                    value=datos.get("restriccion_guardia", 0.7),
                    min=0,
                    max=1,
                    step=0.01,
                    size="sm",
                    style={"backgroundColor": "#1e1e1e", "color": "#ffffff", "borderColor": "#555"}
                ),
                style={"backgroundColor": "#2d2d2d"}
            ),
            
            # Relación flecha
            html.Td(
                dbc.Input(
                    id={"type": "input-relflecha", "modal": modal_id, "id": estado_id},
                    type="number",
                    value=datos.get("relflecha", 0.9),
                    min=0,
                    step=0.01,
                    size="sm",
                    style={"backgroundColor": "#1e1e1e", "color": "#ffffff", "borderColor": "#555"}
                ),
                style={"backgroundColor": "#2d2d2d"}
            ),
            
            # Botón eliminar
            html.Td(
                dbc.Button(
                    "X",
                    id={"type": "btn-eliminar", "modal": modal_id, "id": estado_id},
                    color="danger",
                    size="sm",
                    outline=True
                ),
                className="text-center",
                style={"backgroundColor": "#2d2d2d"}
            )
        ], style={"backgroundColor": "#2d2d2d"})
        filas.append(fila)
    
    # Tabla completa con contenedor oscuro
    tabla = html.Div([
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("ID", className="text-center", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"}),
                html.Th("Temp (°C)", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"}),
                html.Th("Descripción", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"}),
                html.Th("Viento (m/s)", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"}),
                html.Th("Hielo (m)", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"}),
                html.Th("Rest. Cond.", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"}),
                html.Th("Rest. Guard.", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"}),
                html.Th("Relflecha", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"}),
                html.Th("", className="text-center", style={"color": "#ffffff", "backgroundColor": "#1e1e1e"})
            ])),
            html.Tbody(filas, style={"backgroundColor": "#2d2d2d"})
        ], bordered=True, hover=True, responsive=True, size="sm", 
           style={"backgroundColor": "#2d2d2d", "color": "#ffffff", "marginBottom": "0"})
    ], style={"backgroundColor": "#2d2d2d", "padding": "0"})
    
    return tabla
