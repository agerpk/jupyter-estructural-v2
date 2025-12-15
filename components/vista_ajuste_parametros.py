"""
Vista para ajustar parámetros de la estructura actual
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import json
from datetime import datetime

def crear_campo(nombre, tipo, valor, descripcion, opciones=None):
    """Crear un campo de parámetro"""
    # Sliders para parámetros específicos
    if nombre == "alpha":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=180, step=1, value=valor,
            marks={0: '0°', 45: '45°', 90: '90°', 135: '135°', 180: '180°'},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "theta":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=180, step=1, value=valor,
            marks={0: '0°', 45: '45°', 90: '90°', 135: '135°', 180: '180°'},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "t_hielo":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=0.03, step=0.001, value=valor,
            marks={0: '0', 0.01: '0.01', 0.02: '0.02', 0.03: '0.03'},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "SALTO_PORCENTUAL":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=0.1, step=0.01, value=valor,
            marks={0: '0%', 0.05: '5%', 0.1: '10%'},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "PASO_AFINADO":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=0.02, step=0.001, value=valor,
            marks={0: '0%', 0.01: '1%', 0.02: '2%'},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "RELFLECHA_MAX_GUARDIA":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0.5, max=1.1, step=0.01, value=valor,
            marks={0.5: '50%', 0.75: '75%', 1.0: '100%', 1.1: '110%'},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "TENSION":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=1000, step=1, value=valor,
            marks={13.2: '13.2', 33: '33', 66: '66', 132: '132', 220: '220', 330: '330', 500: '500', 600: '600', 700: '700', 800: '800', 900: '900', 1000: '1000'},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "Lk":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=8, step=0.1, value=valor,
            marks={i*0.5: str(i*0.5) for i in range(17)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "LONGITUD_MENSULA_MINIMA_CONDUCTOR":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=5, step=0.05, value=valor,
            marks={i*0.5: str(i*0.5) for i in range(11)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "LONGITUD_MENSULA_MINIMA_GUARDIA":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=5, step=0.05, value=valor,
            marks={i*0.5: str(i*0.5) for i in range(11)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "HADD":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=4, step=0.05, value=valor,
            marks={i: str(i) for i in range(5)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "HADD_HG":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=2, step=0.05, value=valor,
            marks={i*0.5: str(i*0.5) for i in range(5)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "HADD_LMEN":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=2, step=0.05, value=valor,
            marks={i*0.2: str(round(i*0.2, 1)) for i in range(11)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "Altura_MSNM":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=6000, step=50, value=valor,
            marks={i*500: str(i*500) for i in range(13)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "ANCHO_CRUCETA":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=0.5, step=0.01, value=valor,
            marks={i*0.1: str(round(i*0.1, 1)) for i in range(6)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "HADD_ENTRE_AMARRES":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=2, step=0.05, value=valor,
            marks={i*0.2: str(round(i*0.2, 1)) for i in range(11)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "CANT_HG":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=2, step=1, value=valor,
            marks={0: '0', 1: '1', 2: '2'},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "ANG_APANTALLAMIENTO":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=45, step=1, value=valor,
            marks={i: str(i) for i in range(0, 46, 15)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "ALTURA_MINIMA_CABLE":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=10, step=0.1, value=valor,
            marks={i: str(i) for i in range(0, 11, 2)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif nombre == "DIST_REPOSICIONAR_HG":
        input_comp = dcc.Slider(
            id={"type": "param-input", "index": nombre},
            min=0, max=1, step=0.05, value=valor,
            marks={i*0.2: str(round(i*0.2, 1)) for i in range(6)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    elif opciones:
        input_comp = dbc.Select(
            id={"type": "param-input", "index": nombre},
            options=[{"label": opt, "value": opt} for opt in opciones],
            value=valor,
            size="sm"
        )
    elif tipo == bool:
        input_comp = dbc.Switch(
            id={"type": "param-input", "index": nombre},
            value=valor
        )
    else:
        input_comp = dbc.Input(
            id={"type": "param-input", "index": nombre},
            type="number" if tipo in [int, float] else "text",
            value=valor,
            size="sm"
        )
    
    return html.Div([
        html.Label(nombre, style={"fontSize": "1.125rem", "marginBottom": "2px"}),
        html.Div(descripcion, style={"fontSize": "0.9375rem", "color": "#999", "marginBottom": "4px"}) if descripcion else None,
        input_comp
    ], style={"marginBottom": "12px"})

def crear_bloque(titulo, parametros_col1, parametros_col2, estructura, opciones):
    """Crear un bloque de configuración con dos columnas"""
    campos_col1 = []
    for nombre, tipo, desc, opcion_key in parametros_col1:
        valor = estructura.get(nombre, "")
        if valor is None:
            valor = ""
        opts = opciones.get(opcion_key) if opcion_key else None
        campos_col1.append(crear_campo(nombre, tipo, valor, desc, opts))
    
    campos_col2 = []
    for nombre, tipo, desc, opcion_key in parametros_col2:
        valor = estructura.get(nombre, "")
        if valor is None:
            valor = ""
        opts = opciones.get(opcion_key) if opcion_key else None
        campos_col2.append(crear_campo(nombre, tipo, valor, desc, opts))
    
    return html.Div([
        html.H5(titulo, style={"color": "#2084f2", "marginTop": "20px", "marginBottom": "15px", "fontSize": "1.5rem"}),
        dbc.Row([
            dbc.Col(campos_col1, width=6),
            dbc.Col(campos_col2, width=6)
        ])
    ])

def crear_vista_ajuste_parametros(estructura_actual=None, cables_disponibles=None):
    """Crear vista de ajuste de parámetros"""
    
    if estructura_actual is None:
        try:
            with open("actual.estructura.json", "r", encoding="utf-8") as f:
                estructura_actual = json.load(f)
        except FileNotFoundError:
            with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
                estructura_actual = json.load(f)
    
    # Auto-completar fecha_creacion
    if "fecha_creacion" not in estructura_actual or not estructura_actual["fecha_creacion"]:
        estructura_actual["fecha_creacion"] = datetime.now().strftime("%Y-%m-%d")
    
    # Opciones
    opciones = {
        "TIPO_ESTRUCTURA": ["Suspensión Recta", "Suspensión angular", "Retención / Ret. Angular", "Terminal", "Especial"],
        "clase": ["A", "B", "BB", "C", "D", "E"],
        "exposicion": ["B", "C", "D"],
        "Zona_climatica": ["A", "B", "C", "D", "E"],
        "FORZAR_ORIENTACION": ["Longitudinal", "Transversal", "No"],
        "PRIORIDAD_DIMENSIONADO": ["altura_libre", "longitud_total"],
        "Zona_estructura": ["Peatonal", "Rural", "Urbana", "Autopista", "Ferrocarril", "Línea Eléctrica"],
        "METODO_ALTURA_MSNM": ["AEA 3%/300m"],
        "DISPOSICION": ["triangular", "horizontal", "vertical"],
        "TERNA": ["Simple", "Doble"],
        "OBJ_CONDUCTOR": ["FlechaMin", "TiroMin"],
        "OBJ_GUARDIA": ["FlechaMin", "TiroMin"],
        "cable_conductor_id": cables_disponibles if cables_disponibles else [],
        "cable_guardia_id": cables_disponibles if cables_disponibles else [],
        "cable_guardia2_id": cables_disponibles if cables_disponibles else []
    }
    
    # Definir bloques
    bloques = []
    
    # CONFIGURACIÓN GENERAL
    bloques.append(crear_bloque(
        "CONFIGURACIÓN GENERAL",
        [
            ("TITULO", str, None, None),
            ("TIPO_ESTRUCTURA", str, None, "TIPO_ESTRUCTURA"),
            ("clase", str, "Clase de línea según AEA", "clase"),
        ],
        [
            ("exposicion", str, "Exposición al viento", "exposicion"),
            ("Zona_climatica", str, "Zona climática AEA", "Zona_climatica"),
            ("fecha_creacion", str, None, None),
            ("version", str, None, None),
        ],
        estructura_actual, opciones
    ))
    
    # CABLES Y CONDUCTORES
    bloques.append(crear_bloque(
        "CABLES Y CONDUCTORES",
        [
            ("cable_conductor_id", str, "Cable conductor", "cable_conductor_id"),
            ("cable_guardia_id", str, "Cable guardia 1 (derecha, x+)", "cable_guardia_id"),
        ],
        [
            ("cable_guardia2_id", str, "Cable guardia 2 (izquierda, x-)", "cable_guardia2_id"),
        ],
        estructura_actual, opciones
    ))
    
    # CONFIGURACIÓN DISEÑO DE CABEZAL
    bloques.append(crear_bloque(
        "CONFIGURACIÓN DISEÑO DE CABEZAL",
        [
            ("TENSION", int, "Tensión nominal en kV", None),
            ("Zona_estructura", str, None, "Zona_estructura"),
            ("Lk", float, "Longitud cadena oscilante", None),
            ("ANG_APANTALLAMIENTO", float, "Ángulo de apantallamiento", None),
            ("AJUSTAR_POR_ALTURA_MSNM", bool, "Ajustar por alta montaña", None),
            ("METODO_ALTURA_MSNM", str, None, "METODO_ALTURA_MSNM"),
            ("Altura_MSNM", float, "Altura sobre nivel del mar", None),
            ("DISPOSICION", str, None, "DISPOSICION"),
            ("TERNA", str, None, "TERNA"),
            ("CANT_HG", int, "Cantidad cables guardia", None),
        ],
        [
            ("HG_CENTRADO", bool, "Cable guardia centrado", None),
            ("ALTURA_MINIMA_CABLE", float, None, None),
            ("LONGITUD_MENSULA_MINIMA_CONDUCTOR", float, None, None),
            ("LONGITUD_MENSULA_MINIMA_GUARDIA", float, None, None),
            ("HADD", float, "Altura adicional base", None),
            ("HADD_ENTRE_AMARRES", float, "Altura adicional entre amarres", None),
            ("HADD_HG", float, "Altura adicional cable guardia", None),
            ("HADD_LMEN", float, "Altura adicional ménsula", None),
            ("ANCHO_CRUCETA", float, None, None),
            ("AUTOAJUSTAR_LMENHG", bool, "Autoajuste ménsula guardia", None),
            ("DIST_REPOSICIONAR_HG", float, None, None),
        ],
        estructura_actual, opciones
    ))
    
    # PARÁMETROS DE DISEÑO DE LINEA
    bloques.append(crear_bloque(
        "PARÁMETROS DE DISEÑO DE LINEA",
        [
            ("L_vano", float, "Vano regulador de diseño", None),
            ("alpha", float, "Ángulo de quiebre máx. de línea", None),
            ("theta", float, "Ángulo de viento oblicuo", None),
            ("A_cadena", float, "Área en m² de cadena de aisladores", None),
            ("PCADENA", float, "Peso en daN de cadena de aisladores", None),
            ("PESTRUCTURA", float, "Peso en daN de estructura completa sin cables", None),
            ("A_estr_trans", float, "Área transversal de estructura en m²", None),
            ("A_estr_long", float, "Área longitudinal de estructura en m²", None),
            ("Vmax", float, "Viento máximo en m/s", None),
            ("Vmed", float, "Viento medio en m/s", None),
        ],
        [
            ("Vtormenta", float, "Viento de tormenta en m/s", None),
            ("t_hielo", float, "Espesor de manguito de hielo en m", None),
            ("Q", float, "Factor que depende de la densidad del aire, AEA 95301-2007", None),
            ("Zco", float, "Altura efectiva en m, conductor", None),
            ("Zcg", float, "Altura efectiva en m, cable de guardia", None),
            ("Zca", float, "Altura efectiva en m, cadena de aisladores", None),
            ("Zes", float, "Altura efectiva en m, estructura", None),
            ("Cf_cable", float, "Coeficiente de arrastre, cable", None),
            ("Cf_guardia", float, "Coeficiente de arrastre, cable guardia", None),
            ("Cf_cadena", float, "Coeficiente de arrastre, cadena de aisladores", None),
            ("Cf_estructura", float, "Coeficiente de arrastre, estructura", None),
        ],
        estructura_actual, opciones
    ))
    
    # CONFIGURACIÓN SELECCIÓN DE POSTES
    bloques.append(crear_bloque(
        "CONFIGURACIÓN SELECCIÓN DE POSTES",
        [
            ("FORZAR_N_POSTES", int, "0=auto, 1=monoposte, 2=biposte, 3=triposte", None),
            ("FORZAR_ORIENTACION", str, None, "FORZAR_ORIENTACION"),
        ],
        [
            ("PRIORIDAD_DIMENSIONADO", str, None, "PRIORIDAD_DIMENSIONADO"),
        ],
        estructura_actual, opciones
    ))
    
    # CONFIGURACIÓN DE FLECHADO / CÁLCULO MECÁNICO
    bloques.append(crear_bloque(
        "CONFIGURACIÓN DE FLECHADO / CÁLCULO MECÁNICO",
        [
            ("SALTO_PORCENTUAL", float, None, None),
            ("PASO_AFINADO", float, None, None),
            ("OBJ_CONDUCTOR", str, None, "OBJ_CONDUCTOR"),
        ],
        [
            ("OBJ_GUARDIA", str, None, "OBJ_GUARDIA"),
            ("RELFLECHA_MAX_GUARDIA", float, None, None),
            ("RELFLECHA_SIN_VIENTO", bool, None, None),
        ],
        estructura_actual, opciones
    ))
    
    # CONFIGURACIÓN GRÁFICOS
    bloques.append(crear_bloque(
        "CONFIGURACIÓN GRÁFICOS",
        [
            ("ZOOM_CABEZAL", float, None, None),
            ("REEMPLAZAR_TITULO_GRAFICO", bool, None, None),
        ],
        [
            ("MOSTRAR_C2", bool, None, None),
            ("Vn", float, None, None),
        ],
        estructura_actual, opciones
    ))
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Ajustar Parámetros de Estructura", className="mb-0")),
            dbc.CardBody([
                html.Div(bloques),
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Guardar Parámetros",
                            id="guardar-parametros",
                            color="primary",
                            size="lg",
                            className="w-100 mt-4"
                        ),
                        width=6
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Volver",
                            id={"type": "btn-volver", "index": "ajuste"},
                            color="secondary",
                            size="lg",
                            className="w-100 mt-4"
                        ),
                        width=6
                    )
                ])
            ])
        ])
    ])
