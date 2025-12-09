"""
Vista para configuración de nueva estructura
"""

from dash import html
import dash_bootstrap_components as dbc

def crear_vista_configuracion():
    """Crear vista de configuración de nueva estructura"""
    
    # Grupos de parámetros (basados en los comentarios del notebook)
    grupos_parametros = [
        ("CONFIGURACIÓN GENERAL", [
            ("TIPO_ESTRUCTURA", str, "Tipos: Suspensión Recta, Suspensión angular, Retención / Ret. Angular, Terminal"),
            ("exposicion", str, "Exposiciones B, C, D"),
            ("clase", str, "Clase de línea según AEA (A, B, BB, C, D, E)"),
            ("TITULO", str, "Nombre de la estructura"),
        ]),
        
        ("PARÁMETROS DE DISEÑO DE LÍNEA", [
            ("L_vano", float, "Longitud del vano (m)"),
            ("alpha", float, "Ángulo máximo de quiebre (grados)"),
            ("theta", float, "Ángulo de viento oblicuo (grados)"),
            ("Zona_climatica", str, "Zonas climáticas AEA: A,B,C,D,E"),
        ]),
        
        ("CONFIGURACIÓN SELECCIÓN DE POSTES", [
            ("FORZAR_N_POSTES", int, "0=auto, 1=monoposte, 2=biposte, 3=triposte"),
            ("FORZAR_ORIENTACION", str, "Opciones: Longitudinal, Transversal, No"),
            ("PRIORIDAD_DIMENSIONADO", str, "altura_libre o longitud_total"),
        ]),
        
        ("CONFIGURACIÓN DISEÑO DE CABEZAL", [
            ("TENSION", int, "Tensión nominal (kV)"),
            ("Zona_estructura", str, "Rural, Urbana, Peatonal, Autopista, etc."),
            ("DISPOSICION", str, "triangular, horizontal, vertical"),
            ("TERNA", str, "Simple, Doble"),
        ]),
        
        ("CONFIGURACIÓN DE FLECHADO / CÁLCULO MECÁNICO", [
            ("OBJ_CONDUCTOR", str, "FlechaMin o TiroMin"),
            ("OBJ_GUARDIA", str, "FlechaMin o TiroMin"),
            ("SALTO_PORCENTUAL", float, "Salto porcentual para cálculo"),
            ("PASO_AFINADO", float, "Paso de afinado"),
        ]),
    ]
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Configurar Nueva Estructura", className="mb-0")),
            dbc.CardBody([
                dbc.Alert(
                    "Configure los parámetros para una nueva estructura. Los valores mostrados son de la plantilla por defecto.",
                    color="info",
                    className="mb-4"
                ),
                
                html.Div([
                    "Nota: Esta funcionalidad está en desarrollo. Use 'Ajustar Parámetros' en el menú EDITAR para modificar la estructura actual."
                ], className="mb-4 text-muted"),
                
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Crear Estructura",
                            id="btn-crear-estructura",
                            color="primary",
                            size="lg",
                            className="w-100"
                        ),
                        width=6
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Volver",
                            id={"type": "btn-volver", "index": "configuracion"},
                            color="secondary",
                            size="lg",
                            className="w-100"
                        ),
                        width=6
                    )
                ])
            ])
        ])
    ])