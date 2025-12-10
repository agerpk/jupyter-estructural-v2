"""
Vista principal/home de la aplicación
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from models.app_state import AppState
from config.app_config import ARCHIVOS_PROTEGIDOS, DATA_DIR

def crear_tarjeta_estructuras_disponibles():
    """Crear tarjeta con lista de estructuras disponibles"""
    state = AppState()
    estructuras = state.estructura_manager.listar_estructuras()
    estructuras_filtradas = [e for e in estructuras if e not in ARCHIVOS_PROTEGIDOS]
    
    if not estructuras_filtradas:
        contenido = dbc.Alert("No hay estructuras guardadas en la base de datos", color="info")
    else:
        items = []
        for estructura in estructuras_filtradas:
            nombre_mostrar = estructura.replace(".estructura.json", "")
            
            # Cargar datos de la estructura
            try:
                ruta = DATA_DIR / estructura
                datos = state.estructura_manager.cargar_estructura(ruta)
                tipo = datos.get("TIPO_ESTRUCTURA", "N/A")
                terna = datos.get("TERNA", "N/A")
                disposicion = datos.get("DISPOSICION", "N/A")
                tension = datos.get("TENSION", "N/A")
                alpha = datos.get("alpha", 0)
                hadd = datos.get("HADD", 0)
                
                # Generar código
                codigo = ""
                tipo_lower = tipo.lower()
                if "suspensión" in tipo_lower or "suspension" in tipo_lower:
                    codigo = "SD" if alpha > 0 else "S"
                elif "retención" in tipo_lower or "retencion" in tipo_lower:
                    codigo = "RA" if alpha > 0 else "R"
                elif "terminal" in tipo_lower:
                    codigo = "T"
                elif "especial" in tipo_lower:
                    codigo = "E"
                
                if alpha > 0:
                    codigo += f"{alpha:.0f}°"
                
                if "simple" in terna.lower():
                    codigo += "st"
                elif "doble" in terna.lower():
                    codigo += "dt"
                
                if float(hadd) >= 1.0:
                    codigo += f"+{int(round(hadd))}"
                
                info_extra = f"{tipo} | {terna} | {disposicion} | {tension} kV"
            except:
                codigo = ""
                info_extra = ""
            
            items.append(
                dbc.ListGroupItem([
                    dbc.Row([
                        dbc.Col([
                            html.Span(codigo, className="text-info me-2", style={"fontSize": "18px", "fontWeight": "bold"}) if codigo else None,
                            html.I(className="fas fa-file-alt me-2 text-info"),
                            html.Span(nombre_mostrar, className="text-light fw-bold me-3", style={"fontSize": "14px"}),
                            html.Small(info_extra, className="text-info") if info_extra else None
                        ], width=10),
                        dbc.Col([
                            dbc.DropdownMenu([
                                dbc.DropdownMenuItem("Cargar como estructura actual", id={"type": "btn-cargar-estructura", "index": estructura}),
                                dbc.DropdownMenuItem("Descargar parámetros", id={"type": "btn-descargar-estructura", "index": estructura}),
                                dbc.DropdownMenuItem(divider=True),
                                dbc.DropdownMenuItem("Duplicar", id={"type": "btn-duplicar-estructura", "index": estructura}),
                                dbc.DropdownMenuItem("Eliminar", id={"type": "btn-eliminar-estructura-home", "index": estructura}, className="text-danger"),
                            ], size="sm", direction="start", label="⋮", color="secondary", className="p-0", style={"fontSize": "1.2rem"})
                        ], width=2, className="text-end")
                    ], align="center")
                ], action=False, className="py-2", style={"backgroundColor": "#1a1d21", "borderColor": "#2d3139"})
            )
        contenido = dbc.ListGroup(items, flush=True, style={"backgroundColor": "#1a1d21"})
    
    return dbc.Card([
        dbc.CardHeader(html.H5("Estructuras Disponibles", className="mb-0")),
        dbc.CardBody([
            contenido,
            html.P(f"Total: {len(estructuras_filtradas)} estructura(s)", className="text-muted mt-3 mb-0")
        ])
    ])

def crear_tarjeta_estructura_actual():
    """Crear tarjeta con resumen de estructura actual"""
    state = AppState()
    estructura = state.cargar_estructura_actual()
    
    if not estructura:
        return dbc.Card([
            dbc.CardHeader(html.H5("Estructura Actual", className="mb-0")),
            dbc.CardBody([
                dbc.Alert("No hay estructura cargada", color="warning")
            ])
        ])
    
    titulo = estructura.get("TITULO", "Sin título")
    tipo = estructura.get("TIPO_ESTRUCTURA", "N/A")
    terna = estructura.get("TERNA", "N/A")
    disposicion = estructura.get("DISPOSICION", "N/A")
    tension = estructura.get("TENSION", "N/A")
    alpha = estructura.get("alpha", 0)
    hadd = estructura.get("HADD", 0)
    
    conductor = estructura.get("cable_conductor_id", "N/A")
    guardia = estructura.get("cable_guardia_id", "N/A")
    vano = estructura.get("L_vano", "N/A")
    vmax = estructura.get("Vmax", "N/A")
    msnm = estructura.get("Altura_MSNM", "N/A")
    
    # Generar código de estructura
    codigo = ""
    tipo_lower = tipo.lower()
    if "suspensión" in tipo_lower or "suspension" in tipo_lower:
        codigo = "SD" if alpha > 0 else "S"
    elif "retención" in tipo_lower or "retencion" in tipo_lower:
        codigo = "RA" if alpha > 0 else "R"
    elif "terminal" in tipo_lower:
        codigo = "T"
    elif "especial" in tipo_lower:
        codigo = "E"
    
    if alpha > 0:
        codigo += f"{alpha:.0f}°"
    
    if "simple" in terna.lower():
        codigo += "st"
    elif "doble" in terna.lower():
        codigo += "dt"
    
    if hadd >= 1.0:
        codigo += f"+{int(round(hadd))}"
    
    return dbc.Card([
        dbc.Row([
            dbc.Col([
                dbc.CardHeader([
                    html.H5("Actual: ", className="d-inline mb-0"),
                    html.Span(f"{titulo} ", className="text-light fw-bold"),
                    html.Small(f"| {tipo} | {terna} | {disposicion} | {tension} kV", className="text-info")
                ]),
                dbc.CardBody([
                    html.Div([
                        html.P([html.Strong("Conductor: ", className="text-light"), html.Span(conductor, className="text-info")], className="mb-2"),
                        html.P([html.Strong("Guardia: ", className="text-light"), html.Span(guardia, className="text-info")], className="mb-2"),
                        html.P([html.Strong("Vano: ", className="text-light"), html.Span(f"{vano} m", className="text-info")], className="mb-2"),
                        html.P([html.Strong("Vmax: ", className="text-light"), html.Span(f"{vmax} m/s", className="text-info")], className="mb-2"),
                        html.P([html.Strong("MSNM: ", className="text-light"), html.Span(f"{msnm} m", className="text-info")], className="mb-0")
                    ])
                ])
            ], width=10),
            dbc.Col([
                html.Div(
                    html.Span(codigo, className="text-info", style={"fontSize": "clamp(16px, 2vw, 32px)", "fontWeight": "bold", "wordBreak": "break-word", "textAlign": "center"}),
                    className="d-flex align-items-center justify-content-center h-100",
                    style={"backgroundColor": "#1a1d21", "borderLeft": "2px solid #2d3139", "padding": "0.5rem"}
                )
            ], width=2, className="p-0")
        ], className="g-0")
    ])

def crear_vista_home():
    """Crear vista principal/home"""
    
    return html.Div([
        # Modales
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirmar Eliminación")),
            dbc.ModalBody([
                html.P(id="texto-confirmar-eliminar")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancelar-eliminar-home", color="secondary"),
                dbc.Button("Eliminar", id="btn-confirmar-eliminar-home", color="danger")
            ])
        ], id="modal-confirmar-eliminar-home", is_open=False),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Duplicar Estructura")),
            dbc.ModalBody([
                dbc.Label("Nombre de la copia:"),
                dbc.Input(id="input-nombre-duplicado", type="text", placeholder="nombre_copia")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancelar-duplicar", color="secondary"),
                dbc.Button("Aceptar", id="btn-confirmar-duplicar", color="primary")
            ])
        ], id="modal-duplicar-estructura", is_open=False),
        
        dbc.Row([
            # Tarjeta de Estructura Actual
            dbc.Col([
                crear_tarjeta_estructura_actual()
            ], lg=6, md=12, className="mb-4"),
            
            # Tarjeta de Estructuras Disponibles
            dbc.Col([
                crear_tarjeta_estructuras_disponibles()
            ], lg=6, md=12, className="mb-4"),
        ]),
        
        # Stores para mantener estado
        dcc.Store(id="estructura-a-eliminar"),
        dcc.Store(id="estructura-a-duplicar")
    ])
