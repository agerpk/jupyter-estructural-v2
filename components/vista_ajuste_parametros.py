"""Vista para ajustar parámetros de la estructura actual"""

from dash import html
import dash_bootstrap_components as dbc
import json
from components.modal_estados_climaticos import crear_modal_estados_climaticos
from components.modal_copiar_estados import crear_modal_copiar_estados

def crear_vista_ajuste_parametros_con_pestanas(estructura_actual=None, cables_disponibles=None):
    """Crear vista de ajuste de parámetros - solo modo tabla"""
    from components.tabla_parametros import crear_tabla_parametros, crear_filtros_categoria
    from components.pestanas_parametros import crear_toast_validacion
    
    # Indicador de estructura activa
    if estructura_actual:
        titulo = estructura_actual.get('TITULO', 'Sin título')
        indicador = dbc.Alert(f"📁 Editando: {titulo}.estructura.json", color="info", className="mb-3")
    else:
        indicador = dbc.Alert("⚠️ No hay estructura activa", color="warning", className="mb-3")
    
    # Obtener cables disponibles
    try:
        with open("data/cables.json", "r", encoding="utf-8") as f:
            cables_data = json.load(f)
            cables_disponibles = list(cables_data.keys())
    except:
        cables_disponibles = []
    
    return html.Div([
        indicador,
        dbc.Card([
            dbc.CardHeader([
                dbc.Button("Editar Estados Climaticos y Restricciones", id="btn-abrir-estados-ajuste", 
                          color="info", size="sm", className="me-2"),
                html.H4("Ajustar Parámetros de Estructura", className="d-inline mb-0")
            ]),
            dbc.CardBody([
                # Botones de acción
                dbc.Row([
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
                ], className="mb-4"),
                
                # Contenido tabla
                crear_filtros_categoria(),
                crear_tabla_parametros(estructura_actual, cables_disponibles),
                crear_toast_validacion()
            ])
        ]),
        
        # Modales
        crear_modal_estados_climaticos("modal-estados-ajuste"),
        crear_modal_copiar_estados("modal-copiar-estados-ajuste")
    ])
