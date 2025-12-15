"""Helpers para formateo consistente de datos"""

import pandas as pd


def formatear_resultados_cmc(resultados_dict):
    """Formatea diccionario de resultados CMC redondeando floats a 2 decimales
    
    Args:
        resultados_dict: Diccionario con resultados CMC
    
    Returns:
        Diccionario con valores redondeados
    """
    if not resultados_dict:
        return resultados_dict
    
    resultado_fmt = {}
    for estado, valores in resultados_dict.items():
        resultado_fmt[estado] = {}
        for key, val in valores.items():
            if isinstance(val, (int, float)):
                resultado_fmt[estado][key] = round(val, 2)
            else:
                resultado_fmt[estado][key] = val
    return resultado_fmt


def formatear_dataframe_cmc(df, estado_determinante=None):
    """Formatea DataFrame CMC con 2 decimales y marca estado determinante
    
    Args:
        df: DataFrame con resultados CMC
        estado_determinante: Nombre del estado determinante (opcional)
    
    Returns:
        DataFrame formateado
    """
    if df is None or df.empty:
        return df
    
    df_fmt = df.copy()
    
    # Agregar columna de estado determinante
    df_fmt['Estado determinante'] = ''
    if estado_determinante and estado_determinante in df_fmt.index:
        df_fmt.loc[estado_determinante, 'Estado determinante'] = '🟡'
    
    return df_fmt
