"""
Validadores específicos para parámetros de estructura.
"""

from typing import Any, Tuple, List, Optional
import re

class ValidadoresParametros:
    """Validadores específicos para diferentes tipos de parámetros"""
    
    @staticmethod
    def validar_entero(valor: Any, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Tuple[bool, str]:
        """Valida valor entero con rangos opcionales"""
        try:
            val_int = int(float(valor))
            
            if min_val is not None and val_int < min_val:
                return False, f"Debe ser >= {min_val}"
            
            if max_val is not None and val_int > max_val:
                return False, f"Debe ser <= {max_val}"
            
            return True, ""
        except (ValueError, TypeError):
            return False, "Debe ser un número entero"
    
    @staticmethod
    def validar_flotante(valor: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> Tuple[bool, str]:
        """Valida valor flotante con rangos opcionales"""
        try:
            val_float = float(valor)
            
            if min_val is not None and val_float < min_val:
                return False, f"Debe ser >= {min_val}"
            
            if max_val is not None and val_float > max_val:
                return False, f"Debe ser <= {max_val}"
            
            return True, ""
        except (ValueError, TypeError):
            return False, "Debe ser un número decimal"
    
    @staticmethod
    def validar_booleano(valor: Any) -> Tuple[bool, str]:
        """Valida valor booleano"""
        if isinstance(valor, bool):
            return True, ""
        
        if isinstance(valor, str):
            if valor.lower() in ["true", "false", "1", "0", "yes", "no", "on", "off"]:
                return True, ""
        
        if isinstance(valor, (int, float)):
            if valor in [0, 1]:
                return True, ""
        
        return False, "Debe ser verdadero o falso"
    
    @staticmethod
    def validar_texto(valor: Any, max_length: Optional[int] = None, patron: Optional[str] = None) -> Tuple[bool, str]:
        """Valida texto con longitud y patrón opcionales"""
        try:
            val_str = str(valor)
            
            if max_length is not None and len(val_str) > max_length:
                return False, f"Máximo {max_length} caracteres"
            
            if patron is not None and not re.match(patron, val_str):
                return False, "Formato inválido"
            
            return True, ""
        except:
            return False, "Debe ser texto válido"
    
    @staticmethod
    def validar_seleccion(valor: Any, opciones: List[str]) -> Tuple[bool, str]:
        """Valida que valor esté en lista de opciones"""
        if str(valor) in opciones:
            return True, ""
        
        return False, f"Debe ser uno de: {', '.join(opciones)}"
    
    @staticmethod
    def validar_angulo(valor: Any) -> Tuple[bool, str]:
        """Valida ángulo (0-360 grados)"""
        try:
            val_float = float(valor)
            if 0 <= val_float <= 360:
                return True, ""
            return False, "Debe estar entre 0 y 360 grados"
        except (ValueError, TypeError):
            return False, "Debe ser un ángulo válido"
    
    @staticmethod
    def validar_tension(valor: Any) -> Tuple[bool, str]:
        """Valida tensión eléctrica"""
        try:
            val_int = int(float(valor))
            tensiones_validas = [13, 33, 66, 132, 220, 330, 500, 600, 700, 800, 900, 1000]
            
            if val_int in tensiones_validas:
                return True, ""
            
            return False, f"Tensión debe ser una de: {', '.join(map(str, tensiones_validas))} kV"
        except (ValueError, TypeError):
            return False, "Debe ser una tensión válida en kV"
    
    @staticmethod
    def validar_positivo(valor: Any) -> Tuple[bool, str]:
        """Valida que valor sea positivo"""
        try:
            val_float = float(valor)
            if val_float > 0:
                return True, ""
            return False, "Debe ser mayor que 0"
        except (ValueError, TypeError):
            return False, "Debe ser un número positivo"
    
    @staticmethod
    def validar_no_negativo(valor: Any) -> Tuple[bool, str]:
        """Valida que valor no sea negativo"""
        try:
            val_float = float(valor)
            if val_float >= 0:
                return True, ""
            return False, "No puede ser negativo"
        except (ValueError, TypeError):
            return False, "Debe ser un número no negativo"
    
    @staticmethod
    def validar_porcentaje(valor: Any) -> Tuple[bool, str]:
        """Valida porcentaje (0-100)"""
        try:
            val_float = float(valor)
            if 0 <= val_float <= 100:
                return True, ""
            return False, "Debe estar entre 0 y 100%"
        except (ValueError, TypeError):
            return False, "Debe ser un porcentaje válido"
    
    @staticmethod
    def validar_fecha(valor: Any) -> Tuple[bool, str]:
        """Valida formato de fecha YYYY-MM-DD"""
        try:
            val_str = str(valor)
            patron = r'^\d{4}-\d{2}-\d{2}$'
            
            if re.match(patron, val_str):
                return True, ""
            
            return False, "Formato debe ser YYYY-MM-DD"
        except:
            return False, "Fecha inválida"
    
    @classmethod
    def validar_parametro_especifico(cls, parametro: str, valor: Any) -> Tuple[bool, str]:
        """Aplica validaciones específicas según el parámetro"""
        
        # Validaciones específicas por parámetro
        validaciones_especificas = {
            "TENSION": cls.validar_tension,
            "alpha": cls.validar_angulo,
            "theta": cls.validar_angulo,
            "ANG_APANTALLAMIENTO": lambda v: cls.validar_flotante(v, 0, 45),
            "Altura_MSNM": lambda v: cls.validar_flotante(v, 0, 6000),
            "L_vano": cls.validar_positivo,
            "ALTURA_MINIMA_CABLE": cls.validar_no_negativo,
            "CANT_HG": lambda v: cls.validar_entero(v, 0, 2),
            "FORZAR_N_POSTES": lambda v: cls.validar_entero(v, 0, 3),
            "fecha_creacion": cls.validar_fecha,
            "SALTO_PORCENTUAL": lambda v: cls.validar_flotante(v, 0, 0.1),
            "PASO_AFINADO": lambda v: cls.validar_flotante(v, 0, 0.02),
            "RELFLECHA_MAX_GUARDIA": lambda v: cls.validar_flotante(v, 0.5, 1.1),
            "t_hielo": lambda v: cls.validar_flotante(v, 0, 0.03),
            "ZOOM_CABEZAL": cls.validar_positivo,
        }
        
        if parametro in validaciones_especificas:
            return validaciones_especificas[parametro](valor)
        
        return True, ""