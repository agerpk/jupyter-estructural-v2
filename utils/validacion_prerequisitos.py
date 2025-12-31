"""Utilidades para validación de prerequisitos de cálculos"""

from utils.calculo_cache import CalculoCache


def validar_prerequisitos_fundacion(nombre_estructura):
    """Valida que existan SPH y DME antes de ejecutar fundación"""
    sph_existe = CalculoCache.cargar_calculo_sph(nombre_estructura) is not None
    dme_existe = CalculoCache.cargar_calculo_dme(nombre_estructura) is not None
    return sph_existe and dme_existe, f"SPH: {'✅' if sph_existe else '❌'}, DME: {'✅' if dme_existe else '❌'}"


def validar_prerequisitos_costeo(nombre_estructura):
    """Valida que existan todos los prerequisitos para costeo"""
    sph_existe = CalculoCache.cargar_calculo_sph(nombre_estructura) is not None
    fund_existe = CalculoCache.cargar_calculo_fund(nombre_estructura) is not None
    return sph_existe and fund_existe, f"SPH: {'✅' if sph_existe else '❌'}, Fundación: {'✅' if fund_existe else '❌'}"


def validar_prerequisitos_dme(nombre_estructura):
    """Valida que existan CMC y DGE antes de ejecutar DME"""
    cmc_existe = CalculoCache.cargar_calculo_cmc(nombre_estructura) is not None
    dge_existe = CalculoCache.cargar_calculo_dge(nombre_estructura) is not None
    return cmc_existe and dge_existe, f"CMC: {'✅' if cmc_existe else '❌'}, DGE: {'✅' if dge_existe else '❌'}"


def validar_prerequisitos_arboles(nombre_estructura):
    """Valida que exista DME antes de ejecutar árboles"""
    dme_existe = CalculoCache.cargar_calculo_dme(nombre_estructura) is not None
    return dme_existe, f"DME: {'✅' if dme_existe else '❌'}"


def validar_prerequisitos_sph(nombre_estructura):
    """Valida que exista DME antes de ejecutar SPH"""
    dme_existe = CalculoCache.cargar_calculo_dme(nombre_estructura) is not None
    return dme_existe, f"DME: {'✅' if dme_existe else '❌'}"


def obtener_cadena_dependencias():
    """Retorna la cadena de dependencias de cálculos"""
    return {
        'CMC': [],
        'DGE': ['CMC'],
        'DME': ['CMC', 'DGE'],
        'ARBOLES': ['DME'],
        'SPH': ['DME'],
        'FUNDACION': ['SPH', 'DME'],
        'COSTEO': ['SPH', 'FUNDACION']
    }


def validar_cadena_completa(nombre_estructura, hasta_calculo='COSTEO'):
    """Valida que toda la cadena hasta el cálculo especificado esté completa"""
    dependencias = obtener_cadena_dependencias()
    
    if hasta_calculo not in dependencias:
        return False, f"Cálculo '{hasta_calculo}' no reconocido"
    
    # Obtener todos los prerequisitos recursivamente
    prerequisitos_necesarios = set()
    
    def agregar_prerequisitos(calculo):
        for prereq in dependencias[calculo]:
            prerequisitos_necesarios.add(prereq)
            agregar_prerequisitos(prereq)
    
    agregar_prerequisitos(hasta_calculo)
    
    # Verificar que todos existan
    faltantes = []
    for prereq in prerequisitos_necesarios:
        cache_existe = False
        if prereq == 'CMC':
            cache_existe = CalculoCache.cargar_calculo_cmc(nombre_estructura) is not None
        elif prereq == 'DGE':
            cache_existe = CalculoCache.cargar_calculo_dge(nombre_estructura) is not None
        elif prereq == 'DME':
            cache_existe = CalculoCache.cargar_calculo_dme(nombre_estructura) is not None
        elif prereq == 'ARBOLES':
            cache_existe = CalculoCache.cargar_calculo_arboles(nombre_estructura) is not None
        elif prereq == 'SPH':
            cache_existe = CalculoCache.cargar_calculo_sph(nombre_estructura) is not None
        elif prereq == 'FUNDACION':
            cache_existe = CalculoCache.cargar_calculo_fund(nombre_estructura) is not None
        
        if not cache_existe:
            faltantes.append(prereq)
    
    if faltantes:
        return False, f"Faltan prerequisitos: {', '.join(faltantes)}"
    else:
        return True, f"Cadena completa hasta {hasta_calculo}"