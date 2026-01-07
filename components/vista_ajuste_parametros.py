"""
Vista para ajustar parámetros de la estructura actual
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import json
from datetime import datetime
from config.parametros_controles import obtener_config_control

def crear_vista_ajuste_parametros_con_pestanas(estructura_actual=None, cables_disponibles=None):
    """Crear vista de ajuste de parámetros con sistema de pestañas"""
    
    from components.pestanas_parametros import crear_pestanas_parametros, crear_toast_validacion, crear_botones_accion
    
    # Indicador de estructura activa
    if estructura_actual:
        titulo = estructura_actual.get('TITULO', 'Sin título')
        indicador = dbc.Alert(f"📁 Editando: {titulo}.estructura.json", color="info", className="mb-3")
    else:
        indicador = dbc.Alert("⚠️ No hay estructura activa", color="warning", className="mb-3")
    
    return html.Div([
        indicador,
        dbc.Card([
            dbc.CardHeader(html.H4("Ajustar Parámetros de Estructura", className="mb-0")),
            dbc.CardBody([
                # Botones arriba de las pestañas
                crear_botones_accion(),
                html.Hr(),
                crear_pestanas_parametros(),
                crear_toast_validacion()
            ])
        ])
    ])

def crear_campo(nombre, tipo, valor, descripcion, opciones=None):
    """Crear un campo de parámetro usando configuración centralizada"""
    # Convertir valores vacíos o None a valores por defecto según el tipo
    if valor == "" or valor is None:
        if tipo in [int, float]:
            valor = 0
        elif tipo == bool:
            valor = False
        else:
            valor = ""
    
    # Intentar obtener configuración centralizada
    config = obtener_config_control(nombre)
    
    if config:
        if config["tipo"] == "slider":
            input_comp = dcc.Slider(
                id={"type": "param-input", "index": nombre},
                min=config["min"],
                max=config["max"],
                step=config["step"],
                value=valor,
                marks=config["marks"],
                tooltip={"placement": "bottom", "always_visible": True}
            )
        elif config["tipo"] == "slider_input":
            input_comp = dbc.Row([
                dbc.Col(dcc.Slider(
                    id={"type": "param-slider", "index": nombre},
                    min=config["min"],
                    max=config["max"],
                    step=config["step"],
                    value=valor,
                    marks=config["marks"],
                    tooltip={"placement": "bottom", "always_visible": True}
                ), width=8),
                dbc.Col(dbc.Input(
                    id={"type": "param-input", "index": nombre},
                    type="number", value=valor, step=config["step"], size="sm"
                ), width=4)
            ])
        elif config["tipo"] == "select":
            input_comp = dbc.Select(
                id={"type": "param-input", "index": nombre},
                options=[{"label": opt, "value": opt} for opt in config["opciones"]],
                value=valor,
                size="sm"
            )
        elif config["tipo"] == "switch":
            input_comp = dbc.Switch(
                id={"type": "param-input", "index": nombre},
                value=valor
            )
        elif config["tipo"] == "input":
            input_comp = dbc.Input(
                id={"type": "param-input", "index": nombre},
                type=config["input_type"],
                value=valor,
                size="sm"
            )
        else:
            # Fallback a input genérico
            input_comp = dbc.Input(
                id={"type": "param-input", "index": nombre},
                type="number" if tipo in [int, float] else "text",
                value=valor,
                size="sm"
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
            from models.app_state import AppState
            state = AppState()
            # Intentar cargar estructura actual desde el sistema unificado
            if hasattr(state, '_current_estructura_titulo') and state._current_estructura_titulo:
                ruta_actual = state.get_estructura_actual_path()
                with open(ruta_actual, "r", encoding="utf-8") as f:
                    estructura_actual = json.load(f)
            else:
                # Fallback a plantilla si no hay estructura actual
                with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
                    estructura_actual = json.load(f)
        except (FileNotFoundError, AttributeError):
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
        "cable_guardia2_id": cables_disponibles if cables_disponibles else [],
        "metodo_fundacion": ["sulzberger", "mohr_pohl"],
        "forma_fundacion": ["monobloque", "escalonada_recta", "escalonada_piramide"],
        "tipo_base_fundacion": ["Rombica", "Cuadrada"],
        "mensula_defasar": ["primera", "segunda", "tercera"]
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
            ("defasaje_mensula_hielo", bool, "Activar defasaje por hielo", None),
            ("lmen_extra_hielo", float, "Longitud extra hielo (m)", None),
            ("mensula_defasar", str, "Ménsula a defasar", "mensula_defasar"),
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
            ("VANO_DESNIVELADO", bool, "Si es True, se calcula el vano peso según desnivel de catenarias", None),
            ("H_PIQANTERIOR", float, "Altura piquete anterior (m)", None),
            ("H_PIQPOSTERIOR", float, "Altura piquete posterior (m) - Visto en gráfico", None),
            ("SALTO_PORCENTUAL", float, None, None),
            ("PASO_AFINADO", float, None, None),
        ],
        [
            ("OBJ_CONDUCTOR", str, None, "OBJ_CONDUCTOR"),
            ("OBJ_GUARDIA", str, None, "OBJ_GUARDIA"),
            ("RELFLECHA_MAX_GUARDIA", float, None, None),
            ("RELFLECHA_SIN_VIENTO", bool, None, None),
        ],
        estructura_actual, opciones
    ))
    
    # CONFIGURACIÓN GRÁFICOS
    bloques.append(crear_bloque(
        "CONFIGURACIÓN DE VISUALIZACIÓN",
        [
            ("ZOOM_CABEZAL", float, None, None),
            ("REEMPLAZAR_TITULO_GRAFICO", bool, None, None),
            ("ADC_3D", bool, "Árboles de carga en 3D", None),
        ],
        [
            ("MOSTRAR_C2", bool, None, None),
            ("Vn", float, None, None),
        ],
        estructura_actual, opciones
    ))
    
    # PARÁMETROS DE FUNDACIÓN
    bloques.append(crear_bloque(
        "PARÁMETROS DE FUNDACIÓN",
        [
            ("metodo_fundacion", str, "Método de cálculo", "metodo_fundacion"),
            ("forma_fundacion", str, "Forma de fundación", "forma_fundacion"),
            ("tipo_base_fundacion", str, "Tipo de base", "tipo_base_fundacion"),
            ("profundidad_propuesta", float, "Profundidad propuesta (tin) [m]", None),
            ("longitud_colineal_inferior", float, "Longitud colineal inferior (ain) [m]", None),
            ("longitud_transversal_inferior", float, "Longitud transversal inferior (bin) [m]", None),
            ("coef_seguridad_volcamiento", float, "Coef. seguridad volcamiento (F.S)", None),
            ("inclinacion_desplazamiento", float, "Inclinación desplazamiento (tg α adm)", None),
            ("relacion_max_sin_armadura", float, "Relación máx. sin armadura (t/he)", None),
            ("superacion_presion_admisible", float, "Superación presión adm. (σmax/σadm)", None),
            ("indice_compresibilidad", float, "Índice compresibilidad C [kg/m³]", None),
        ],
        [
            ("presion_admisible", float, "Presión admisible σadm [kg/m²]", None),
            ("angulo_tierra_gravante", float, "Ángulo tierra gravante β [°]", None),
            ("coef_friccion_terreno_hormigon", float, "Coef. fricción terreno-hormigón μ", None),
            ("densidad_hormigon", float, "Densidad hormigón [kg/m³]", None),
            ("densidad_tierra", float, "Densidad tierra [kg/m³]", None),
            ("coef_aumento_cb_ct", float, "Coef. aumento Cb/Ct", None),
            ("distancia_molde_hueco_lateral", float, "Distancia molde hueco lateral (dml) [m]", None),
            ("distancia_molde_hueco_fondo", float, "Distancia molde hueco fondo (dmf) [m]", None),
            ("diametro_molde", float, "Diámetro molde (dmol) [m]", None),
            ("separacion_postes_cima", float, "Separación postes cima (spc) [m]", None),
            ("pendiente_postes_multiples", float, "Pendiente postes múltiples (pp) [%]", None),
            ("conicidad_poste", float, "Conicidad poste (con) [%]", None),
            ("incremento_calculo", float, "Incremento cálculo [m]", None),
        ],
        estructura_actual, opciones
    ))
    
    # PARÁMETROS DE COSTEO
    def crear_campos_costeo(estructura_actual):
        """Crear campos para parámetros de costeo anidados"""
        costeo = estructura_actual.get('costeo', {})
        postes = costeo.get('postes', {})
        accesorios = costeo.get('accesorios', {})
        fundaciones = costeo.get('fundaciones', {})
        montaje = costeo.get('montaje', {})
        adicional = costeo.get('adicional_estructura', 2000.0)
        
        campos_col1 = [
            crear_campo("costeo_coef_a", float, postes.get('coef_a', 0.5), "Coeficiente A (por kg peso)"),
            crear_campo("costeo_coef_b", float, postes.get('coef_b', 100.0), "Coeficiente B (por m altura)"),
            crear_campo("costeo_coef_c", float, postes.get('coef_c', 1000.0), "Coeficiente C (fijo)"),
            crear_campo("costeo_precio_vinculos", float, accesorios.get('vinculos', 50.0), "Precio vínculos [UM/u]"),
            crear_campo("costeo_precio_crucetas", float, accesorios.get('crucetas', 400.0), "Precio crucetas [UM/u]"),
            crear_campo("costeo_precio_mensulas", float, accesorios.get('mensulas', 175.0), "Precio ménsulas [UM/u]"),
        ]
        
        campos_col2 = [
            crear_campo("costeo_precio_hormigon", float, fundaciones.get('precio_m3_hormigon', 150.0), "Precio hormigón [UM/m³]"),
            crear_campo("costeo_factor_hierro", float, fundaciones.get('factor_hierro', 1.2), "Factor hierro"),
            crear_campo("costeo_precio_estructura", float, montaje.get('precio_por_estructura', 5000.0), "Precio por estructura [UM]"),
            crear_campo("costeo_factor_terreno", float, montaje.get('factor_terreno', 1.0), "Factor terreno"),
            crear_campo("costeo_adicional_estructura", float, adicional, "Adicional estructura [UM]"),
        ]
        
        return campos_col1, campos_col2
    
    campos_costeo_col1, campos_costeo_col2 = crear_campos_costeo(estructura_actual)
    
    bloques.append(html.Div([
        html.H5("PARÁMETROS DE COSTEO", style={"color": "#2084f2", "marginTop": "20px", "marginBottom": "15px", "fontSize": "1.5rem"}),
        dbc.Row([
            dbc.Col(campos_costeo_col1, width=6),
            dbc.Col(campos_costeo_col2, width=6)
        ])
    ]))
    
    # Indicador de estructura activa
    if estructura_actual:
        titulo = estructura_actual.get('TITULO', 'Sin título')
        indicador = dbc.Alert(f"📁 Editando: {titulo}.estructura.json", color="info", className="mb-3")
    else:
        indicador = dbc.Alert("⚠️ No hay estructura activa", color="warning", className="mb-3")
    
    return html.Div([
        indicador,
        dbc.Card([
            dbc.CardHeader(html.H4("Ajustar Parámetros de Estructura", className="mb-0")),
            dbc.CardBody([
                # Botón para modificar estados climáticos
                dbc.Card([
                    dbc.CardHeader(html.H6("Estados Climáticos y Restricciones")),
                    dbc.CardBody([
                        dbc.Button("Modificar Estados Climáticos y Restricciones", 
                                  id="btn-modificar-estados-panel", 
                                  color="info", size="sm")
                    ])
                ], className="mb-3"),
                
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
