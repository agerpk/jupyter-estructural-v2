"""
Gestión centralizada de parámetros de estructura con metadatos y validación.
"""

import json
from typing import Dict, List, Tuple, Any, Optional
from config.parametros_controles import CONTROLES_PARAMETROS

class ParametrosManager:
    """Gestiona parámetros de estructura con metadatos y validación"""
    
    # Metadatos de parámetros con información para tabla
    PARAMETROS_METADATA = {
        # CONFIGURACIÓN GENERAL
        "TITULO": {
            "simbolo": "T",
            "unidad": "-",
            "descripcion": "Título de la estructura",
            "tipo": "str",
            "categoria": "General"
        },
        "TIPO_ESTRUCTURA": {
            "simbolo": "TE",
            "unidad": "-", 
            "descripcion": "Tipo de estructura",
            "tipo": "select",
            "categoria": "General"
        },
        "doble_terna_una_terna_activa": {
            "simbolo": "DT1A",
            "unidad": "-",
            "descripcion": "Doble terna con una terna activa (anula cargas lado X-)",
            "tipo": "bool",
            "categoria": "General"
        },
        "clase": {
            "simbolo": "CL",
            "unidad": "-",
            "descripcion": "Clase de línea según AEA",
            "tipo": "select",
            "categoria": "General"
        },
        "exposicion": {
            "simbolo": "EXP",
            "unidad": "-",
            "descripcion": "Exposición al viento",
            "tipo": "select",
            "categoria": "General"
        },
        "Zona_climatica": {
            "simbolo": "ZC",
            "unidad": "-",
            "descripcion": "Zona climática AEA",
            "tipo": "select",
            "categoria": "General"
        },
        "fecha_creacion": {
            "simbolo": "FC",
            "unidad": "-",
            "descripcion": "Fecha de creación",
            "tipo": "str",
            "categoria": "General"
        },
        "version": {
            "simbolo": "V",
            "unidad": "-",
            "descripcion": "Versión del archivo",
            "tipo": "str",
            "categoria": "General"
        },
        
        # CABLES Y CONDUCTORES
        "cable_conductor_id": {
            "simbolo": "CC",
            "unidad": "-",
            "descripcion": "Cable conductor",
            "tipo": "select",
            "categoria": "Cables"
        },
        "cable_guardia_id": {
            "simbolo": "CG1",
            "unidad": "-",
            "descripcion": "Cable guardia 1 (derecha, x+)",
            "tipo": "select",
            "categoria": "Cables"
        },
        "cable_guardia2_id": {
            "simbolo": "CG2",
            "unidad": "-",
            "descripcion": "Cable guardia 2 (izquierda, x-)",
            "tipo": "select",
            "categoria": "Cables"
        },
        
        # PARÁMETROS DE VIENTO Y CARGAS
        "Vmax": {
            "simbolo": "Vmax",
            "unidad": "m/s",
            "descripcion": "Velocidad máxima del viento",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Vmed": {
            "simbolo": "Vmed",
            "unidad": "m/s",
            "descripcion": "Velocidad media del viento",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Vtormenta": {
            "simbolo": "Vtor",
            "unidad": "m/s",
            "descripcion": "Velocidad de viento en tormenta",
            "tipo": "float",
            "categoria": "Línea"
        },
        "t_hielo": {
            "simbolo": "thielo",
            "unidad": "m",
            "descripcion": "Espesor de hielo",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Q": {
            "simbolo": "Q",
            "unidad": "kN/m²",
            "descripcion": "Presión dinámica del viento",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Zco": {
            "simbolo": "Zco",
            "unidad": "m",
            "descripcion": "Altura de referencia conductor",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Zcg": {
            "simbolo": "Zcg",
            "unidad": "m",
            "descripcion": "Altura de referencia guardia",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Zca": {
            "simbolo": "Zca",
            "unidad": "m",
            "descripcion": "Altura de referencia cadena",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Zes": {
            "simbolo": "Zes",
            "unidad": "m",
            "descripcion": "Altura de referencia estructura",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Cf_cable": {
            "simbolo": "Cf_c",
            "unidad": "-",
            "descripcion": "Coeficiente de forma cable",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Cf_guardia": {
            "simbolo": "Cf_g",
            "unidad": "-",
            "descripcion": "Coeficiente de forma guardia",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Cf_cadena": {
            "simbolo": "Cf_cad",
            "unidad": "-",
            "descripcion": "Coeficiente de forma cadena",
            "tipo": "float",
            "categoria": "Línea"
        },
        "Cf_estructura": {
            "simbolo": "Cf_e",
            "unidad": "-",
            "descripcion": "Coeficiente de forma estructura",
            "tipo": "float",
            "categoria": "Línea"
        },
        "A_cadena": {
            "simbolo": "Acad",
            "unidad": "m²",
            "descripcion": "Área expuesta cadena",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "PCADENA": {
            "simbolo": "Pcad",
            "unidad": "daN",
            "descripcion": "Peso de cadena",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "PESTRUCTURA": {
            "simbolo": "Pestr",
            "unidad": "daN",
            "descripcion": "Peso de estructura",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "A_estr_trans": {
            "simbolo": "Aet",
            "unidad": "m²",
            "descripcion": "Área estructura transversal",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "A_estr_long": {
            "simbolo": "Ael",
            "unidad": "m²",
            "descripcion": "Área estructura longitudinal",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        
        # CONFIGURACIÓN DISEÑO DE CABEZAL
        "TENSION": {
            "simbolo": "U",
            "unidad": "kV",
            "descripcion": "Tensión nominal",
            "tipo": "int",
            "categoria": "Cabezal"
        },
        "Zona_estructura": {
            "simbolo": "ZE",
            "unidad": "-",
            "descripcion": "Zona de estructura",
            "tipo": "select",
            "categoria": "Cabezal"
        },
        "Lk": {
            "simbolo": "Lk",
            "unidad": "m",
            "descripcion": "Longitud cadena oscilante",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "ANG_APANTALLAMIENTO": {
            "simbolo": "α",
            "unidad": "°",
            "descripcion": "Ángulo de apantallamiento",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "AJUSTAR_POR_ALTURA_MSNM": {
            "simbolo": "AMSNM",
            "unidad": "-",
            "descripcion": "Ajustar por alta montaña",
            "tipo": "bool",
            "categoria": "Cabezal"
        },
        "METODO_ALTURA_MSNM": {
            "simbolo": "MMSNM",
            "unidad": "-",
            "descripcion": "Método altura MSNM",
            "tipo": "select",
            "categoria": "Cabezal"
        },
        "Altura_MSNM": {
            "simbolo": "HMSNM",
            "unidad": "m",
            "descripcion": "Altura sobre nivel del mar",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "DISPOSICION": {
            "simbolo": "DISP",
            "unidad": "-",
            "descripcion": "Disposición de conductores",
            "tipo": "select",
            "categoria": "Cabezal"
        },
        "TERNA": {
            "simbolo": "TERNA",
            "unidad": "-",
            "descripcion": "Configuración de terna",
            "tipo": "select",
            "categoria": "Cabezal"
        },
        "CANT_HG": {
            "simbolo": "nHG",
            "unidad": "-",
            "descripcion": "Cantidad cables guardia",
            "tipo": "int",
            "categoria": "Cabezal"
        },
        "HG_CENTRADO": {
            "simbolo": "HGC",
            "unidad": "-",
            "descripcion": "Cable guardia centrado",
            "tipo": "bool",
            "categoria": "Cabezal"
        },
        "ALTURA_MINIMA_CABLE": {
            "simbolo": "Hmin",
            "unidad": "m",
            "descripcion": "Altura mínima de cable",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "LONGITUD_MENSULA_MINIMA_CONDUCTOR": {
            "simbolo": "LmenC",
            "unidad": "m",
            "descripcion": "Longitud mínima ménsula conductor",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "LONGITUD_MENSULA_MINIMA_GUARDIA": {
            "simbolo": "LmenG",
            "unidad": "m",
            "descripcion": "Longitud mínima ménsula guardia",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "HADD": {
            "simbolo": "Hadd",
            "unidad": "m",
            "descripcion": "Altura adicional base",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "HADD_ENTRE_AMARRES": {
            "simbolo": "HaddA",
            "unidad": "m",
            "descripcion": "Altura adicional entre amarres",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "HADD_HG": {
            "simbolo": "HaddHG",
            "unidad": "m",
            "descripcion": "Altura adicional cable guardia",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "HADD_LMEN": {
            "simbolo": "HaddL",
            "unidad": "m",
            "descripcion": "Altura adicional ménsula",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "D_fases_add": {
            "simbolo": "Dfadd",
            "unidad": "m",
            "descripcion": "Distancia adicional entre fases",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "ANCHO_CRUCETA": {
            "simbolo": "Ac",
            "unidad": "m",
            "descripcion": "Ancho de cruceta",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "AUTOAJUSTAR_LMENHG": {
            "simbolo": "AutoLHG",
            "unidad": "-",
            "descripcion": "Autoajuste ménsula guardia",
            "tipo": "bool",
            "categoria": "Cabezal"
        },
        "DIST_REPOSICIONAR_HG": {
            "simbolo": "DistHG",
            "unidad": "m",
            "descripcion": "Distancia reposición HG",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "defasaje_mensula_hielo": {
            "simbolo": "DEF_HIELO",
            "unidad": "-",
            "descripcion": "Activar defasaje de ménsula por hielo",
            "tipo": "bool",
            "categoria": "Cabezal"
        },
        "lmen_extra_hielo": {
            "simbolo": "L_HIELO",
            "unidad": "m",
            "descripcion": "Longitud extra para ménsula defasada",
            "tipo": "float",
            "categoria": "Cabezal"
        },
        "mensula_defasar": {
            "simbolo": "MEN_DEF",
            "unidad": "-",
            "descripcion": "Ménsula a defasar (primera/segunda/tercera)",
            "tipo": "select",
            "opciones": ["primera", "segunda", "tercera"],
            "categoria": "Cabezal"
        },
        
        # PARÁMETROS DE DISEÑO DE LÍNEA
        "L_vano": {
            "simbolo": "Lv",
            "unidad": "m",
            "descripcion": "Vano regulador de diseño",
            "tipo": "float",
            "categoria": "Línea"
        },
        "alpha": {
            "simbolo": "α",
            "unidad": "°",
            "descripcion": "Ángulo de quiebre máximo",
            "tipo": "float",
            "categoria": "Línea"
        },
        "theta": {
            "simbolo": "θ",
            "unidad": "°",
            "descripcion": "Ángulo de viento oblicuo",
            "tipo": "float",
            "categoria": "Línea"
        },
        
        # CONFIGURACIÓN SELECCIÓN DE POSTES
        "FORZAR_N_POSTES": {
            "simbolo": "nP",
            "unidad": "-",
            "descripcion": "Número de postes forzado",
            "tipo": "int",
            "categoria": "Postes"
        },
        "FORZAR_ORIENTACION": {
            "simbolo": "Orient",
            "unidad": "-",
            "descripcion": "Orientación forzada",
            "tipo": "select",
            "categoria": "Postes"
        },
        "PRIORIDAD_DIMENSIONADO": {
            "simbolo": "PrioDim",
            "unidad": "-",
            "descripcion": "Prioridad de dimensionado",
            "tipo": "select",
            "categoria": "Postes"
        },
        
        # CONFIGURACIÓN MECÁNICA
        "VANO_DESNIVELADO": {
            "simbolo": "VD",
            "unidad": "-",
            "descripcion": "Vano desnivelado",
            "tipo": "bool",
            "categoria": "Mecánica"
        },
        "H_PIQANTERIOR": {
            "simbolo": "Hant",
            "unidad": "m",
            "descripcion": "Altura piquete anterior",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "H_PIQPOSTERIOR": {
            "simbolo": "Hpost",
            "unidad": "m",
            "descripcion": "Altura piquete posterior",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "OBJ_CONDUCTOR": {
            "simbolo": "ObjC",
            "unidad": "-",
            "descripcion": "Objetivo conductor",
            "tipo": "select",
            "categoria": "Mecánica"
        },
        "OBJ_GUARDIA": {
            "simbolo": "ObjG",
            "unidad": "-",
            "descripcion": "Objetivo guardia",
            "tipo": "select",
            "categoria": "Mecánica"
        },
        "SALTO_PORCENTUAL": {
            "simbolo": "Salto",
            "unidad": "-",
            "descripcion": "Salto porcentual optimización",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "PASO_AFINADO": {
            "simbolo": "Paso",
            "unidad": "-",
            "descripcion": "Paso afinado optimización",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "RELFLECHA_MAX_GUARDIA": {
            "simbolo": "RFG",
            "unidad": "-",
            "descripcion": "Relación flecha máx guardia",
            "tipo": "float",
            "categoria": "Mecánica"
        },
        "RELFLECHA_SIN_VIENTO": {
            "simbolo": "RFSV",
            "unidad": "-",
            "descripcion": "Relación flecha sin viento",
            "tipo": "bool",
            "categoria": "Mecánica"
        },
        "Vn": {
            "simbolo": "Vn",
            "unidad": "kV",
            "descripcion": "Tensión nominal línea",
            "tipo": "float",
            "categoria": "General"
        },
        
        # CONFIGURACIÓN GRÁFICOS
        "ZOOM_CABEZAL": {
            "simbolo": "Zoom",
            "unidad": "-",
            "descripcion": "Zoom del cabezal",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "REEMPLAZAR_TITULO_GRAFICO": {
            "simbolo": "ReplTit",
            "unidad": "-",
            "descripcion": "Reemplazar título gráfico",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        "ADC_3D": {
            "simbolo": "3D",
            "unidad": "-",
            "descripcion": "Árboles de carga en 3D",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        "MOSTRAR_C2": {
            "simbolo": "C2",
            "unidad": "-",
            "descripcion": "Mostrar C2",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        
        # PARÁMETROS GRÁFICOS - COLORES
        "parametros_graficos.colores.conductor": {
            "simbolo": "Col_C",
            "unidad": "-",
            "descripcion": "Color conductor (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.guardia": {
            "simbolo": "Col_G",
            "unidad": "-",
            "descripcion": "Color guardia (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.poste": {
            "simbolo": "Col_P",
            "unidad": "-",
            "descripcion": "Color poste (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.cadena": {
            "simbolo": "Col_Cad",
            "unidad": "-",
            "descripcion": "Color cadena (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.conductor_end": {
            "simbolo": "Col_CE",
            "unidad": "-",
            "descripcion": "Color extremo conductor (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.circulo": {
            "simbolo": "Col_Cir",
            "unidad": "-",
            "descripcion": "Color círculo (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.apantallamiento": {
            "simbolo": "Col_A",
            "unidad": "-",
            "descripcion": "Color apantallamiento (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.texto_verde": {
            "simbolo": "Col_TV",
            "unidad": "-",
            "descripcion": "Color texto verde (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.dhg_circulo": {
            "simbolo": "Col_DHG",
            "unidad": "-",
            "descripcion": "Color círculo Dhg (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.terreno": {
            "simbolo": "Col_T",
            "unidad": "-",
            "descripcion": "Color terreno (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        "parametros_graficos.colores.area_s_estructura": {
            "simbolo": "Col_AS",
            "unidad": "-",
            "descripcion": "Color área s_estructura (hex)",
            "tipo": "str",
            "categoria": "Gráficos"
        },
        
        # PARÁMETROS GRÁFICOS - CONTROLES
        "parametros_graficos.controles.declinar_todos": {
            "simbolo": "Dec_T",
            "unidad": "-",
            "descripcion": "Declinar todos los conductores",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.dibujar_solo_circulos_declinados_trayectoria": {
            "simbolo": "Cir_Tray",
            "unidad": "-",
            "descripcion": "Dibujar solo círculos declinados trayectoria",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.dibujar_circulos_s_estructura": {
            "simbolo": "Cir_S",
            "unidad": "-",
            "descripcion": "Dibujar círculos s_estructura",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.dibujar_areas_s_estructura": {
            "simbolo": "Area_S",
            "unidad": "-",
            "descripcion": "Dibujar áreas s_estructura",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.dibujar_circulos_d_fases": {
            "simbolo": "Cir_D",
            "unidad": "-",
            "descripcion": "Dibujar círculos D_fases",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.dibujar_circulos_dhg": {
            "simbolo": "Cir_DHG",
            "unidad": "-",
            "descripcion": "Dibujar círculos Dhg",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.linewidth_cadena": {
            "simbolo": "LW_Cad",
            "unidad": "px",
            "descripcion": "Ancho línea cadena",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.linewidth_estructura": {
            "simbolo": "LW_Est",
            "unidad": "px",
            "descripcion": "Ancho línea estructura",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.linewidth_cruceta": {
            "simbolo": "LW_Cru",
            "unidad": "px",
            "descripcion": "Ancho línea cruceta",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.linewidth_circulo": {
            "simbolo": "LW_Cir",
            "unidad": "px",
            "descripcion": "Ancho línea círculo",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.alpha_cruceta": {
            "simbolo": "α_Cru",
            "unidad": "-",
            "descripcion": "Transparencia cruceta (0-1)",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.alpha_circulo": {
            "simbolo": "α_Cir",
            "unidad": "-",
            "descripcion": "Transparencia círculo (0-1)",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.alpha_circulo_trayectoria": {
            "simbolo": "α_CirT",
            "unidad": "-",
            "descripcion": "Transparencia círculo trayectoria (0-1)",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.alpha_apantallamiento": {
            "simbolo": "α_Apan",
            "unidad": "-",
            "descripcion": "Transparencia apantallamiento (0-1)",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.alpha_area_s_estructura": {
            "simbolo": "α_AS",
            "unidad": "-",
            "descripcion": "Transparencia área s_estructura (0-1)",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.size_nodo_conductor": {
            "simbolo": "Sz_NC",
            "unidad": "px",
            "descripcion": "Tamaño nodo conductor",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.size_nodo_guardia": {
            "simbolo": "Sz_NG",
            "unidad": "px",
            "descripcion": "Tamaño nodo guardia",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.size_nodo_estructura": {
            "simbolo": "Sz_NE",
            "unidad": "px",
            "descripcion": "Tamaño nodo estructura",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.size_conductor_end": {
            "simbolo": "Sz_CE",
            "unidad": "px",
            "descripcion": "Tamaño extremo conductor",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.zoom_cabezal_default": {
            "simbolo": "Zm_Cab",
            "unidad": "-",
            "descripcion": "Zoom cabezal por defecto",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.zoom_estructura_default": {
            "simbolo": "Zm_Est",
            "unidad": "-",
            "descripcion": "Zoom estructura por defecto",
            "tipo": "float",
            "categoria": "Gráficos"
        },
        "parametros_graficos.controles.mostrar_c2": {
            "simbolo": "MC2",
            "unidad": "-",
            "descripcion": "Mostrar hipótesis C2",
            "tipo": "bool",
            "categoria": "Gráficos"
        },
        
        # PARÁMETROS DE FUNDACIÓN
        "metodo_fundacion": {
            "simbolo": "MF",
            "unidad": "-",
            "descripcion": "Método de cálculo de fundación",
            "tipo": "select",
            "categoria": "Fundación"
        },
        "forma_fundacion": {
            "simbolo": "FF",
            "unidad": "-",
            "descripcion": "Forma de la fundación",
            "tipo": "select",
            "categoria": "Fundación"
        },
        "tipo_base_fundacion": {
            "simbolo": "TB",
            "unidad": "-",
            "descripcion": "Tipo de base de fundación",
            "tipo": "select",
            "categoria": "Fundación"
        },
        "profundidad_propuesta": {
            "simbolo": "tin",
            "unidad": "m",
            "descripcion": "Profundidad propuesta",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "longitud_colineal_inferior": {
            "simbolo": "ain",
            "unidad": "m",
            "descripcion": "Longitud colineal con línea, inferior",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "longitud_transversal_inferior": {
            "simbolo": "bin",
            "unidad": "m",
            "descripcion": "Longitud transversal a línea, inferior",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "coef_seguridad_volcamiento": {
            "simbolo": "F.S",
            "unidad": "-",
            "descripcion": "Coeficiente de seguridad al volcamiento",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "inclinacion_desplazamiento": {
            "simbolo": "tg α adm",
            "unidad": "-",
            "descripcion": "Inclinación por desplazamiento de base",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "relacion_max_sin_armadura": {
            "simbolo": "t/he",
            "unidad": "-",
            "descripcion": "Relación máx. sin armadura",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "superacion_presion_admisible": {
            "simbolo": "σmax/σadm",
            "unidad": "-",
            "descripcion": "Superación de la presión admisible",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "indice_compresibilidad": {
            "simbolo": "C",
            "unidad": "kg/m³",
            "descripcion": "Índice de compresibilidad C, al metro",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "presion_admisible": {
            "simbolo": "σadm",
            "unidad": "kg/m²",
            "descripcion": "Presión admisible",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "angulo_tierra_gravante": {
            "simbolo": "β",
            "unidad": "°",
            "descripcion": "Ángulo de tierra gravante",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "coef_friccion_terreno_hormigon": {
            "simbolo": "μ",
            "unidad": "-",
            "descripcion": "Coeficiente de fricción terreno-hormigón",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "densidad_hormigon": {
            "simbolo": "γhor",
            "unidad": "kg/m³",
            "descripcion": "Densidad del hormigón",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "densidad_tierra": {
            "simbolo": "γtierra",
            "unidad": "kg/m³",
            "descripcion": "Densidad tierra",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "coef_aumento_cb_ct": {
            "simbolo": "cacb",
            "unidad": "-",
            "descripcion": "Coeficiente aumento Cb respecto Ct",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "distancia_molde_hueco_lateral": {
            "simbolo": "dml",
            "unidad": "m",
            "descripcion": "Distancia del molde p/ hueco al lateral",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "distancia_molde_hueco_fondo": {
            "simbolo": "dmf",
            "unidad": "m",
            "descripcion": "Distancia del molde p/ hueco al fondo",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "diametro_molde": {
            "simbolo": "dmol",
            "unidad": "m",
            "descripcion": "Diámetro del molde",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "separacion_postes_cima": {
            "simbolo": "spc",
            "unidad": "m",
            "descripcion": "Separación entre postes en cima",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "pendiente_postes_multiples": {
            "simbolo": "pp",
            "unidad": "%",
            "descripcion": "Pendiente de postes dobles, triples entre sí",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "conicidad_poste": {
            "simbolo": "con",
            "unidad": "%",
            "descripcion": "Conicidad poste",
            "tipo": "float",
            "categoria": "Fundación"
        },
        "incremento_calculo": {
            "simbolo": "incremento",
            "unidad": "m",
            "descripcion": "Incremento para iteraciones de cálculo",
            "tipo": "float",
            "categoria": "Fundación"
        },
        
        # ANÁLISIS ESTÁTICO DE ESFUERZOS (AEE)
        "AnalisisEstaticoEsfuerzos.ACTIVAR_AEE": {
            "simbolo": "AEE_ON",
            "unidad": "-",
            "descripcion": "Activar módulo AEE",
            "tipo": "bool",
            "categoria": "AEE"
        },
        "AnalisisEstaticoEsfuerzos.GRAFICOS_3D_AEE": {
            "simbolo": "AEE_3D",
            "unidad": "-",
            "descripcion": "Gráficos 3D (False=2D)",
            "tipo": "bool",
            "categoria": "AEE"
        },
        "AnalisisEstaticoEsfuerzos.n_segmentar_conexion_corta": {
            "simbolo": "n_corta",
            "unidad": "-",
            "descripcion": "Elementos conexión corta",
            "tipo": "int",
            "categoria": "AEE"
        },
        "AnalisisEstaticoEsfuerzos.n_segmentar_conexion_larga": {
            "simbolo": "n_larga",
            "unidad": "-",
            "descripcion": "Elementos conexión larga",
            "tipo": "int",
            "categoria": "AEE"
        },
        "AnalisisEstaticoEsfuerzos.percentil_separacion_corta_larga": {
            "simbolo": "p_sep",
            "unidad": "-",
            "descripcion": "Percentil separación corta/larga",
            "tipo": "int",
            "categoria": "AEE"
        },
        "AnalisisEstaticoEsfuerzos.DIAGRAMAS_ACTIVOS.MQNT": {
            "simbolo": "MQNT",
            "unidad": "-",
            "descripcion": "Diagrama MQNT",
            "tipo": "bool",
            "categoria": "AEE"
        },
        "AnalisisEstaticoEsfuerzos.DIAGRAMAS_ACTIVOS.MRT": {
            "simbolo": "MRT",
            "unidad": "-",
            "descripcion": "Diagrama MRT",
            "tipo": "bool",
            "categoria": "AEE"
        },
        "AnalisisEstaticoEsfuerzos.DIAGRAMAS_ACTIVOS.MFE": {
            "simbolo": "MFE",
            "unidad": "-",
            "descripcion": "Diagrama MFE",
            "tipo": "bool",
            "categoria": "AEE"
        },
        
        # PARÁMETROS DE COSTEO
        "costeo.postes.coef_a": {
            "simbolo": "Ca",
            "unidad": "UM/kg",
            "descripcion": "Coeficiente A (por kg peso)",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.postes.coef_b": {
            "simbolo": "Cb",
            "unidad": "UM/m",
            "descripcion": "Coeficiente B (por m altura)",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.postes.coef_c": {
            "simbolo": "Cc",
            "unidad": "UM",
            "descripcion": "Coeficiente C (fijo)",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.accesorios.vinculos": {
            "simbolo": "Pv",
            "unidad": "UM/u",
            "descripcion": "Precio vínculos",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.accesorios.crucetas": {
            "simbolo": "Pc",
            "unidad": "UM/u",
            "descripcion": "Precio crucetas",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.accesorios.mensulas": {
            "simbolo": "Pm",
            "unidad": "UM/u",
            "descripcion": "Precio ménsulas",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.fundaciones.precio_m3_hormigon": {
            "simbolo": "Ph",
            "unidad": "UM/m³",
            "descripcion": "Precio hormigón por m³",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.fundaciones.factor_hierro": {
            "simbolo": "Fh",
            "unidad": "-",
            "descripcion": "Factor hierro",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.montaje.precio_por_estructura": {
            "simbolo": "Pe",
            "unidad": "UM",
            "descripcion": "Precio por estructura",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.montaje.factor_terreno": {
            "simbolo": "Ft",
            "unidad": "-",
            "descripcion": "Factor terreno",
            "tipo": "float",
            "categoria": "Costeo"
        },
        "costeo.adicional_estructura": {
            "simbolo": "Pad",
            "unidad": "UM",
            "descripcion": "Adicional por estructura",
            "tipo": "float",
            "categoria": "Costeo"
        }
    }
    
    @classmethod
    def obtener_metadatos_parametros(cls) -> Dict[str, Dict]:
        """Obtiene metadatos de todos los parámetros"""
        return cls.PARAMETROS_METADATA
    
    @classmethod
    def estructura_a_tabla(cls, estructura: Dict) -> List[Dict]:
        """Convierte estructura JSON a formato tabla
        
        SIEMPRE muestra todos los parámetros definidos en PARAMETROS_METADATA,
        usando valores de estructura si existen, o valores por defecto si no.
        """
        from pathlib import Path
        import json
        
        # Cargar plantilla para obtener valores por defecto
        plantilla_path = Path("data/plantilla.estructura.json")
        plantilla = {}
        if plantilla_path.exists():
            try:
                with open(plantilla_path, "r", encoding="utf-8") as f:
                    plantilla = json.load(f)
            except:
                pass
        
        tabla_data = []
        titulo_fila = None
        
        # Procesar TODOS los parámetros de PARAMETROS_METADATA
        for parametro, metadata in cls.PARAMETROS_METADATA.items():
            # Saltar parámetros anidados (se procesan después)
            if "." in parametro:
                continue
            
            # Obtener valor: primero de estructura, luego de plantilla, luego por defecto
            if parametro in estructura:
                valor = estructura[parametro]
            elif parametro in plantilla:
                valor = plantilla[parametro]
            else:
                valor = cls._valor_por_defecto(metadata["tipo"])
            
            fila = {
                "categoria": metadata["categoria"],
                "parametro": parametro,
                "simbolo": metadata["simbolo"],
                "valor": valor,
                "unidad": metadata["unidad"],
                "descripcion": metadata["descripcion"],
                "tipo": metadata["tipo"]
            }
            
            # Separar TITULO para ponerlo primero
            if parametro == "TITULO":
                titulo_fila = fila
            else:
                tabla_data.append(fila)
        
        # Procesar parámetros anidados de parametros_graficos
        graficos_filas = []
        param_graficos = estructura.get("parametros_graficos", {})
        plantilla_graficos = plantilla.get("parametros_graficos", {})
        
        # Procesar TODOS los parámetros gráficos de PARAMETROS_METADATA
        for parametro, metadata in cls.PARAMETROS_METADATA.items():
            if parametro.startswith("parametros_graficos."):
                parts = parametro.split(".")
                if len(parts) == 3:
                    categoria = parts[1]  # colores o controles
                    param_name = parts[2]
                    
                    # Obtener valor: estructura -> plantilla -> por defecto
                    if categoria in param_graficos and param_name in param_graficos[categoria]:
                        valor = param_graficos[categoria][param_name]
                    elif categoria in plantilla_graficos and param_name in plantilla_graficos[categoria]:
                        valor = plantilla_graficos[categoria][param_name]
                    else:
                        valor = cls._valor_por_defecto(metadata["tipo"])
                    
                    graficos_filas.append({
                        "categoria": metadata["categoria"],
                        "parametro": parametro,
                        "simbolo": metadata["simbolo"],
                        "valor": valor,
                        "unidad": metadata["unidad"],
                        "descripcion": metadata["descripcion"],
                        "tipo": metadata["tipo"]
                    })
        
        # Procesar parámetros anidados de costeo
        costeo_fundacion_filas = []
        costeo_estructura = estructura.get("costeo", {})
        costeo_plantilla = plantilla.get("costeo", {})
        
        # Procesar TODOS los parámetros de costeo de PARAMETROS_METADATA
        for parametro, metadata in cls.PARAMETROS_METADATA.items():
            if parametro.startswith("costeo."):
                parts = parametro.split(".")
                if len(parts) == 3:  # costeo.categoria.parametro
                    categoria = parts[1]
                    param_name = parts[2]
                    
                    # Obtener valor: estructura -> plantilla -> por defecto
                    if categoria in costeo_estructura and param_name in costeo_estructura[categoria]:
                        valor = costeo_estructura[categoria][param_name]
                    elif categoria in costeo_plantilla and param_name in costeo_plantilla[categoria]:
                        valor = costeo_plantilla[categoria][param_name]
                    else:
                        valor = cls._valor_por_defecto(metadata["tipo"])
                    
                    costeo_fundacion_filas.append({
                        "categoria": metadata["categoria"],
                        "parametro": parametro,
                        "simbolo": metadata["simbolo"],
                        "valor": valor,
                        "unidad": metadata["unidad"],
                        "descripcion": metadata["descripcion"],
                        "tipo": metadata["tipo"]
                    })
                elif len(parts) == 2 and parts[1] == "adicional_estructura":
                    # Obtener valor: estructura -> plantilla -> por defecto
                    if "adicional_estructura" in costeo_estructura:
                        valor = costeo_estructura["adicional_estructura"]
                    elif "adicional_estructura" in costeo_plantilla:
                        valor = costeo_plantilla["adicional_estructura"]
                    else:
                        valor = cls._valor_por_defecto(metadata["tipo"])
                    
                    costeo_fundacion_filas.append({
                        "categoria": metadata["categoria"],
                        "parametro": parametro,
                        "simbolo": metadata["simbolo"],
                        "valor": valor,
                        "unidad": metadata["unidad"],
                        "descripcion": metadata["descripcion"],
                        "tipo": metadata["tipo"]
                    })
        
        # Procesar parámetros anidados de AEE
        aee_filas = []
        aee_estructura = estructura.get("AnalisisEstaticoEsfuerzos", {})
        aee_plantilla = plantilla.get("AnalisisEstaticoEsfuerzos", {})
        
        for parametro, metadata in cls.PARAMETROS_METADATA.items():
            if parametro.startswith("AnalisisEstaticoEsfuerzos."):
                parts = parametro.split(".")
                if len(parts) == 2:  # AnalisisEstaticoEsfuerzos.parametro
                    param_name = parts[1]
                    if param_name in aee_estructura:
                        valor = aee_estructura[param_name]
                    elif param_name in aee_plantilla:
                        valor = aee_plantilla[param_name]
                    else:
                        valor = cls._valor_por_defecto(metadata["tipo"])
                    
                    aee_filas.append({
                        "categoria": metadata["categoria"],
                        "parametro": parametro,
                        "simbolo": metadata["simbolo"],
                        "valor": valor,
                        "unidad": metadata["unidad"],
                        "descripcion": metadata["descripcion"],
                        "tipo": metadata["tipo"]
                    })
                elif len(parts) == 3:  # AnalisisEstaticoEsfuerzos.DIAGRAMAS_ACTIVOS.MQNT
                    categoria_aee = parts[1]
                    param_name = parts[2]
                    if categoria_aee in aee_estructura and param_name in aee_estructura[categoria_aee]:
                        valor = aee_estructura[categoria_aee][param_name]
                    elif categoria_aee in aee_plantilla and param_name in aee_plantilla[categoria_aee]:
                        valor = aee_plantilla[categoria_aee][param_name]
                    else:
                        valor = cls._valor_por_defecto(metadata["tipo"])
                    
                    aee_filas.append({
                        "categoria": metadata["categoria"],
                        "parametro": parametro,
                        "simbolo": metadata["simbolo"],
                        "valor": valor,
                        "unidad": metadata["unidad"],
                        "descripcion": metadata["descripcion"],
                        "tipo": metadata["tipo"]
                    })
        
        # Ordenar por categoría, moviendo Costeo y Fundación al final
        orden_categorias = {"Costeo": 999, "Fundación": 998}
        tabla_data.sort(key=lambda x: (orden_categorias.get(x["categoria"], 0), x["categoria"], x["parametro"]))
        
        # Construir resultado final: TITULO primero, luego resto, luego Gráficos, luego AEE, luego Costeo/Fundación
        resultado = []
        if titulo_fila:
            resultado.append(titulo_fila)
        resultado.extend(tabla_data)
        resultado.extend(graficos_filas)
        resultado.extend(aee_filas)
        resultado.extend(costeo_fundacion_filas)
        
        return resultado
    
    @classmethod
    def tabla_a_estructura(cls, tabla_data: List[Dict]) -> Dict:
        """Convierte datos de tabla a estructura JSON"""
        estructura = {}
        costeo = {"postes": {}, "accesorios": {}, "fundaciones": {}, "montaje": {}}
        parametros_graficos = {"colores": {}, "controles": {}}
        aee = {"DIAGRAMAS_ACTIVOS": {}}
        
        for fila in tabla_data:
            parametro = fila["parametro"]
            valor = fila["valor"]
            
            # Convertir valor según tipo
            if parametro in cls.PARAMETROS_METADATA:
                tipo = cls.PARAMETROS_METADATA[parametro]["tipo"]
                valor = cls._convertir_valor(valor, tipo)
            
            # Manejar parámetros anidados de parametros_graficos
            if parametro.startswith("parametros_graficos."):
                parts = parametro.split(".")
                if len(parts) == 3:  # parametros_graficos.categoria.parametro
                    categoria = parts[1]  # colores o controles
                    param_name = parts[2]
                    if categoria in parametros_graficos:
                        parametros_graficos[categoria][param_name] = valor
            # Manejar parámetros anidados de costeo
            elif parametro.startswith("costeo."):
                parts = parametro.split(".")
                if len(parts) == 3:  # costeo.categoria.parametro
                    categoria = parts[1]
                    param_name = parts[2]
                    if categoria in costeo:
                        costeo[categoria][param_name] = valor
                elif len(parts) == 2 and parts[1] == "adicional_estructura":
                    costeo["adicional_estructura"] = valor
            # Manejar parámetros anidados de AEE
            elif parametro.startswith("AnalisisEstaticoEsfuerzos."):
                parts = parametro.split(".")
                if len(parts) == 2:  # AnalisisEstaticoEsfuerzos.parametro
                    param_name = parts[1]
                    aee[param_name] = valor
                elif len(parts) == 3:  # AnalisisEstaticoEsfuerzos.DIAGRAMAS_ACTIVOS.MQNT
                    categoria_aee = parts[1]
                    param_name = parts[2]
                    if categoria_aee not in aee:
                        aee[categoria_aee] = {}
                    aee[categoria_aee][param_name] = valor
            else:
                estructura[parametro] = valor
        
        # Agregar parametros_graficos si tiene datos
        if any(parametros_graficos[cat] for cat in ["colores", "controles"]):
            estructura["parametros_graficos"] = parametros_graficos
        
        # Agregar costeo si tiene datos
        if any(costeo[cat] for cat in ["postes", "accesorios", "fundaciones", "montaje"]) or "adicional_estructura" in costeo:
            estructura["costeo"] = costeo
        
        # Agregar AEE si tiene datos
        if len(aee) > 1 or (len(aee) == 1 and "DIAGRAMAS_ACTIVOS" not in aee):  # Más que solo DIAGRAMAS_ACTIVOS vacío
            estructura["AnalisisEstaticoEsfuerzos"] = aee
        
        return estructura
    
    @classmethod
    def _convertir_valor(cls, valor: Any, tipo: str) -> Any:
        """Convierte valor al tipo correcto"""
        if valor == "" or valor is None:
            return cls._valor_por_defecto(tipo)
        
        try:
            if tipo == "int":
                return int(float(valor))
            elif tipo == "float":
                return float(valor)
            elif tipo == "bool":
                if isinstance(valor, bool):
                    return valor
                if isinstance(valor, str):
                    return valor.lower() in ["true", "1", "yes", "on"]
                return bool(valor)
            else:  # str, select
                return str(valor)
        except (ValueError, TypeError):
            return cls._valor_por_defecto(tipo)
    
    @classmethod
    def _valor_por_defecto(cls, tipo: str) -> Any:
        """Obtiene valor por defecto según tipo"""
        if tipo == "int":
            return 0
        elif tipo == "float":
            return 0.0
        elif tipo == "bool":
            return False
        else:  # str, select
            return ""
    
    @classmethod
    def validar_valor(cls, parametro: str, valor: Any) -> Tuple[bool, str]:
        """Valida valor de parámetro"""
        if parametro not in cls.PARAMETROS_METADATA:
            return True, ""
        
        metadata = cls.PARAMETROS_METADATA[parametro]
        tipo = metadata["tipo"]
        
        # Validar tipo
        try:
            valor_convertido = cls._convertir_valor(valor, tipo)
        except:
            return False, f"Valor inválido para tipo {tipo}"
        
        # Validar opciones para select
        if tipo == "select" and parametro in CONTROLES_PARAMETROS:
            config = CONTROLES_PARAMETROS[parametro]
            if "opciones" in config and valor not in config["opciones"]:
                return False, f"Valor debe ser uno de: {', '.join(config['opciones'])}"
        
        # Validar rangos para numéricos
        if tipo in ["int", "float"] and parametro in CONTROLES_PARAMETROS:
            config = CONTROLES_PARAMETROS[parametro]
            # Excluir D_fases_add de validación de rangos
            if parametro != "D_fases_add":
                if "min" in config and valor_convertido < config["min"]:
                    return False, f"Valor debe ser >= {config['min']}"
                if "max" in config and valor_convertido > config["max"]:
                    return False, f"Valor debe ser <= {config['max']}"
        
        return True, ""
    
    @classmethod
    def obtener_opciones_parametro(cls, parametro: str) -> Optional[List[str]]:
        """Obtiene opciones para parámetro tipo select"""
        # Primero buscar en PARAMETROS_METADATA
        if parametro in cls.PARAMETROS_METADATA:
            metadata = cls.PARAMETROS_METADATA[parametro]
            if metadata.get("tipo") == "select" and "opciones" in metadata:
                return metadata["opciones"]
        
        # Fallback a CONTROLES_PARAMETROS
        if parametro in CONTROLES_PARAMETROS:
            config = CONTROLES_PARAMETROS[parametro]
            if config.get("tipo") == "select":
                return config.get("opciones", [])
        
        return None
    
    @classmethod
    def obtener_rango_parametro(cls, parametro: str) -> Tuple[Optional[float], Optional[float]]:
        """Obtiene rango mínimo y máximo para parámetro numérico"""
        if parametro in CONTROLES_PARAMETROS:
            config = CONTROLES_PARAMETROS[parametro]
            min_val = config.get("min")
            max_val = config.get("max")
            return min_val, max_val
        return None, None
    
    @classmethod
    def obtener_parametros_por_categoria(cls) -> Dict[str, List[str]]:
        """Obtiene parámetros agrupados por categoría"""
        categorias = {}
        
        for parametro, metadata in cls.PARAMETROS_METADATA.items():
            categoria = metadata["categoria"]
            if categoria not in categorias:
                categorias[categoria] = []
            categorias[categoria].append(parametro)
        
        return categorias