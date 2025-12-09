"""
Vista para configuración de nueva estructura
"""

from dash import html
import dash_bootstrap_components as dbc
from components.parametro_input import crear_grupo_parametros

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
    
    # Opciones especiales para ciertos parámetros
    opciones_especiales = {
        "TIPO_ESTRUCTURA": ["Suspensión Recta", "Suspensión angular", "Retención / Ret. Angular", "Terminal"],
        "exposicion": ["B", "C", "D"],
        "clase": ["A", "B", "BB", "C", "D", "E"],
        "Zona_climatica": ["A", "B", "C", "D", "E"],
        "FORZAR_ORIENTACION": ["Longitudinal", "Transversal", "No"],
        "PRIORIDAD_DIMENSIONADO": ["altura_libre", "longitud_total"],
        "Zona_estructura": ["Peatonal", "Rural", "Urbana", "Autopista", "Ferrocarril", "Línea Eléctrica"],
        "DISPOSICION": ["triangular", "horizontal", "vertical"],
        "TERNA": ["Simple", "Doble"],
        "OBJ_CONDUCTOR": ["FlechaMin", "TiroMin"],
        "OBJ_GUARDIA": ["FlechaMin", "TiroMin"],
    }
    
    # Crear acordeón con grupos de parámetros
    items_acordeon = []
    for grupo_nombre, parametros in grupos_parametros:
        items_acordeon.append(
            crear_grupo_parametros(grupo_nombre, parametros, {}, opciones_especiales)
        )
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Configurar Nueva Estructura", className="mb-0")),
            dbc.CardBody([
                dbc.Alert(
                    "Configure los parámetros para una nueva estructura. Los valores mostrados son de la plantilla por defecto.",
                    color="info",
                    className="mb-4"
                ),
                
                dbc.Accordion(
                    items_acordeon,
                    always_open=True,
                    className="mb-4"
                ),
                
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
                            id="btn-volver-home",
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