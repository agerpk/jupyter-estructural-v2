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
        }
    }
    
    @classmethod
    def obtener_metadatos_parametros(cls) -> Dict[str, Dict]:
        """Obtiene metadatos de todos los parámetros"""
        return cls.PARAMETROS_METADATA
    
    @classmethod
    def estructura_a_tabla(cls, estructura: Dict) -> List[Dict]:
        """Convierte estructura JSON a formato tabla"""
        tabla_data = []
        
        for parametro, valor in estructura.items():
            if parametro in cls.PARAMETROS_METADATA:
                metadata = cls.PARAMETROS_METADATA[parametro]
                tabla_data.append({
                    "parametro": parametro,
                    "simbolo": metadata["simbolo"],
                    "valor": valor,
                    "unidad": metadata["unidad"],
                    "descripcion": metadata["descripcion"],
                    "tipo": metadata["tipo"],
                    "categoria": metadata["categoria"]
                })
        
        # Ordenar por categoría y luego por parámetro
        tabla_data.sort(key=lambda x: (x["categoria"], x["parametro"]))
        return tabla_data
    
    @classmethod
    def tabla_a_estructura(cls, tabla_data: List[Dict]) -> Dict:
        """Convierte datos de tabla a estructura JSON"""
        estructura = {}
        
        for fila in tabla_data:
            parametro = fila["parametro"]
            valor = fila["valor"]
            
            # Convertir valor según tipo
            if parametro in cls.PARAMETROS_METADATA:
                tipo = cls.PARAMETROS_METADATA[parametro]["tipo"]
                valor = cls._convertir_valor(valor, tipo)
            
            estructura[parametro] = valor
        
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
                return str(valor).lower() in ["true", "1", "yes", "on"]
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
            if "min" in config and valor_convertido < config["min"]:
                return False, f"Valor debe ser >= {config['min']}"
            if "max" in config and valor_convertido > config["max"]:
                return False, f"Valor debe ser <= {config['max']}"
        
        return True, ""
    
    @classmethod
    def obtener_opciones_parametro(cls, parametro: str) -> Optional[List[str]]:
        """Obtiene opciones para parámetro tipo select"""
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