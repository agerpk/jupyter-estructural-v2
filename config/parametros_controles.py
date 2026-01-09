"""
Definición centralizada de controles para parámetros de estructura.
Todos los sliders, inputs y selects se definen aquí para mantener consistencia.
"""

# Definición de controles por parámetro
CONTROLES_PARAMETROS = {
    # Sliders numéricos
    "alpha": {
        "tipo": "slider",
        "min": 0,
        "max": 180,
        "step": 1,
        "marks": {0: '0°', 45: '45°', 90: '90°', 135: '135°', 180: '180°'}
    },
    "theta": {
        "tipo": "slider",
        "min": 0,
        "max": 180,
        "step": 1,
        "marks": {0: '0°', 45: '45°', 90: '90°', 135: '135°', 180: '180°'}
    },
    "t_hielo": {
        "tipo": "slider",
        "min": 0,
        "max": 0.03,
        "step": 0.001,
        "marks": {0: '0', 0.01: '0.01', 0.02: '0.02', 0.03: '0.03'}
    },
    "SALTO_PORCENTUAL": {
        "tipo": "slider",
        "min": 0,
        "max": 0.1,
        "step": 0.01,
        "marks": {0: '0%', 0.05: '5%', 0.1: '10%'}
    },
    "PASO_AFINADO": {
        "tipo": "slider",
        "min": 0,
        "max": 0.02,
        "step": 0.001,
        "marks": {0: '0%', 0.01: '1%', 0.02: '2%'}
    },
    "RELFLECHA_MAX_GUARDIA": {
        "tipo": "slider",
        "min": 0.5,
        "max": 1.1,
        "step": 0.01,
        "marks": {0.5: '50%', 0.75: '75%', 1.0: '100%', 1.1: '110%'}
    },
    "TENSION": {
        "tipo": "slider",
        "min": 0,
        "max": 1000,
        "step": 1,
        "marks": {13.2: '13.2', 33: '33', 66: '66', 132: '132', 220: '220', 330: '330', 500: '500', 600: '600', 700: '700', 800: '800', 900: '900', 1000: '1000'}
    },
    "Lk": {
        "tipo": "slider",
        "min": 0,
        "max": 8,
        "step": 0.1,
        "marks": {i*0.5: str(i*0.5) for i in range(17)}
    },
    "LONGITUD_MENSULA_MINIMA_CONDUCTOR": {
        "tipo": "slider",
        "min": 0,
        "max": 5,
        "step": 0.05,
        "marks": {i*0.5: str(i*0.5) for i in range(11)}
    },
    "LONGITUD_MENSULA_MINIMA_GUARDIA": {
        "tipo": "slider",
        "min": 0,
        "max": 5,
        "step": 0.05,
        "marks": {i*0.5: str(i*0.5) for i in range(11)}
    },
    "HADD": {
        "tipo": "slider",
        "min": 0,
        "max": 4,
        "step": 0.05,
        "marks": {i: str(i) for i in range(5)}
    },
    "HADD_HG": {
        "tipo": "slider",
        "min": 0,
        "max": 2,
        "step": 0.05,
        "marks": {i*0.5: str(i*0.5) for i in range(5)}
    },
    "HADD_LMEN": {
        "tipo": "slider",
        "min": 0,
        "max": 2,
        "step": 0.05,
        "marks": {i*0.2: str(round(i*0.2, 1)) for i in range(11)}
    },
    "D_fases_add": {
        "tipo": "slider",
        "min": -2,
        "max": 2,
        "step": 0.05,
        "marks": {-2: '-2', -1: '-1', 0: '0', 1: '1', 2: '2'}
    },
    "Altura_MSNM": {
        "tipo": "slider",
        "min": 0,
        "max": 6000,
        "step": 50,
        "marks": {i*500: str(i*500) for i in range(13)}
    },
    "ANCHO_CRUCETA": {
        "tipo": "slider",
        "min": 0,
        "max": 0.5,
        "step": 0.01,
        "marks": {i*0.1: str(round(i*0.1, 1)) for i in range(6)}
    },
    "HADD_ENTRE_AMARRES": {
        "tipo": "slider",
        "min": -2,
        "max": 2,
        "step": 0.05,
        "marks": {-2: '-2', -1: '-1', 0: '0', 1: '1', 2: '2'}
    },
    "CANT_HG": {
        "tipo": "slider",
        "min": 0,
        "max": 2,
        "step": 1,
        "marks": {0: '0', 1: '1', 2: '2'}
    },
    "ANG_APANTALLAMIENTO": {
        "tipo": "slider",
        "min": 0,
        "max": 45,
        "step": 1,
        "marks": {i: str(i) for i in range(0, 46, 15)}
    },
    "ALTURA_MINIMA_CABLE": {
        "tipo": "slider",
        "min": 0,
        "max": 10,
        "step": 0.1,
        "marks": {i: str(i) for i in range(0, 11, 2)}
    },
    "DIST_REPOSICIONAR_HG": {
        "tipo": "slider",
        "min": 0,
        "max": 1,
        "step": 0.05,
        "marks": {i*0.2: str(round(i*0.2, 1)) for i in range(6)}
    },
    "H_PIQANTERIOR": {
        "tipo": "slider_input",
        "min": -15,
        "max": 15,
        "step": 0.05,
        "marks": {i*5: str(i*5) for i in range(-3, 4)}
    },
    "H_PIQPOSTERIOR": {
        "tipo": "slider_input",
        "min": -15,
        "max": 15,
        "step": 0.05,
        "marks": {i*5: str(i*5) for i in range(-3, 4)}
    },
    
    # Selects (dropdowns)
    "TIPO_ESTRUCTURA": {
        "tipo": "select",
        "opciones": ["Suspensión Recta", "Suspensión angular", "Retención / Ret. Angular", "Terminal", "Especial"]
    },
    "doble_terna_una_terna_activa": {
        "tipo": "switch",
        "label": "Doble terna con una terna activa",
        "descripcion": "Anula cargas de la terna del lado X- en DME (solo Terminal Doble)",
        "default": False
    },
    "clase": {
        "tipo": "select",
        "opciones": ["A", "B", "BB", "C", "D", "E"]
    },
    "exposicion": {
        "tipo": "select",
        "opciones": ["B", "C", "D"]
    },
    "Zona_climatica": {
        "tipo": "select",
        "opciones": ["A", "B", "C", "D", "E"]
    },
    "FORZAR_ORIENTACION": {
        "tipo": "select",
        "opciones": ["Longitudinal", "Transversal", "No"]
    },
    "PRIORIDAD_DIMENSIONADO": {
        "tipo": "select",
        "opciones": ["altura_libre", "longitud_total"]
    },
    "Zona_estructura": {
        "tipo": "select",
        "opciones": ["Peatonal", "Rural", "Urbana", "Autopista", "Ferrocarril", "Línea Eléctrica"]
    },
    "METODO_ALTURA_MSNM": {
        "tipo": "select",
        "opciones": ["AEA 3%/300m"]
    },
    "DISPOSICION": {
        "tipo": "select",
        "opciones": ["triangular", "horizontal", "vertical"]
    },
    "TERNA": {
        "tipo": "select",
        "opciones": ["Simple", "Doble"]
    },
    "OBJ_CONDUCTOR": {
        "tipo": "select",
        "opciones": ["FlechaMin", "TiroMin"]
    },
    "OBJ_GUARDIA": {
        "tipo": "select",
        "opciones": ["FlechaMin", "TiroMin"]
    },
    
    # Switches (booleanos)
    "VANO_DESNIVELADO": {
        "tipo": "switch"
    },
    "AJUSTAR_POR_ALTURA_MSNM": {
        "tipo": "switch"
    },
    "HG_CENTRADO": {
        "tipo": "switch"
    },
    "AUTOAJUSTAR_LMENHG": {
        "tipo": "switch"
    },
    "RELFLECHA_SIN_VIENTO": {
        "tipo": "switch"
    },
    "REEMPLAZAR_TITULO_GRAFICO": {
        "tipo": "switch"
    },
    "MOSTRAR_C2": {
        "tipo": "switch"
    },
    "ADC_3D": {
        "tipo": "switch"
    },
    
    # PARÁMETROS DE FUNDACIÓN
    "metodo_fundacion": {
        "tipo": "select",
        "opciones": ["sulzberger", "mohr_pohl"]
    },
    "forma_fundacion": {
        "tipo": "select",
        "opciones": ["monobloque", "escalonada_recta", "escalonada_piramide"]
    },
    "tipo_base_fundacion": {
        "tipo": "select",
        "opciones": ["Rombica", "Cuadrada"]
    },
    "profundidad_propuesta": {
        "tipo": "input",
        "input_type": "number"
    },
    "longitud_colineal_inferior": {
        "tipo": "input",
        "input_type": "number"
    },
    "longitud_transversal_inferior": {
        "tipo": "input",
        "input_type": "number"
    },
    "coef_seguridad_volcamiento": {
        "tipo": "input",
        "input_type": "number"
    },
    "inclinacion_desplazamiento": {
        "tipo": "input",
        "input_type": "number"
    },
    "relacion_max_sin_armadura": {
        "tipo": "input",
        "input_type": "number"
    },
    "superacion_presion_admisible": {
        "tipo": "input",
        "input_type": "number"
    },
    "indice_compresibilidad": {
        "tipo": "input",
        "input_type": "number"
    },
    "presion_admisible": {
        "tipo": "input",
        "input_type": "number"
    },
    "angulo_tierra_gravante": {
        "tipo": "input",
        "input_type": "number"
    },
    "coef_friccion_terreno_hormigon": {
        "tipo": "input",
        "input_type": "number"
    },
    "densidad_hormigon": {
        "tipo": "input",
        "input_type": "number"
    },
    "densidad_tierra": {
        "tipo": "input",
        "input_type": "number"
    },
    "coef_aumento_cb_ct": {
        "tipo": "input",
        "input_type": "number"
    },
    "distancia_molde_hueco_lateral": {
        "tipo": "input",
        "input_type": "number"
    },
    "distancia_molde_hueco_fondo": {
        "tipo": "input",
        "input_type": "number"
    },
    "diametro_molde": {
        "tipo": "input",
        "input_type": "number"
    },
    "separacion_postes_cima": {
        "tipo": "input",
        "input_type": "number"
    },
    "pendiente_postes_multiples": {
        "tipo": "input",
        "input_type": "number"
    },
    "conicidad_poste": {
        "tipo": "input",
        "input_type": "number"
    },
    "incremento_calculo": {
        "tipo": "input",
        "input_type": "number"
    },
    
    # Inputs numéricos simples
    "L_vano": {
        "tipo": "input",
        "input_type": "number"
    },
    "A_cadena": {
        "tipo": "input",
        "input_type": "number"
    },
    "PCADENA": {
        "tipo": "input",
        "input_type": "number"
    },
    "PESTRUCTURA": {
        "tipo": "input",
        "input_type": "number"
    },
    "A_estr_trans": {
        "tipo": "input",
        "input_type": "number"
    },
    "A_estr_long": {
        "tipo": "input",
        "input_type": "number"
    },
    "Vmax": {
        "tipo": "input",
        "input_type": "number"
    },
    "Vmed": {
        "tipo": "input",
        "input_type": "number"
    },
    "Vtormenta": {
        "tipo": "input",
        "input_type": "number"
    },
    "Q": {
        "tipo": "input",
        "input_type": "number"
    },
    "Zco": {
        "tipo": "input",
        "input_type": "number"
    },
    "Zcg": {
        "tipo": "input",
        "input_type": "number"
    },
    "Zca": {
        "tipo": "input",
        "input_type": "number"
    },
    "Zes": {
        "tipo": "input",
        "input_type": "number"
    },
    "Cf_cable": {
        "tipo": "input",
        "input_type": "number"
    },
    "Cf_guardia": {
        "tipo": "input",
        "input_type": "number"
    },
    "Cf_cadena": {
        "tipo": "input",
        "input_type": "number"
    },
    "Cf_estructura": {
        "tipo": "input",
        "input_type": "number"
    },
    "FORZAR_N_POSTES": {
        "tipo": "input",
        "input_type": "number"
    },
    "ZOOM_CABEZAL": {
        "tipo": "input",
        "input_type": "number"
    },
    "Vn": {
        "tipo": "input",
        "input_type": "number"
    },
    
    # Inputs de texto
    "TITULO": {
        "tipo": "input",
        "input_type": "text"
    },
    "fecha_creacion": {
        "tipo": "input",
        "input_type": "text"
    },
    "version": {
        "tipo": "input",
        "input_type": "text"
    },
}


def obtener_config_control(nombre_parametro):
    """
    Obtiene la configuración de un control por nombre de parámetro.
    
    Args:
        nombre_parametro: Nombre del parámetro
        
    Returns:
        dict: Configuración del control o None si no existe
    """
    return CONTROLES_PARAMETROS.get(nombre_parametro)


def crear_slider(nombre, valor, config):
    """
    Crea un slider con la configuración especificada.
    
    Args:
        nombre: Nombre del parámetro
        valor: Valor actual
        config: Configuración del slider
        
    Returns:
        dcc.Slider configurado
    """
    from dash import dcc
    
    return dcc.Slider(
        id=f"slider-{nombre}",
        min=config["min"],
        max=config["max"],
        step=config["step"],
        value=valor,
        marks=config["marks"],
        tooltip={"placement": "bottom", "always_visible": True}
    )
