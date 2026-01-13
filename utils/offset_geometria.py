# utils/offset_geometria.py
"""Cálculo de offsets para columnas y ménsulas"""


def calcular_offset_columna(z, z_min, z_max, offset_inicio, offset_fin, tipo_offset):
    """Calcula offset bilateral en X para columna en altura z
    
    Args:
        z: Altura actual
        z_min: Altura mínima (BASE o CROSS_H1)
        z_max: Altura máxima (CROSS_H1 o altura máxima)
        offset_inicio: Offset en z_min
        offset_fin: Offset en z_max
        tipo_offset: "Recto", "Trapezoidal", "Triangular"
    
    Returns:
        float: Offset en X (bilateral, +/-)
    """
    if tipo_offset == "Triangular":
        offset_fin = 0.0
    
    if tipo_offset == "Recto":
        return offset_inicio
    
    if z_max == z_min:
        return offset_inicio
    
    factor = (z - z_min) / (z_max - z_min)
    return offset_inicio + factor * (offset_fin - offset_inicio)


def calcular_offset_mensula(x, x_min, x_max, offset_inicio, offset_fin, tipo_offset):
    """Calcula offset unilateral en Z para ménsula en posición x
    
    Args:
        x: Posición X actual (valor absoluto)
        x_min: Posición X mínima (menor |x|)
        x_max: Posición X máxima (mayor |x|)
        offset_inicio: Offset en menor |x|
        offset_fin: Offset en mayor |x|
        tipo_offset: "Recto", "Trapezoidal", "Triangular"
    
    Returns:
        float: Offset en Z (solo positivo, hacia arriba)
    """
    if tipo_offset == "Triangular":
        offset_fin = 0.0
    
    if tipo_offset == "Recto":
        return offset_inicio
    
    if x_max == x_min:
        return offset_inicio
    
    factor = (abs(x) - x_min) / (x_max - x_min)
    return offset_inicio + factor * (offset_fin - offset_inicio)
